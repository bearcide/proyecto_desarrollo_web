from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase, LiveServerTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from apps.core.models import Tenant, MembresiaTenant, Alumno, PlanEstudios, Nodo, Grupo, SolicitudMateria, EjecucionAsignacion
from . import models as m


@override_settings(COMMERCIAL_PROVIDER='DEMO')
class AcademicLicenseTests(TestCase):
    def setUp(self):
        U = get_user_model()
        self.admin = U.objects.create_user(username='admin', password='Demo-pagos!')
        self.owner = U.objects.create_superuser(username='owner', password='Demo-pagos!')
        self.tenant = Tenant.objects.create(nombre_comercial='A', plan_suscripcion='demo')
        self.other = Tenant.objects.create(nombre_comercial='B', plan_suscripcion='demo')
        MembresiaTenant.objects.create(user=self.admin, tenant=self.tenant, es_administrador=True)
        self.client = self.login('admin')
        self.root = self.login('owner')
        self.plan = m.Plan.objects.create(codigo='basic', nombre='Basic', max_alumnos=1, max_planteles=1,
                                         funcionalidades={'alumnos':True, 'planes_estudios':True, 'horarios':True})
        self.price = m.Precio.objects.create(plan=self.plan, modalidad='process', importe='50', dias=30)
        self.academic = PlanEstudios.objects.create(tenant=self.tenant, nombre='Académico')

    def login(self, name):
        client = APIClient()
        response = client.post('/api/v1/token/', {'matricula':name, 'password':'Demo-pagos!'}, format='json')
        self.assertEqual(response.status_code, 200)
        client.credentials(HTTP_AUTHORIZATION='Bearer '+response.data['access'])
        return client

    def purchase(self, price=None, key='purchase_0001'):
        response = self.client.post('/api/v1/comercial/checkout/', {'precio':str((price or self.price).pk)}, format='json', HTTP_IDEMPOTENCY_KEY=key)
        self.assertEqual(response.status_code, 201, response.data)
        order = m.Orden.objects.get(pk=response.data['orden'])
        confirmation = {'orden':str(order.pk), 'resultado':'paid', 'referencia':'demo_'+key}
        self.assertEqual(self.client.post('/api/v1/comercial/demo/confirmar/', confirmation, format='json').status_code, 403)
        self.assertEqual(self.root.post('/api/v1/comercial/demo/confirmar/', confirmation, format='json').status_code, 200)
        return order

    def denied(self, url, code='license_required', client=None):
        response = (client or self.client).get(url)
        self.assertEqual(response.status_code, 403, response.data)
        self.assertEqual(response.data['code'], code)

    def test_jwt_owner_navigation_claim_and_refresh(self):
        anonymous = APIClient()
        pair = anonymous.post('/api/v1/token/', {'matricula':'owner','password':'Demo-pagos!'}, format='json').data
        self.assertTrue(AccessToken(pair['access'])['is_superuser'])
        refreshed = anonymous.post('/api/v1/token/refresh/', {'refresh':pair['refresh']}, format='json').data
        self.assertTrue(AccessToken(refreshed['access'])['is_superuser'])
        # Claim is a UI hint: a user without membership has no academic bypass.
        self.assertEqual(self.root.get('/api/v1/alumnos/').status_code, 403)

    def test_end_to_end_basic_and_upgrade(self):
        self.denied('/api/v1/demo/grupos/')
        order = self.purchase()
        self.assertEqual(self.client.get('/api/v1/comercial/acceso/').data['activo'], True)
        self.assertEqual(self.client.get('/api/v1/demo/grupos/').status_code, 200)
        self.denied('/api/v1/demo/estadisticas/')
        order.refresh_from_db()
        self.assertEqual(order.estado, 'paid')
        self.assertEqual(order.transaccion_set.count(), 1)
        self.assertEqual(order.licencia.estado, 'active')
        # A second paid plan adds modules through its immutable snapshot.
        advanced = m.Plan.objects.create(codigo='reports', nombre='Reportes', funcionalidades={'reportes':True}, max_alumnos=5)
        advanced_price = m.Precio.objects.create(plan=advanced, modalidad='process', importe='20')
        self.purchase(advanced_price, 'upgrade_0001')
        self.assertEqual(self.client.get('/api/v1/demo/estadisticas/').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/comercial/acceso/').data['max_alumnos'], 5)
        for name in ('Uno', 'Dos'):
            created = self.client.post('/api/v1/alumnos/', {'plan_estudios':self.academic.pk, 'nombre':name, 'apellido_paterno':'Ficticio'}, format='json')
            self.assertEqual(created.status_code, 201, created.data)

    def test_expired_revoked_and_future_license_fail_each_request(self):
        order = self.purchase()
        for changes in ({'fin':timezone.now()-timedelta(seconds=1)}, {'estado':'revoked'}, {'inicio':timezone.now()+timedelta(days=1)}):
            m.Licencia.objects.filter(orden=order).update(estado='active', inicio=timezone.now()-timedelta(days=1), fin=timezone.now()+timedelta(days=30))
            m.Licencia.objects.filter(orden=order).update(**changes)
            self.denied('/api/v1/alumnos/')
            for url in ('/api/v1/comercial/planes/', '/api/v1/comercial/precios/', '/api/v1/comercial/contratos/', '/api/v1/comercial/ordenes/', '/api/v1/comercial/acceso/', '/api/v1/membresias/me/', '/api/v1/tenants/'):
                self.assertEqual(self.client.get(url).status_code, 200, url)
            self.assertIsNotNone(self.login('admin'))
        # Revocation through the owner route is enforced immediately as well.
        m.Licencia.objects.filter(orden=order).update(estado='active', inicio=timezone.now()-timedelta(days=1), fin=timezone.now()+timedelta(days=30))
        self.assertEqual(self.root.post(f'/api/v1/comercial/licencias/{order.licencia.pk}/revocar/', {}, format='json').status_code, 200)
        self.denied('/api/v1/demo/grupos/')
        self.purchase(key='renewal_0001')
        self.assertEqual(self.client.get('/api/v1/demo/grupos/').status_code, 200)

    def test_recurring_expired_period_and_canceled(self):
        price = m.Precio.objects.create(plan=self.plan, modalidad='monthly', importe='50', dias=30)
        order = self.purchase(price)
        self.assertEqual(self.client.get('/api/v1/demo/grupos/').status_code, 200)
        m.Suscripcion.objects.filter(orden=order).update(cancel_at_period_end=True)
        self.assertEqual(self.client.get('/api/v1/demo/grupos/').status_code, 200)
        for attrs in ({'fin_periodo':timezone.now()-timedelta(seconds=1)}, {'estado':'canceled'}, {'estado':'past_due'}):
            m.Suscripcion.objects.filter(orden=order).update(estado='active', fin_periodo=timezone.now()+timedelta(days=20))
            m.Suscripcion.objects.filter(orden=order).update(**attrs)
            self.denied('/api/v1/demo/grupos/')

    def test_student_limit_rest_atomic_and_reducing_usage(self):
        self.purchase()
        data = {'plan_estudios':self.academic.pk, 'nombre':'Ficticio', 'apellido_paterno':'Demo'}
        created = self.client.post('/api/v1/alumnos/', data, format='json')
        self.assertEqual(created.status_code, 201, created.data)
        rejected = self.client.post('/api/v1/alumnos/', data, format='json')
        self.assertEqual(rejected.status_code, 403, rejected.data)
        self.assertEqual(rejected.data['code'], 'license_limit')
        self.assertEqual(Alumno.objects.filter(tenant=self.tenant).count(), 1)
        self.assertEqual(self.client.patch(f"/api/v1/alumnos/{created.data['id']}/", {'nombre':'Cambio'}, format='json').status_code, 200)
        self.assertEqual(self.client.delete(f"/api/v1/alumnos/{created.data['id']}/").status_code, 204)
        self.assertEqual(self.client.post('/api/v1/alumnos/', data, format='json').status_code, 201)

    def test_csv_module_and_capacity_no_partial_writes(self):
        self.plan.funcionalidades.update(importaciones=True)
        self.plan.save()
        self.purchase()
        csv = 'matricula,nombre,apellido_paterno,apellido_materno,plan,aprobadas,password\nCSV1,Ficticio,Uno,,Académico,,Demo-pagos!\nCSV2,Ficticio,Dos,,Académico,,Demo-pagos!\n'
        for action in ('validar', 'confirmar'):
            response = self.client.post(f'/api/v1/demo/importaciones/{action}/', {'archivos':{'alumnos':csv}}, format='json')
            self.assertEqual(response.status_code, 403, response.data)
            self.assertEqual(response.data['code'], 'license_limit')
            self.assertFalse(Alumno.objects.filter(tenant=self.tenant).exists())
            self.assertFalse(get_user_model().objects.filter(username__startswith='CSV').exists())
        # Import feature does not confer modules included in the CSV.
        m.Licencia.objects.update(funcionalidades={'importaciones':True})
        self.assertEqual(self.client.post('/api/v1/demo/importaciones/confirmar/', {'archivos':{'alumnos':csv}}, format='json').status_code, 403)

    def test_import_update_at_limit_is_allowed(self):
        self.plan.funcionalidades['importaciones'] = True
        self.plan.save()
        self.purchase()
        csv = 'matricula,nombre,apellido_paterno,apellido_materno,plan,aprobadas,password\nCSV1,Ficticio,Uno,,Académico,,Demo-pagos!\n'
        for _ in range(2):
            response = self.client.post('/api/v1/demo/importaciones/confirmar/', {'archivos':{'alumnos':csv}}, format='json')
            self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(Alumno.objects.filter(tenant=self.tenant).count(), 1)

    def test_all_academic_entrypoints_require_modules(self):
        self.purchase()
        m.Licencia.objects.update(funcionalidades={})
        for route in ('alumnos/', 'planes-estudios/', 'nodos/', 'prerrequisitos/', 'estadisticas-nodos/', 'demo/grupos/', 'demo/estadisticas/', 'demo/asignaciones/', 'demo/asignaciones/1/', 'demo/asignaciones/1/csv/'):
            self.denied('/api/v1/'+route)
        for route in ('demo/importaciones/validar/', 'demo/importaciones/confirmar/', 'demo/asignaciones/generar/', 'demo/asignaciones/1/publicar/'):
            response = self.client.post('/api/v1/'+route, {}, format='json')
            self.assertEqual(response.status_code, 403, (route, response.data))

    def test_student_profile_and_schedule_are_protected(self):
        student = get_user_model().objects.create_user(username='student', password='Demo-pagos!')
        MembresiaTenant.objects.create(user=student, tenant=self.tenant, es_alumno=True)
        Alumno.objects.create(tenant=self.tenant, plan_estudios=self.academic, user=student, nombre='Ficticio', apellido_paterno='Demo')
        client = self.login('student')
        self.denied('/api/v1/alumnos/me/', client=client)
        self.denied('/api/v1/demo/horario/me/', client=client)
        self.purchase()
        self.assertEqual(client.get('/api/v1/alumnos/me/').status_code, 200)
        self.assertEqual(client.get('/api/v1/demo/horario/me/').status_code, 404)  # sin publicación

    def test_assignment_actual_usage_limit_and_publication(self):
        self.plan.funcionalidades['asignaciones'] = True
        self.plan.save()
        self.purchase()
        node = Nodo.objects.create(tenant=self.tenant, plan_estudios=self.academic, clave='MAT', nombre='Materia', creditos=4, semestre=1)
        Grupo.objects.create(tenant=self.tenant, nodo=node, clave='G', cupo=1, horarios=[])
        student = Alumno.objects.create(tenant=self.tenant, plan_estudios=self.academic, nombre='Uno', apellido_paterno='Demo')
        SolicitudMateria.objects.create(tenant=self.tenant, alumno=student, nodo=node)
        generated = self.client.post('/api/v1/demo/asignaciones/generar/', {}, format='json')
        self.assertEqual(generated.status_code, 201, generated.data)
        Alumno.objects.create(tenant=self.tenant, plan_estudios=self.academic, nombre='Dos', apellido_paterno='Demo')
        for route in ('demo/asignaciones/generar/', f"demo/asignaciones/{generated.data['id']}/publicar/"):
            rejected = self.client.post('/api/v1/'+route, {}, format='json')
            self.assertEqual(rejected.status_code, 403, rejected.data)
            self.assertEqual(rejected.data['code'], 'license_limit')
        self.assertEqual(EjecucionAsignacion.objects.count(), 1)
        self.assertEqual(EjecucionAsignacion.objects.get().estado, 'BORRADOR')

    def test_tenant_identity_precedes_license_and_foreign_keys(self):
        self.purchase()
        self.assertEqual(self.client.get('/api/v1/alumnos/', HTTP_X_TENANT_ID=str(self.other.pk)).status_code, 403)
        MembresiaTenant.objects.create(user=self.admin, tenant=self.other, es_administrador=True)
        self.assertEqual(self.client.get('/api/v1/alumnos/').status_code, 400)
        self.assertEqual(self.client.get('/api/v1/alumnos/', HTTP_X_TENANT_ID=str(self.other.pk)).status_code, 403)
        foreign = PlanEstudios.objects.create(tenant=self.other, nombre='Ajeno')
        response = self.client.post('/api/v1/alumnos/', {'plan_estudios':foreign.pk,'nombre':'No','apellido_paterno':'No'}, format='json', HTTP_X_TENANT_ID=str(self.tenant.pk))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Alumno.objects.exists())

    def test_legacy_transition_is_explicit_and_ends_at_first_order(self):
        self.tenant.licencia_requerida = False
        self.tenant.save(update_fields=['licencia_requerida'])
        self.assertEqual(self.client.get('/api/v1/alumnos/').status_code, 200)
        response = self.client.post('/api/v1/comercial/checkout/', {'precio':str(self.price.pk)}, format='json', HTTP_IDEMPOTENCY_KEY='pending_0001')
        self.assertEqual(response.status_code, 201)
        self.denied('/api/v1/alumnos/')
        # Neither school nor owner can switch policy through public API fields.
        self.assertEqual(self.client.patch(f'/api/v1/tenants/{self.tenant.pk}/', {'licencia_requerida':False}, format='json').status_code, 400)
        self.assertEqual(self.root.patch(f'/api/v1/comercial/instituciones/{self.tenant.pk}/', {'licencia_requerida':False}, format='json').status_code, 400)

    def test_active_contract_expiry_removes_academic_access(self):
        contract = m.Contrato.objects.create(tenant=self.tenant, precio=self.price, inicio=timezone.now()-timedelta(days=1), fin=timezone.now()+timedelta(days=1), estado='active')
        order = self.purchase()
        order.contrato = contract
        order.save(update_fields=['contrato'])
        self.assertEqual(self.client.get('/api/v1/alumnos/').status_code, 200)
        m.Contrato.objects.filter(pk=contract.pk).update(fin=timezone.now()-timedelta(seconds=1))
        self.denied('/api/v1/alumnos/')


