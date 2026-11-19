"""Operaciones financieras: snapshots, bloqueo de filas y confirmación del proveedor."""
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError
from apps.core.services.identidad import ErrorIdentidad
from .models import (Orden, Precio, Contrato, Suscripcion, Licencia, Transaccion, Comprobante)


class ProveedorNoDisponible(APIException):
    status_code = 503
    default_detail = 'Proveedor sandbox no disponible.'


def stripe_api():
    if settings.COMMERCIAL_PROVIDER != 'stripe' or not settings.STRIPE_SECRET_KEY.startswith('sk_test_'):
        raise ProveedorNoDisponible()
    try:
        import stripe
    except ImportError as exc:
        raise ProveedorNoDisponible() from exc
    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe.max_network_retries = 2
    return stripe


def contrato_valido(contrato):
    now = timezone.now()
    return contrato.estado == 'active' and contrato.inicio <= now and (contrato.fin is None or contrato.fin > now)


@transaction.atomic
def preparar_orden(tenant, precio_id, alumnos, contrato_id, clave):
    # Lock the tenant too: concurrent first requests cannot both create an order.
    type(tenant).objects.select_for_update().get(pk=tenant.pk)
    anterior = Orden.objects.select_for_update().filter(tenant=tenant, clave=clave).first()
    if anterior:
        if str(anterior.precio_id) != str(precio_id) or anterior.alumnos != alumnos or str(anterior.contrato_id or '') != str(contrato_id or ''):
            raise ErrorIdentidad('idempotency_conflict', 'La clave ya pertenece a otra compra.', 409)
        orden = anterior
    else:
        try:
            precio = Precio.objects.select_related('plan').get(pk=precio_id, activo=True, plan__activo=True)
        except Precio.DoesNotExist:
            raise ValidationError('Precio no disponible.')
        contrato = None
        if contrato_id:
            contrato = Contrato.objects.filter(pk=contrato_id, tenant=tenant, precio=precio).first()
            if not contrato or not contrato_valido(contrato):
                raise ValidationError('Contrato no vigente o ajeno a la institución.')
        if precio.modalidad == 'enterprise' and not contrato:
            raise ValidationError('La modalidad empresarial requiere contrato vigente.')
        if alumnos > precio.plan.max_alumnos:
            raise ValidationError('Cantidad superior al límite del plan.')
        importe = (precio.importe + precio.por_alumno * alumnos).quantize(Decimal('0.01'))
        if importe > Decimal('9999999.99'):
            raise ValidationError('Importe fuera de rango.')
        if settings.COMMERCIAL_PROVIDER not in ('DEMO', 'stripe'):
            raise ProveedorNoDisponible()
        orden = Orden.objects.create(tenant=tenant, precio=precio, contrato=contrato,
            alumnos=alumnos, importe=importe, moneda=precio.moneda, clave=clave,
            proveedor=settings.COMMERCIAL_PROVIDER, condiciones={
                'modalidad': precio.modalidad, 'dias': precio.dias, 'recurrente': precio.recurrente,
                'nombre': precio.plan.nombre, 'funcionalidades': precio.plan.funcionalidades,
                'max_alumnos': precio.plan.max_alumnos, 'max_planteles': precio.plan.max_planteles})
    return orden


def checkout(tenant, precio_id, alumnos, contrato_id, clave):
    orden = preparar_orden(tenant, precio_id, alumnos, contrato_id, clave)
    return abrir_checkout(orden.id)


@transaction.atomic
def abrir_checkout(orden_id):
    # Persist order before contacting Stripe: even a timeout reuses its stable ID.
    orden = Orden.objects.select_for_update().get(pk=orden_id)
    if orden.proveedor == 'stripe' and not orden.sesion:
        stripe = stripe_api()
        price_data = {'currency': orden.moneda.lower(), 'unit_amount': int(orden.importe * 100),
                      'product_data': {'name': orden.condiciones['nombre']}}
        recurrente = orden.condiciones['recurrente']
        if recurrente:
            price_data['recurring'] = {'interval': 'month' if orden.condiciones['modalidad'] in ('monthly','hybrid') else 'year'}
        args = dict(mode='subscription' if recurrente else 'payment',
                    line_items=[{'price_data': price_data, 'quantity': 1}],
                    client_reference_id=str(orden.pk), metadata={'orden': str(orden.pk)},
                    success_url=settings.COMMERCIAL_SUCCESS_URL, cancel_url=settings.COMMERCIAL_CANCEL_URL,
                    idempotency_key='comercial-' + str(orden.pk))
        if recurrente:
            args['subscription_data'] = {'metadata': {'orden': str(orden.pk)}}
        try:
            session = stripe.checkout.Session.create(**args)
        except stripe.StripeError as exc:
            raise ProveedorNoDisponible() from exc
        orden.sesion, orden.url = session.id, session.url
        orden.save(update_fields=['sesion','url'])
    return orden


