import hashlib
import hmac
import json
import time
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch
import stripe
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from apps.core.models import Tenant, MembresiaTenant
from . import models as m, services as s


@override_settings(COMMERCIAL_PROVIDER='DEMO')
class ComercialTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(nombre_comercial='Escuela A',plan_suscripcion='demo')
        self.other = Tenant.objects.create(nombre_comercial='Escuela B',plan_suscripcion='demo')
        U = get_user_model()
        self.user = U.objects.create_user(username='adminA',password='test')
        self.root = U.objects.create_superuser(username='owner',password='test')
        MembresiaTenant.objects.create(user=self.user,tenant=self.tenant,es_administrador=True)
        self.client = APIClient(); self.client.force_authenticate(self.user)
        self.plan = m.Plan.objects.create(codigo='base',nombre='Base',funcionalidades={'horarios':True},max_alumnos=100)
        self.precio = m.Precio.objects.create(plan=self.plan,modalidad='monthly',importe='100.00',por_alumno='2.50',dias=30)

    def compra(self, precio=None, clave='compra_1234', **extra):
        data = {'precio':str((precio or self.precio).id),'alumnos':2,**extra}
        return self.client.post('/api/v1/comercial/checkout/',data,format='json',HTTP_IDEMPOTENCY_KEY=clave)

    def orden(self,precio=None,clave='compra_1234'):
        response = self.compra(precio,clave)
        self.assertEqual(response.status_code,201,response.data)
        return m.Orden.objects.get(pk=response.data['orden'])

    def pago(self,orden,referencia='demo_pago_1234',estado='paid',fin=None):
        return s.confirmar(orden.id,referencia,estado,orden.importe,orden.moneda,'DEMO',
                           fin=fin or timezone.now()+timedelta(days=30),suscripcion='demo_sub_'+str(orden.id))

    def test_suscripcion_y_snapshot(self):
        orden = self.orden(); self.assertEqual(orden.importe,Decimal('105.00'))
        self.assertFalse(s.acceso(self.tenant)['activo'])
        self.pago(orden)
        self.assertTrue(s.acceso(self.tenant)['funcionalidades']['horarios'])
        self.assertEqual(m.Suscripcion.objects.get().estado,'active')
        self.plan.funcionalidades={}; self.plan.save()
        self.assertTrue(s.acceso(self.tenant)['funcionalidades']['horarios'])

    def test_modalidades_unicas_y_perpetua(self):
        for modalidad in ('process','institutional','perpetual'):
            precio = m.Precio.objects.create(plan=self.plan,modalidad=modalidad,importe='120.00',dias=365)
            orden = self.orden(precio,clave='compra_'+modalidad)
            self.pago(orden,referencia='demo_'+modalidad)
            self.assertEqual(orden.licencia.fin is None,modalidad=='perpetual')
        self.assertEqual(m.Suscripcion.objects.count(),0)

    def test_renovacion_cancelacion_expiracion(self):
        orden=self.orden(); self.pago(orden)
        sub=m.Suscripcion.objects.get(); fin=sub.fin_periodo+timedelta(days=30)
        self.pago(orden,'demo_renovacion',fin=fin)
        sub.refresh_from_db(); self.assertEqual(sub.fin_periodo,fin)
        response=self.client.post(f'/api/v1/comercial/suscripciones/{sub.pk}/cancelar/',{},format='json')
        self.assertEqual(response.status_code,200,response.data)
        sub.refresh_from_db(); self.assertTrue(sub.cancel_at_period_end)
        self.assertTrue(s.acceso(self.tenant)['activo'])
        m.Licencia.objects.update(fin=timezone.now()-timedelta(seconds=1))
        self.assertFalse(s.acceso(self.tenant)['activo'])

    def test_fallo_pendiente_y_recuperacion(self):
        orden=self.orden()
        self.pago(orden,'demo_pending',estado='pending'); self.assertFalse(m.Licencia.objects.exists())
        self.pago(orden,'demo_failed',estado='failed'); self.assertFalse(m.Licencia.objects.exists())
        self.pago(orden); self.assertTrue(m.Licencia.objects.exists())
        self.pago(orden,'demo_failed_renew',estado='failed'); self.assertFalse(s.acceso(self.tenant)['activo'])

    def test_idempotencia_y_manipulacion(self):
        orden=self.orden(); self.orden(); self.assertEqual(m.Orden.objects.count(),1)
        response=self.compra(alumnos=3); self.assertEqual(response.status_code,409,response.data)
        self.assertEqual(self.compra(clave='otra_compra',importe='0.01').status_code,400)
        self.assertEqual(self.compra(clave='otra_compra',tenant=str(self.other.id)).status_code,400)
        self.pago(orden); self.pago(orden)
        self.assertEqual(m.Transaccion.objects.count(),1); self.assertEqual(m.Comprobante.objects.count(),1)
        with self.assertRaises(Exception):
            s.confirmar(orden.id,'demo_tamper','paid',Decimal('0.01'),'MXN','DEMO')
        self.assertEqual(m.Transaccion.objects.count(),1)

    def test_aislamiento_roles(self):
        orden=self.orden(); self.pago(orden)
        for ruta in ('ordenes','suscripciones','licencias','transacciones','comprobantes','contratos'):
            response=self.client.get('/api/v1/comercial/'+ruta+'/',HTTP_X_TENANT_ID=str(self.other.id))
            self.assertEqual(response.status_code,403,(ruta,response.data))
        self.assertEqual(self.client.get('/api/v1/comercial/ingresos/').status_code,403)
        self.assertEqual(self.client.post('/api/v1/comercial/planes/',{'codigo':'x','nombre':'x'},format='json').status_code,403)
        self.user.is_staff=True; self.user.save()
        self.assertEqual(self.client.get('/api/v1/comercial/eventos/').status_code,403)
        self.client.force_authenticate(self.root)
        self.assertEqual(self.client.get('/api/v1/comercial/instituciones/').status_code,200)
        self.assertEqual(self.client.post('/api/v1/comercial/planes/',{'codigo':'nuevo','nombre':'Nuevo'},format='json').status_code,201)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/v1/comercial/ordenes/').status_code,401)

    def test_contrato_vencido(self):
        precio=m.Precio.objects.create(plan=self.plan,modalidad='enterprise',importe='200')
        contrato=m.Contrato.objects.create(tenant=self.tenant,precio=precio,inicio=timezone.now()-timedelta(days=2),fin=timezone.now()-timedelta(days=1),estado='active')
        self.assertEqual(self.compra(precio,contrato=str(contrato.id)).status_code,400)
        contrato.fin=timezone.now()+timedelta(days=1); contrato.save()
        response=self.compra(precio,contrato=str(contrato.id)); self.assertEqual(response.status_code,201,response.data)
        orden=m.Orden.objects.get(); self.pago(orden)
        contrato.fin=timezone.now()-timedelta(hours=1); contrato.save()
        self.assertFalse(s.acceso(self.tenant)['activo'])

    def test_transaccion_expone_comprobante_correspondiente_e_institucion(self):
        orden = self.orden()
        pendiente = self.pago(orden, referencia='demo_pendiente_pdf', estado='pending')
        pagada = self.pago(orden)
        for transaccion, comprobante in [(pendiente, None), (pagada, str(m.Comprobante.objects.get(transaccion=pagada).pk))]:
            respuesta = self.client.get(f'/api/v1/comercial/transacciones/{transaccion.pk}/')
            self.assertEqual(respuesta.status_code, 200)
            self.assertEqual(respuesta.data['comprobante_id'], comprobante)
            self.assertEqual(respuesta.data['institucion'], self.tenant.nombre_comercial)

    def test_pdf_factura_y_limites(self):
        orden=self.orden(); self.pago(orden)
        comprobante=m.Comprobante.objects.get()
        response=self.client.get(f'/api/v1/comercial/comprobantes/{comprobante.id}/pdf/')
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.content.startswith(b'%PDF-1.4'))
        self.assertIn(b'SIN VALIDEZ FISCAL',response.content)
        self.assertEqual(self.client.post('/api/v1/comercial/facturas/',{'orden':str(orden.id),'rfc':'XAXX010101000','razon_social':'Escuela','regimen':'601','codigo_postal':'01000','uso_cfdi':'G03'},format='json').status_code,201)
        with self.assertRaises(Exception): s.exigir_capacidad(self.tenant,alumnos=101)
        self.assertEqual(s.exigir_capacidad(self.tenant,alumnos=100)['max_alumnos'],100)

    def test_cotizacion_checkout_y_cambio_de_importe(self):
        url = '/api/v1/comercial/cotizacion/'
        payload = {'precio': str(self.precio.id), 'alumnos': 2}
        cotizacion = self.client.post(url, payload, format='json')
        self.assertEqual(cotizacion.status_code, 200, cotizacion.data)
        self.assertEqual(cotizacion.data, {'base': '100.00', 'cuota_alumnos': '5.00',
                                          'total': '105.00', 'moneda': 'MXN'})
        self.assertFalse(m.Orden.objects.exists())
        self.assertEqual(self.client.post(url, {**payload, 'alumnos': 101}, format='json').status_code, 400)
        self.assertEqual(self.compra(importe_esperado='105.01', moneda_esperada='MXN').status_code, 409)
        self.assertFalse(m.Orden.objects.exists())
        primero = self.compra(importe_esperado='105.00', moneda_esperada='MXN')
        segundo = self.compra(importe_esperado='105.00', moneda_esperada='MXN')
        self.assertEqual(primero.status_code, 201, primero.data)
        self.assertEqual(primero.data, segundo.data)
        self.assertEqual(m.Orden.objects.get().importe, Decimal('105.00'))
        self.assertFalse(m.Licencia.objects.exists())

    def test_demo_solo_propietario(self):
        orden=self.orden(); data={'orden':str(orden.id),'referencia':'demo_prueba_1234','resultado':'paid'}
        self.assertEqual(self.client.post('/api/v1/comercial/demo/confirmar/',data,format='json').status_code,403)
        pendientes = '/api/v1/comercial/demo/pendientes/'
        self.assertEqual(self.client.get(pendientes).status_code, 403)
        self.client.force_authenticate(self.root)
        self.assertEqual([fila['id'] for fila in self.client.get(pendientes).data], [str(orden.id)])
        self.assertEqual(self.client.post('/api/v1/comercial/demo/confirmar/',data,format='json').status_code,200)
        self.assertEqual(self.client.post('/api/v1/comercial/demo/confirmar/', data, format='json').status_code, 200)
        self.assertEqual(self.client.post('/api/v1/comercial/demo/confirmar/',
                                          {**data, 'referencia': 'demo_repetida_0001'}, format='json').status_code, 400)
        self.assertEqual(self.client.get(pendientes).data, [])
        self.assertEqual(m.Transaccion.objects.count(), 1)
        self.assertTrue(s.acceso(self.tenant)['activo'])

    @override_settings(COMMERCIAL_PROVIDER='stripe',STRIPE_SECRET_KEY='sk_test_fake',STRIPE_WEBHOOK_SECRET='whsec_test')
    def test_webhook_firmas_duplicados_y_rollback(self):
        body=json.dumps({'id':'evt_test','object':'event','type':'unknown','livemode':False,'data':{'object':{}}}).encode()
        url='/api/v1/comercial/webhooks/stripe/'
        response=self.client.post(url,body,content_type='application/json',HTTP_STRIPE_SIGNATURE='incorrecta')
        self.assertEqual(response.status_code,400); self.assertFalse(m.Evento.objects.exists())
        stamp=str(int(time.time())); signature=hmac.new(b'whsec_test',stamp.encode()+b'.'+body,hashlib.sha256).hexdigest()
        header=f't={stamp},v1={signature}'
        with patch('apps.comercial.services.procesar_stripe',return_value='processed') as process:
            for _ in range(2): self.assertEqual(self.client.post(url,body,content_type='application/json',HTTP_STRIPE_SIGNATURE=header).status_code,200)
            self.assertEqual(process.call_count,1)
        self.assertEqual(m.Evento.objects.count(),1)

    @override_settings(COMMERCIAL_PROVIDER='stripe',STRIPE_SECRET_KEY='sk_live_prohibida')
    def test_live_rechazado(self):
        self.assertEqual(self.compra().status_code,503)
        self.assertFalse(m.Licencia.objects.exists())

    @override_settings(COMMERCIAL_PROVIDER='stripe',STRIPE_SECRET_KEY='sk_test_fake')
    def test_checkout_stripe_servidor(self):
        with patch('stripe.checkout.Session.create',return_value=stripe.StripeObject.construct_from({'id':'cs_test','url':'https://checkout.stripe.com/test'},None)) as create:
            orden=self.orden(); self.orden()
            self.assertEqual(create.call_count,1)
            self.assertEqual(create.call_args.kwargs['line_items'][0]['price_data']['unit_amount'],10500)
            self.assertEqual(create.call_args.kwargs['mode'],'subscription')
            for clave, retorno in [('success_url', 'exito'), ('cancel_url', 'cancelado')]:
                from urllib.parse import urlsplit, parse_qs
                url = urlsplit(create.call_args.kwargs[clave])
                self.assertEqual(url.path, '/admin/comercial/checkout/resultado')
                self.assertEqual(parse_qs(url.query), {'orden_id': [str(orden.id)], 'retorno': [retorno]})
            self.assertFalse(m.Licencia.objects.exists())
            self.assertEqual(orden.sesion,'cs_test')

    @override_settings(COMMERCIAL_PROVIDER='stripe',STRIPE_SECRET_KEY='sk_test_fake')
    def test_pago_unico_stripe_confirmado(self):
        precio=m.Precio.objects.create(plan=self.plan,modalidad='process',importe='100.00')
        orden=s.preparar_orden(self.tenant,precio.id,1,None,'stripe_one_123')
        orden.sesion='cs_one'; orden.save()
        session=stripe.StripeObject.construct_from({'id':'cs_one','livemode':False,'client_reference_id':str(orden.id),'amount_total':10000,'currency':'mxn','payment_status':'unpaid'},None)
        event={'type':'checkout.session.completed','data':{'object':{'id':'cs_one'}}}
        with patch('stripe.checkout.Session.retrieve',return_value=session):
            s.procesar_stripe(event); self.assertFalse(m.Licencia.objects.exists())
            session.payment_status='paid'
            s.procesar_stripe(event); s.procesar_stripe(event)
        self.assertEqual(m.Licencia.objects.count(),1)
        self.assertEqual(m.Transaccion.objects.count(),1)

    @override_settings(COMMERCIAL_PROVIDER='stripe',STRIPE_SECRET_KEY='sk_test_fake')
    def test_facturas_stripe_inicial_y_renovacion(self):
        orden=s.preparar_orden(self.tenant,self.precio.id,2,None,'stripe_sub_123')
        orden.sesion='cs_sub'; orden.save()
        fin=int((timezone.now()+timedelta(days=30)).timestamp())
        sub=stripe.StripeObject.construct_from({'id':'sub_test','livemode':False,'status':'active','metadata':{'orden':str(orden.id)},'items':{'data':[{'current_period_end':fin}]}},None)
        invoice=stripe.StripeObject.construct_from({'id':'in_first','livemode':False,'parent':{'subscription_details':{'subscription':'sub_test'}},'customer':'cus_test','status':'paid','amount_paid':10500,'currency':'mxn','lines':{'data':[{'period':{'end':fin}}]}},None)
        session=stripe.StripeObject.construct_from({'id':'cs_sub','subscription':'sub_test','customer':'cus_test'},None)
        event={'type':'invoice.paid','data':{'object':{'id':'in_first'}}}
        with patch('stripe.Invoice.retrieve',return_value=invoice),patch('stripe.Subscription.retrieve',return_value=sub),patch('stripe.checkout.Session.retrieve',return_value=session):
            s.procesar_stripe(event); s.procesar_stripe(event)
            self.assertEqual(m.Transaccion.objects.count(),1)
            self.assertTrue(s.acceso(self.tenant)['activo'])
            invoice.id='in_renew'; sub['items']['data'][0]['current_period_end']=fin+30*86400
            invoice['lines']['data'][0]['period']['end']=fin+30*86400
            s.procesar_stripe(event)
            self.assertEqual(m.Transaccion.objects.count(),2)
            self.assertEqual(int(m.Suscripcion.objects.get().fin_periodo.timestamp()),fin+30*86400)
            invoice.id='in_fake'; invoice.amount_paid=1
            with self.assertRaises(Exception): s.procesar_stripe(event)
            self.assertEqual(m.Transaccion.objects.count(),2)
            invoice.amount_paid=10500; invoice.paid_out_of_band=True
            with self.assertRaises(Exception): s.procesar_stripe(event)

    @override_settings(COMMERCIAL_PROVIDER='stripe',STRIPE_SECRET_KEY='sk_test_fake')
    def test_timeout_reutiliza_idempotencia(self):
        with patch('stripe.checkout.Session.create',side_effect=stripe.APIConnectionError('timeout')):
            self.assertEqual(self.compra().status_code,503)
        orden=m.Orden.objects.get()
        with patch('stripe.checkout.Session.create',return_value=stripe.StripeObject.construct_from({'id':'cs_retry','url':'https://checkout.stripe.com/retry'},None)) as create:
            self.assertEqual(self.compra().status_code,201)
            self.assertEqual(create.call_args.kwargs['idempotency_key'],'comercial-'+str(orden.id))
        self.assertEqual(m.Orden.objects.count(),1)

    def test_recurso_ajeno_no_expuesto_y_precios_inmutables(self):
        orden=self.orden(); self.pago(orden)
        user=get_user_model().objects.create_user(username='adminB')
        MembresiaTenant.objects.create(user=user,tenant=self.other,es_administrador=True)
        self.client.force_authenticate(user)
        self.assertEqual(self.client.get(f'/api/v1/comercial/ordenes/{orden.id}/').status_code,404)
        self.assertEqual(self.client.get('/api/v1/comercial/licencias/').data['count'],0)
        self.client.force_authenticate(self.root)
        self.assertEqual(self.client.patch(f'/api/v1/comercial/precios/{self.precio.id}/',{'importe':'1.00'},format='json').status_code,405)

    def test_revocacion_y_validacion_contrato(self):
        orden=self.orden(); self.pago(orden)
        lic=m.Licencia.objects.get()
        url=f'/api/v1/comercial/licencias/{lic.id}/revocar/'
        self.assertEqual(self.client.post(url,{},format='json').status_code,403)
        self.client.force_authenticate(self.root)
        self.assertEqual(self.client.post(url,{},format='json').status_code,200)
        self.assertFalse(s.acceso(self.tenant)['activo'])
        self.assertEqual(m.Evento.objects.get().tipo,'internal.license.revoked')
        self.assertEqual(self.client.post('/api/v1/comercial/contratos/',{'tenant':str(self.tenant.id),'precio':str(self.precio.id),'inicio':timezone.now().isoformat(),'fin':(timezone.now()-timedelta(days=1)).isoformat()},format='json').status_code,400)

    @override_settings(COMMERCIAL_PROVIDER='stripe',STRIPE_SECRET_KEY='sk_test_fake')
    def test_cancelacion_stripe(self):
        orden=s.preparar_orden(self.tenant,self.precio.id,1,None,'stripe_cancel_123')
        sub=m.Suscripcion.objects.create(orden=orden,referencia='sub_cancel',estado='active',fin_periodo=timezone.now()+timedelta(days=20))
        with patch('stripe.Subscription.modify') as modify:
            response=self.client.post(f'/api/v1/comercial/suscripciones/{sub.id}/cancelar/',{},format='json')
            self.assertEqual(response.status_code,200,response.data)
            self.assertTrue(modify.call_args.kwargs['cancel_at_period_end'])
        event={'type':'customer.subscription.deleted','data':{'object':{'id':'sub_cancel'}}}
        with transaction_context():
            with patch('stripe.Subscription.retrieve',return_value=stripe.StripeObject.construct_from({'id':'sub_cancel','status':'canceled'},None)):
                s.procesar_stripe(event)
        sub.refresh_from_db(); self.assertEqual(sub.estado,'canceled')


def transaction_context():
    from django.db import transaction
    return transaction.atomic()
