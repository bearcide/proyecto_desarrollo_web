from datetime import timedelta
from io import StringIO
import json
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.models import Alumno, MembresiaTenant, Nodo, NodoEstadistico, PlanEstudios, Prerrequisito, Tenant
from apps.core.services.identidad import resolver_identidad


class IdentidadApiTests(TestCase):
    def setUp(self):
        U = get_user_model()
        self.user = U.objects.create_user(username='matricula', password='clave')
        self.admin = U.objects.create_user(username='administrador', password='clave')
        self.otro = U.objects.create_user(username='otro', password='clave')
        self.a = Tenant.objects.create(nombre_comercial='A', plan_suscripcion='prueba')
        self.b = Tenant.objects.create(nombre_comercial='B', plan_suscripcion='prueba')
        self.pa = PlanEstudios.objects.create(tenant=self.a, nombre='Plan A')
        self.pb = PlanEstudios.objects.create(tenant=self.b, nombre='Plan B')
        self.na = Nodo.objects.create(tenant=self.a, plan_estudios=self.pa, clave='A', nombre='Materia A', creditos=5, semestre=1)
        self.na2 = Nodo.objects.create(tenant=self.a, plan_estudios=self.pa, clave='A2', nombre='Materia A2', creditos=5, semestre=1)
        self.nb = Nodo.objects.create(tenant=self.b, plan_estudios=self.pb, clave='B', nombre='Materia B', creditos=5, semestre=1)
        self.sa = NodoEstadistico.objects.create(tenant=self.a, nodo=self.na)
        self.sb = NodoEstadistico.objects.create(tenant=self.b, nodo=self.nb)
        self.ea = Prerrequisito.objects.create(tenant=self.a, nodo=self.na2, prerrequisito=self.na)
        self.eb = Prerrequisito.objects.create(tenant=self.b, nodo=self.nb, prerrequisito=Nodo.objects.create(tenant=self.b, plan_estudios=self.pb, clave='B2', nombre='B2', creditos=5, semestre=1))
        self.alumno = Alumno.objects.create(id=101, user=self.user, tenant=self.a, plan_estudios=self.pa, nombre='Propio', apellido_paterno='A')
        self.ajeno = Alumno.objects.create(user=self.otro, tenant=self.a, plan_estudios=self.pa, nombre='Ajeno', apellido_paterno='A')
        self.externo = Alumno.objects.create(tenant=self.b, plan_estudios=self.pb, nombre='Externo', apellido_paterno='B')
        self.m = MembresiaTenant.objects.create(user=self.user, tenant=self.a, es_alumno=True)
        MembresiaTenant.objects.create(user=self.admin, tenant=self.a, es_administrador=True)
        self.client = APIClient()
        self.login(self.user)

    def login(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(token))
        return token

    def problem(self, response, status, code=None):
        self.assertEqual(response.status_code, status, response.content)
        self.assertEqual(response['Content-Type'].split(';')[0], 'application/problem+json')
        data = response.json()
        self.assertEqual(data['status'], status)
        for key in ('type','title','detail','instance','code'):
            self.assertIn(key, data)
        if code:
            self.assertEqual(data['code'], code)
        return data

    def resources(self, external=False):
        return {'tenants': self.b.pk if external else self.a.pk,
                'planes-estudios': self.pb.pk if external else self.pa.pk,
                'nodos': self.nb.pk if external else self.na.pk,
                'prerrequisitos': self.eb.pk if external else self.ea.pk,
                'estadisticas-nodos': self.sb.pk if external else self.sa.pk,
                'alumnos': self.externo.pk if external else self.alumno.pk}

    def test_me_identidad_y_campos_exactos(self):
        r = self.client.get('/api/v1/alumnos/me/')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data['id'], 101)
        self.assertNotEqual(r.data['id'], self.user.pk)
        self.assertEqual(set(r.data), {'id','tenant','plan_estudios','numero_de_cuenta','nombre','apellido_paterno','apellido_materno','semestre','materias_pasadas','materias_cursadas','creditos','promedio_acumulado','indicador_escolar','materias_aprobadas_ids','numero_inscripcion','ventana_inicio','ventana_texto'})
        from apps.core.api.serializers import AlumnoPerfilSerializer
        self.assertTrue(all(f.read_only for f in AlumnoPerfilSerializer().fields.values()))
        for method in ('post','put','patch','delete'):
            self.problem(getattr(self.client,method)('/api/v1/alumnos/me/', {}, format='json'),405)

    def test_lista_y_detalle_solo_propietario(self):
        r = self.client.get('/api/v1/alumnos/?search=A')
        self.assertEqual([x['id'] for x in r.data['results']], [101])
        self.problem(self.client.get(f'/api/v1/alumnos/{self.ajeno.pk}/'),404)
        self.problem(self.client.get(f'/api/v1/alumnos/{self.externo.pk}/'),404)

    def test_sin_token_invalido_vencido_e_inactivo(self):
        for bearer in ('', 'Bearer invalido'):
            self.client.credentials(HTTP_AUTHORIZATION=bearer)
            r = self.client.get('/api/v1/alumnos/me/')
            self.problem(r,401)
            self.assertIn('WWW-Authenticate',r)
        token=self.login(self.user); token.set_exp(lifetime=timedelta(seconds=-1))
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+str(token))
        self.problem(self.client.get('/api/v1/alumnos/me/'),401)
        self.login(self.user); self.user.is_active=False; self.user.save()
        self.problem(self.client.get('/api/v1/alumnos/me/'),401)

    def test_login_jwt_real_y_credenciales_invalidas(self):
        self.client.credentials()
        r=self.client.post('/api/v1/token/', {'matricula':'matricula','password':'clave'},format='json')
        self.assertEqual(r.status_code,200,r.content)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+r.data['access'])
        self.assertEqual(self.client.get('/api/v1/alumnos/me/').status_code,200)
        self.problem(self.client.post('/api/v1/token/', {'matricula':'matricula','password':'mal'},format='json'),401)
        r=self.client.post('/api/v1/token/refresh/', {'refresh':r.data['refresh']},format='json')
        self.assertEqual(r.status_code,200)

    def test_varias_escuelas_y_header_verificado(self):
        MembresiaTenant.objects.create(user=self.user, tenant=self.b, es_alumno=True)
        self.problem(self.client.get('/api/v1/alumnos/me/'),400,'tenant_required')
        self.assertEqual(self.client.get('/api/v1/alumnos/me/',HTTP_X_TENANT_ID=str(self.a.pk)).status_code,200)
        self.problem(self.client.get('/api/v1/alumnos/me/',HTTP_X_TENANT_ID=str(uuid4())),403,'tenant_access_denied')
        self.problem(self.client.get('/api/v1/alumnos/me/',HTTP_X_TENANT_ID='mal'),400,'invalid_tenant')
        self.problem(self.client.get('/api/v1/alumnos/me/',HTTP_X_TENANT_ID=''),400)

    def test_membresias_descubrimiento_solo_propias(self):
        self.a.estado='SUSPENDIDO'; self.a.save()
        r=self.client.get('/api/v1/membresias/me/')
        self.assertEqual(r.status_code,200)
        self.assertEqual(len(r.data),1)
        self.assertEqual(r.data[0]['estado_escuela'],'SUSPENDIDO')
        self.assertEqual(str(r.data[0]['tenant']),str(self.a.pk))
        self.problem(self.client.post('/api/v1/membresias/me/',{},format='json'),405)

    def test_revocacion_y_estado_se_consultan_cada_peticion(self):
        self.assertEqual(self.client.get('/api/v1/alumnos/me/').status_code,200)
        for estado in ('SUSPENDIDO','CANCELADO'):
            self.a.estado=estado; self.a.save()
            self.problem(self.client.get('/api/v1/alumnos/me/'),403,'tenant_unavailable')
        self.a.estado='ACTIVO'; self.a.save()
        self.m.activo=False; self.m.save()
        self.problem(self.client.get('/api/v1/alumnos/me/'),403,'tenant_access_denied')

    def test_perfil_ausente_duplicado_inactivo_y_sin_rol(self):
        self.alumno.activo=False; self.alumno.save()
        self.problem(self.client.get('/api/v1/alumnos/me/'),403,'alumno_inactive')
        self.alumno.activo=True; self.alumno.save()
        duplicate=Alumno.objects.create(user=self.user,tenant=self.a,plan_estudios=self.pa,nombre='Duplicado',apellido_paterno='A')
        self.problem(self.client.get('/api/v1/alumnos/me/'),409,'ambiguous_alumno_identity')
        duplicate.delete(); self.alumno.user=None; self.alumno.save()
        self.problem(self.client.get('/api/v1/alumnos/me/'),404,'alumno_not_found')
        self.m.es_alumno=False; self.m.save()
        self.problem(self.client.get('/api/v1/nodos/'),403)

    def test_sin_bypass_staff_o_superuser(self):
        self.otro.is_staff=True; self.otro.is_superuser=True; self.otro.save()
        self.login(self.otro)
        self.problem(self.client.get('/api/v1/alumnos/'),403,'tenant_access_denied')

    def test_alumno_no_escribe_ningun_recurso(self):
        before=list(Alumno.objects.values())
        for resource,pk in self.resources().items():
            with self.subTest(resource=resource):
                for method in ('post','put','patch','delete'):
                    path=f'/api/v1/{resource}/' if method=='post' else f'/api/v1/{resource}/{pk}/'
                    expected = 405 if (resource == 'tenants' and method in ('post', 'delete')) or (resource == 'prerrequisitos' and method in ('put', 'patch')) else 403
                    self.problem(getattr(self.client,method)(path,{},format='json'),expected)
        self.assertEqual(before,list(Alumno.objects.values()))

    def test_listas_y_detalles_aislados_todos_recursos(self):
        for user in (self.user,self.admin):
            self.login(user)
            for resource,pk in self.resources(external=True).items():
                with self.subTest(user=user.pk,resource=resource):
                    self.problem(self.client.get(f'/api/v1/{resource}/{pk}/'),404)
                    r=self.client.get(f'/api/v1/{resource}/')
                    self.assertEqual(r.status_code,200,r.content)
                    for row in r.data['results']:
                        self.assertEqual(str(row['id'] if resource=='tenants' else row['tenant']),str(self.a.pk))

    def test_admin_sin_alumno_y_escrituras_locales(self):
        self.login(self.admin)
        self.problem(self.client.get('/api/v1/alumnos/me/'),403)
        r=self.client.post('/api/v1/planes-estudios/',{'nombre':'Nuevo'},format='json')
        self.assertEqual(r.status_code,201,r.content)
        pk=r.data['id']
        self.assertEqual(str(r.data['tenant']),str(self.a.pk))
        self.assertEqual(self.client.patch(f'/api/v1/planes-estudios/{pk}/',{'nombre':'Actualizado'},format='json').status_code,200)
        self.assertEqual(self.client.delete(f'/api/v1/planes-estudios/{pk}/').status_code,204)
        r=self.client.post('/api/v1/alumnos/',{'nombre':'Nuevo','apellido_paterno':'A','plan_estudios':self.pa.pk},format='json')
        self.assertEqual(r.status_code,201,r.content)

    def test_admin_no_actualiza_ni_elimina_escuela_ajena(self):
        self.login(self.admin)
        for resource,pk in self.resources(external=True).items():
            for method in ('put','patch','delete'):
                if resource=='prerrequisitos' and method in ('put','patch'): continue
                if resource=='tenants' and method=='delete': continue
                with self.subTest(resource=resource,method=method):
                    self.problem(getattr(self.client,method)(f'/api/v1/{resource}/{pk}/',{},format='json'),404)
        self.assertTrue(Alumno.objects.filter(pk=self.externo.pk).exists())

    def test_relaciones_externas_y_campos_privilegiados(self):
        self.login(self.admin)
        cases=[('nodos',{'plan_estudios':self.pb.pk,'clave':'X','nombre':'X','creditos':1,'semestre':1}),
               ('alumnos',{'plan_estudios':self.pb.pk,'nombre':'X','apellido_paterno':'X'}),
               ('estadisticas-nodos',{'nodo':self.nb.pk}),
               ('prerrequisitos',{'nodo':self.na.pk,'prerrequisito':self.nb.pk})]
        for resource,payload in cases:
            with self.subTest(resource=resource):
                data=self.problem(self.client.post(f'/api/v1/{resource}/',payload,format='json'),400)
                self.assertIn('invalid_params',data)
        for payload in ({'tenant':str(self.b.pk)}, {'user':self.admin.pk}, {'es_administrador':True}, {'materias_aprobadas_ids':[self.nb.pk]}, {'materias_aprobadas_ids':['1']}):
            self.problem(self.client.patch(f'/api/v1/alumnos/{self.alumno.pk}/',payload,format='json'),400)
        for payload in ({'estado':'CANCELADO'},{'plan_suscripcion':'otro'}):
            self.problem(self.client.patch(f'/api/v1/tenants/{self.a.pk}/',payload,format='json'),400)
        self.problem(self.client.patch(f'/api/v1/alumnos/{self.alumno.pk}/',{'plan_estudios':self.pb.pk},format='json'),400)
        self.problem(self.client.patch(f'/api/v1/estadisticas-nodos/{self.sa.pk}/',{'nodo':self.nb.pk},format='json'),400)

    def test_doble_rol_y_revocacion_administracion(self):
        self.m.es_administrador=True; self.m.save()
        self.assertEqual(self.client.get(f'/api/v1/alumnos/{self.ajeno.pk}/').status_code,200)
        self.assertEqual(self.client.get('/api/v1/alumnos/me/').data['id'],101)
        self.m.es_administrador=False; self.m.save()
        self.problem(self.client.get(f'/api/v1/alumnos/{self.ajeno.pk}/'),404)

    def test_problem_details_json_invalido_ruta_y_metodo(self):
        self.login(self.admin)
        self.problem(self.client.post('/api/v1/planes-estudios/',data='{',content_type='application/json'),400)
        self.problem(self.client.get('/api/v1/no-existe/'),404)
        self.problem(self.client.put('/api/v1/membresias/me/',{},format='json'),405)
        self.problem(self.client.post('/api/v1/token/refresh/',{'refresh':'invalido'},format='json'),401)

    def test_comando_simulacion_auditoria_preserva_usuario_y_alumno(self):
        before=list(get_user_model().objects.values()); academic=list(Alumno.objects.values())
        out=StringIO()
        with self.assertLogs('apps.core.auditoria',level='INFO'), self.captureOnCommitCallbacks(execute=True):
            call_command('aprovisionar_admin_escolar',user_id=self.otro.pk,tenant_id=str(self.a.pk),referencia='solicitud-1',simular=True,stdout=out)
        self.assertFalse(MembresiaTenant.objects.filter(user=self.otro).exists())
        self.assertTrue(json.loads(out.getvalue())['simulacion'])
        call_command('aprovisionar_admin_escolar',user_id=self.user.pk,tenant_id=str(self.a.pk),referencia='solicitud-2',stdout=StringIO())
        self.m.refresh_from_db(); self.assertTrue(self.m.es_alumno); self.assertTrue(self.m.es_administrador)
        self.assertEqual(before,list(get_user_model().objects.values()))
        self.assertEqual(academic,list(Alumno.objects.values()))

    def test_comando_reactivacion_explicita_y_validaciones(self):
        self.m.activo=False; self.m.save()
        args={'user_id':self.user.pk,'tenant_id':str(self.a.pk),'referencia':'solicitud'}
        with self.assertRaises(CommandError): call_command('aprovisionar_admin_escolar',**args,stdout=StringIO())
        call_command('aprovisionar_admin_escolar',**args,reactivar=True,stdout=StringIO())
        self.m.refresh_from_db(); self.assertTrue(self.m.activo)
        for key,value in (('tenant_id','mal'),('user_id',99999),('referencia',' ')):
            bad={**args,key:value}
            with self.assertRaises(CommandError): call_command('aprovisionar_admin_escolar',**bad,stdout=StringIO())
        self.a.estado='SUSPENDIDO';self.a.save()
        with self.assertRaises(CommandError):call_command('aprovisionar_admin_escolar',**args,stdout=StringIO())


    def test_contexto_es_unico_por_peticion(self):
        from types import SimpleNamespace
        request=SimpleNamespace(user=self.admin,headers={})
        with self.assertNumQueries(1):
            first=resolver_identidad(request)
        with self.assertNumQueries(0):
            self.assertIs(resolver_identidad(request),first)

    def test_sin_membresia_y_header_ajeno_no_tienen_fallback(self):
        self.problem(self.client.get('/api/v1/nodos/',HTTP_X_TENANT_ID=str(self.b.pk)),403,'tenant_access_denied')
        self.m.delete()
        self.problem(self.client.get('/api/v1/nodos/'),403,'tenant_access_denied')
        self.assertEqual(self.client.get('/api/v1/membresias/me/').data,[])

    def test_cambio_contexto_multiescuela_no_reutiliza_perfil(self):
        MembresiaTenant.objects.create(user=self.user,tenant=self.b,es_alumno=True)
        self.externo.user=self.user; self.externo.save()
        for tenant,profile in ((self.a,self.alumno),(self.b,self.externo),(self.a,self.alumno)):
            response=self.client.get('/api/v1/alumnos/me/',HTTP_X_TENANT_ID=str(tenant.pk))
            self.assertEqual(response.status_code,200,response.content)
            self.assertEqual(response.data['id'],profile.pk)

    def test_creacion_actualizacion_eliminacion_admin_en_cada_recurso(self):
        self.login(self.admin)
        # Se crea un grafo independiente para no tocar fixtures compartidos.
        r=self.client.post('/api/v1/planes-estudios/',{'nombre':'CRUD'},format='json')
        self.assertEqual(r.status_code,201,r.content); plan=r.data['id']
        nodes=[]
        for key in ('C1','C2'):
            r=self.client.post('/api/v1/nodos/',{'plan_estudios':plan,'clave':key,'nombre':key,'creditos':3,'semestre':1},format='json')
            self.assertEqual(r.status_code,201,r.content); nodes.append(r.data['id'])
        r=self.client.post('/api/v1/prerrequisitos/',{'nodo':nodes[1],'prerrequisito':nodes[0]},format='json')
        self.assertEqual(r.status_code,201,r.content); edge=r.data['id']
        r=self.client.post('/api/v1/estadisticas-nodos/',{'nodo':nodes[0],'alumnos_inscritos':2},format='json')
        self.assertEqual(r.status_code,201,r.content); stats=r.data['id']
        r=self.client.post('/api/v1/alumnos/',{'nombre':'CRUD','apellido_paterno':'A','plan_estudios':plan,'materias_aprobadas_ids':[nodes[0]]},format='json')
        self.assertEqual(r.status_code,201,r.content); alumno=r.data['id']
        for resource,pk,payload in (('tenants',self.a.pk,{'nombre_comercial':'Actualizada'}),('nodos',nodes[0],{'nombre':'Actualizada'}),('estadisticas-nodos',stats,{'alumnos_inscritos':3}),('alumnos',alumno,{'nombre':'Actualizada'})):
            with self.subTest(resource=resource):
                r=self.client.patch(f'/api/v1/{resource}/{pk}/',payload,format='json')
                self.assertEqual(r.status_code,200,r.content)
        for resource,pk in (('alumnos',alumno),('estadisticas-nodos',stats),('prerrequisitos',edge),('nodos',nodes[0]),('nodos',nodes[1]),('planes-estudios',plan)):
            self.assertEqual(self.client.delete(f'/api/v1/{resource}/{pk}/').status_code,204)

    def test_validacion_grafo_y_conflictos_protegidos(self):
        self.login(self.admin)
        r=self.client.post('/api/v1/prerrequisitos/',{'nodo':self.na.pk,'prerrequisito':self.na2.pk},format='json')
        self.problem(r,400)
        new_plan=PlanEstudios.objects.create(tenant=self.a,nombre='Otro plan')
        self.problem(self.client.patch(f'/api/v1/nodos/{self.na.pk}/',{'plan_estudios':new_plan.pk},format='json'),400)
        self.problem(self.client.delete(f'/api/v1/planes-estudios/{self.pa.pk}/'),409)
        r=self.client.post('/api/v1/planes-estudios/',{'nombre':'Plan A'},format='json')
        self.problem(r,400)

    def test_paginacion_y_busqueda_no_amplian_ambito(self):
        self.login(self.admin)
        for index in range(30):
            Alumno.objects.create(tenant=self.a,plan_estudios=self.pa,nombre=f'Local {index}',apellido_paterno='A')
        response=self.client.get('/api/v1/alumnos/?page=2&ordering=nombre')
        self.assertEqual(response.status_code,200)
        for row in response.data['results']:
            self.assertEqual(str(row['tenant']),str(self.a.pk))
        self.assertEqual(self.client.get('/api/v1/alumnos/?search=Externo').data['results'],[])
        self.assertEqual(self.client.get(f'/api/v1/alumnos/?plan_estudios={self.pb.pk}').data['results'],[])

    def test_todos_recursos_bloqueados_por_suspension_y_revocacion(self):
        self.login(self.admin)
        membership=MembresiaTenant.objects.get(user=self.admin,tenant=self.a)
        for suspended in (True,False):
            self.a.estado='SUSPENDIDO' if suspended else 'ACTIVO'; self.a.save()
            membership.activo=suspended; membership.save()
            for resource in self.resources():
                self.problem(self.client.get(f'/api/v1/{resource}/'),403)

    def test_comando_crea_admin_sin_alumno_y_es_idempotente(self):
        args={'user_id':self.otro.pk,'tenant_id':str(self.a.pk),'referencia':'alta-aprobada'}
        for _ in range(2):
            call_command('aprovisionar_admin_escolar',**args,stdout=StringIO())
        membership=MembresiaTenant.objects.get(user=self.otro,tenant=self.a)
        self.assertTrue(membership.es_administrador)
        self.assertFalse(membership.es_alumno)
        self.assertFalse(get_user_model().objects.get(pk=self.otro.pk).is_staff)
        self.assertEqual(MembresiaTenant.objects.filter(user=self.otro).count(),1)
        self.otro.is_active=False; self.otro.save()
        with self.assertRaises(CommandError): call_command('aprovisionar_admin_escolar',**args,stdout=StringIO())


    def test_cors_header_y_problem_details_conservan_cabeceras(self):
        from django.test import override_settings
        with override_settings(CORS_ALLOWED_ORIGINS=['http://localhost:5173']):
            response=self.client.options('/api/v1/alumnos/me/',HTTP_ORIGIN='http://localhost:5173',HTTP_ACCESS_CONTROL_REQUEST_METHOD='GET',HTTP_ACCESS_CONTROL_REQUEST_HEADERS='authorization,x-tenant-id')
            self.assertIn('x-tenant-id',response['Access-Control-Allow-Headers'])
            response=self.client.get('/api/v1/no-existe/',HTTP_ORIGIN='http://localhost:5173')
            self.problem(response,404)
            self.assertEqual(response['Access-Control-Allow-Origin'],'http://localhost:5173')

    def test_schema_documenta_me_y_selector_sin_consultar_identidad(self):
        from drf_spectacular.generators import SchemaGenerator
        schema=SchemaGenerator().get_schema(request=None,public=True)
        operation=schema['paths']['/api/v1/alumnos/me/']['get']
        self.assertIn('X-Tenant-ID',[p['name'] for p in operation['parameters']])
        self.assertIn('application/problem+json',operation['responses']['403']['content'])
        self.assertIn('/api/v1/membresias/me/',schema['paths'])

    def test_todos_viewsets_academicos_usan_contexto_y_permiso(self):
        from apps.core.api.urls import router
        from apps.core.api.mixins import TenantScopedMixin
        from apps.core.api.permissions import TieneTenant
        expected={'tenants','planes-estudios','nodos','prerrequisitos','estadisticas-nodos','alumnos'}
        for prefix,view,_ in router.registry:
            if prefix in expected:
                self.assertTrue(issubclass(view,TenantScopedMixin))
                self.assertIn(TieneTenant,view.permission_classes)
                expected.remove(prefix)
        self.assertFalse(expected)