@transaction.atomic
def confirmar(orden_id, referencia, estado, importe, moneda, proveedor, fin=None, suscripcion=None):
    orden = Orden.objects.select_for_update().get(pk=orden_id)
    if orden.proveedor != proveedor or importe != orden.importe or moneda.upper() != orden.moneda:
        raise ValidationError('Confirmación incompatible con la orden.')
    if estado not in ('paid','failed','pending'):
        raise ValidationError('Estado desconocido.')
    existente = Transaccion.objects.filter(proveedor=proveedor, referencia=referencia).first()
    if existente:
        if existente.orden_id != orden.id or existente.estado != estado:
            raise ValidationError('Referencia ya utilizada con otros datos.')
        return existente
    tx = Transaccion.objects.create(orden=orden, referencia=referencia, proveedor=proveedor,
                                   importe=importe, moneda=moneda.upper(), estado=estado)
    if estado != 'paid':
        if orden.estado != 'paid':
            orden.estado = estado
            orden.save(update_fields=['estado'])
        if estado == 'failed':
            Suscripcion.objects.filter(orden=orden).exclude(estado='canceled').update(estado='past_due')
        return tx
    if orden.contrato and not contrato_valido(orden.contrato):
        # Record receipt of money but do not grant an expired contract.
        orden.estado = 'paid'
        orden.save(update_fields=['estado'])
        Comprobante.objects.create(transaccion=tx)
        return tx
    now = timezone.now()
    recurrente = orden.condiciones['recurrente']
    if recurrente:
        if not suscripcion or not fin:
            raise ValidationError('Falta periodo recurrente confirmado.')
        if fin <= now:
            # A delayed valid invoice remains in accounting without renewing access.
            orden.estado = 'paid'
            orden.save(update_fields=['estado'])
            Comprobante.objects.create(transaccion=tx)
            return tx
        sub, _ = Suscripcion.objects.get_or_create(orden=orden, defaults={'referencia': suscripcion})
        if sub.referencia != suscripcion:
            raise ValidationError('Suscripción incompatible.')
        if sub.estado == 'canceled':
            raise ValidationError('Suscripción cancelada.')
        sub.estado = 'active'
        sub.fin_periodo = max(sub.fin_periodo or fin, fin)
        sub.save()
        fin = sub.fin_periodo
    elif orden.condiciones['modalidad'] == 'perpetual':
        fin = None
    else:
        fin = now + timedelta(days=orden.condiciones['dias'])
    licencia, nueva = Licencia.objects.get_or_create(orden=orden, defaults={
        'inicio': now, 'fin': fin, 'funcionalidades': orden.condiciones['funcionalidades'],
        'max_alumnos': orden.condiciones['max_alumnos'], 'max_planteles': orden.condiciones['max_planteles']})
    if not nueva and recurrente and licencia.estado == 'active' and (not licencia.fin or fin > licencia.fin):
        licencia.fin = fin
        licencia.save(update_fields=['fin'])
    orden.estado = 'paid'
    orden.save(update_fields=['estado'])
    Comprobante.objects.create(transaccion=tx)
    return tx


def acceso(tenant):
    now = timezone.now()
    licencias = Licencia.objects.filter(orden__tenant=tenant, estado='active', inicio__lte=now).filter(Q(fin__isnull=True) | Q(fin__gt=now)).select_related('orden__contrato','orden__suscripcion')
    funciones, alumnos, planteles, activo = {}, 0, 0, False
    for lic in licencias:
        if tenant.estado != 'ACTIVO' or (lic.orden.contrato and not contrato_valido(lic.orden.contrato)):
            continue
        if lic.orden.condiciones['recurrente']:
            sub = getattr(lic.orden, 'suscripcion', None)
            if not sub or sub.estado != 'active' or not sub.fin_periodo or sub.fin_periodo <= now:
                continue
        activo = True
        for k,v in lic.funcionalidades.items():
            if v: funciones[k] = v
        alumnos, planteles = max(alumnos,lic.max_alumnos), max(planteles,lic.max_planteles)
    return dict(activo=activo, funcionalidades=funciones, max_alumnos=alumnos, max_planteles=planteles)