class LicenseTransitionMigrationTests(TransactionTestCase):
    def test_existing_rows_keep_transition_new_rows_require_license(self):
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(connection)
        executor.migrate([('core', '0004_demo_academica')])
        try:
            historical = executor.loader.project_state([('core','0004_demo_academica')]).apps.get_model('core', 'Tenant')
            previous = historical.objects.create(nombre_comercial='Anterior', plan_suscripcion='legacy')
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate([('core','0005_licencia_institucional')])
        self.assertFalse(Tenant.objects.get(pk=previous.pk).licencia_requerida)
        self.assertTrue(Tenant.objects.create(nombre_comercial='Nueva', plan_suscripcion='demo').licencia_requerida)


@override_settings(COMMERCIAL_PROVIDER='DEMO', CORS_ALLOWED_ORIGINS=['http://127.0.0.1:5174'])
class BrowserTransportTests(LiveServerTestCase):
    def test_real_http_login_membership_owner_claim_cors_and_license_denial(self):
        import json
        from urllib.request import Request, urlopen
        from urllib.error import HTTPError
        tenant = Tenant.objects.create(nombre_comercial='Visual', plan_suscripcion='demo')
        owner = get_user_model().objects.create_superuser(username='visual', password='Demo-pagos!')
        MembresiaTenant.objects.create(user=owner, tenant=tenant)
        request = Request(self.live_server_url+'/api/v1/token/', data=json.dumps({'matricula':'visual', 'password':'Demo-pagos!'}).encode(),
                          headers={'Content-Type':'application/json', 'Origin':'http://127.0.0.1:5174'})
        with urlopen(request) as response:
            self.assertEqual(response.headers['Access-Control-Allow-Origin'], 'http://127.0.0.1:5174')
            pair = json.load(response)
        self.assertTrue(AccessToken(pair['access'])['is_superuser'])
        headers = {'Authorization':'Bearer '+pair['access'], 'X-Tenant-ID':str(tenant.pk)}
        with urlopen(Request(self.live_server_url+'/api/v1/membresias/me/', headers=headers)) as response:
            memberships = json.load(response)
        self.assertTrue(memberships[0]['activo'])
        self.assertFalse(memberships[0]['es_administrador'])
        with urlopen(Request(self.live_server_url+'/api/v1/comercial/planes/', headers=headers)) as response:
            self.assertEqual(response.status, 200)
        try:
            urlopen(Request(self.live_server_url+'/api/v1/demo/grupos/', headers=headers))
        except HTTPError as response:
            self.assertEqual(response.code, 403)
        else:
            self.fail('Un propietario sin rol académico no debe acceder a grupos')