def exigir_capacidad(tenant, funcionalidad=None, alumnos=None, planteles=None):
    """Límite central: módulos y capacidad se comprueban también desde la API académica."""
    actual = acceso(tenant)
    if not actual['activo'] or (funcionalidad and not actual['funcionalidades'].get(funcionalidad)):
        raise ErrorIdentidad('license_required', 'Funcionalidad sin licencia vigente.')
    if (alumnos is not None and alumnos > actual['max_alumnos']) or (planteles is not None and planteles > actual['max_planteles']):
        raise ErrorIdentidad('license_limit', 'Límite contratado excedido.')
    return actual


def procesar_stripe(event):
    """Do not trust event amounts: retrieve authoritative session/invoice/subscription."""
    stripe = stripe_api()
    tipo, obj = event['type'], event['data']['object']
    if tipo.startswith('checkout.session.'):
        session = stripe.checkout.Session.retrieve(obj['id'])
        orden = Orden.objects.filter(sesion=session.id, proveedor='stripe').first()
        if not orden or orden.condiciones['recurrente']:
            return 'ignored'
        if session.get('livemode') or session.get('client_reference_id') != str(orden.id):
            raise ValidationError('Sesión incompatible.')
        if tipo in ('checkout.session.completed','checkout.session.async_payment_succeeded') and session.payment_status == 'paid':
            confirmar(orden.id, session.id, 'paid', Decimal(session.amount_total)/100, session.currency, 'stripe')
        elif tipo == 'checkout.session.async_payment_failed':
            confirmar(orden.id, session.id + ':failed', 'failed', Decimal(session.amount_total)/100, session.currency, 'stripe')
        return 'processed'
    if tipo in ('invoice.paid','invoice.payment_failed'):
        invoice = stripe.Invoice.retrieve(obj['id'])
        subscription_id = invoice.get('subscription') or (invoice.get('parent') or {}).get('subscription_details',{}).get('subscription')
        if not subscription_id: return 'ignored'
        sub = stripe.Subscription.retrieve(subscription_id)
        orden_id = sub.get('metadata',{}).get('orden')
        orden = Orden.objects.filter(pk=orden_id, proveedor='stripe').first() if orden_id else None
        if not orden: return 'ignored'
        if invoice.get('livemode') or sub.get('livemode') or not orden.condiciones['recurrente']:
            raise ValidationError('Factura incompatible.')
        # Tie the subscription to the checkout created by our server.
        session = stripe.checkout.Session.retrieve(orden.sesion)
        if session.get('subscription') != sub.id or session.get('customer') != invoice.get('customer'):
            raise ValidationError('Factura ajena a la sesión.')
        if tipo == 'invoice.payment_failed' and (invoice.get('status') == 'paid' or sub.get('status') == 'active'):
            return 'ignored'
        if tipo == 'invoice.paid' and (invoice.get('status') != 'paid' or invoice.get('paid_out_of_band') or sub.get('status') != 'active'):
            raise ValidationError('Factura no confirmada.')
        # Use the paid invoice period, never the period of a newer unpaid invoice.
        ends = [line.get('period',{}).get('end',0) for line in invoice.get('lines',{}).get('data',[])]
        end = min(ends, default=0)
        if not end:
            raise ValidationError('Factura sin periodo de servicio.')
        fin = datetime.fromtimestamp(end, tz=dt_timezone.utc)
        estado = 'paid' if tipo == 'invoice.paid' else 'failed'
        amount = invoice.get('amount_paid') if estado == 'paid' else invoice.get('amount_due')
        confirmar(orden.id, invoice.id + ':' + estado, estado, Decimal(amount)/100,
                  invoice.currency, 'stripe', fin=fin, suscripcion=sub.id)
        return 'processed'
    if tipo in ('customer.subscription.updated','customer.subscription.deleted'):
        sub = stripe.Subscription.retrieve(obj['id'])
        local = Suscripcion.objects.select_for_update().filter(referencia=sub.id, orden__proveedor='stripe').first()
        if local:
            status = sub.get('status')
            if status in ('canceled','unpaid','incomplete_expired'):
                local.estado = 'canceled'
            elif status == 'past_due': local.estado = 'past_due'
            local.cancel_at_period_end = sub.get('cancel_at_period_end',False)
            local.save()
        return 'processed'
    return 'ignored'
