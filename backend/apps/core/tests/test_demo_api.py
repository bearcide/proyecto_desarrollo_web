"""Contrato de demo local: importar, asignar y publicar con JWT reales.

Ejecutar únicamente mediante backend/pruebas_aisladas.py.
"""
import csv
from collections import Counter
from io import StringIO

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.models import (
    Alumno, Grupo, MembresiaTenant, Nodo, PlanEstudios, Prerrequisito,
    SolicitudMateria, EjecucionAsignacion, ResultadoAsignacion, Tenant,
)


def csv_text(headers, rows):
    out = StringIO()
    writer = csv.writer(out)
    writer.writerow(headers)
    writer.writerows(rows)
    return out.getvalue()


class DemoApiBase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(nombre_comercial='Demo ficticia', plan_suscripcion='demo')
        self.other_tenant = Tenant.objects.create(nombre_comercial='Escuela externa ficticia', plan_suscripcion='demo')
        self.admin = get_user_model().objects.create_user(username='admin_demo_test', password='DemoLocal2026!')
        MembresiaTenant.objects.create(user=self.admin, tenant=self.tenant, es_administrador=True)
        self.client = APIClient()
        self.authenticate(self.admin)
        self.plan = PlanEstudios.objects.create(tenant=self.tenant, nombre='Plan local')

    def authenticate(self, user):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(RefreshToken.for_user(user).access_token))

    def response(self, response, status):
        self.assertEqual(response.status_code, status, response.content)
        return response.json() if status != 204 else None

    def material(self, clave, *, plan=None):
        plan = plan or self.plan
        return Nodo.objects.create(tenant=plan.tenant, plan_estudios=plan, clave=clave, nombre=clave, creditos=4, semestre=1)

    def group(self, node, clave='G1', cupo=10, start=480, end=600, day='Lunes'):
        return Grupo.objects.create(tenant=node.tenant, nodo=node, clave=clave, profesor='Docente ficticio', cupo=cupo,
                                    horarios=[{'dia': day, 'inicio': start, 'fin': end}])

    def student(self, code='A001', *, plan=None, user=False):
        plan = plan or self.plan
        actor = get_user_model().objects.create_user(username=code, password='DemoLocal2026!') if user else None
        alumno = Alumno.objects.create(tenant=plan.tenant, plan_estudios=plan, user=actor, numero_de_cuenta=code,
                                      nombre='Alumno ficticio', apellido_paterno=code)
        if actor:
            MembresiaTenant.objects.create(user=actor, tenant=plan.tenant, es_alumno=True)
        return alumno

    def request_subject(self, alumno, node, preference=1, priority=100):
        return SolicitudMateria.objects.create(tenant=alumno.tenant, alumno=alumno, nodo=node,
                                               preferencia=preference, prioridad_institucional=priority)

    def generate(self):
        return self.response(self.client.post('/api/v1/demo/asignaciones/generar/', {}, format='json'), 201)

    def results(self, execution_id):
        return self.response(self.client.get(f'/api/v1/demo/asignaciones/{execution_id}/'), 200)['resultados']


class DemoCsvTests(DemoApiBase):
    def bundle(self):
        return {'archivos': {
            'planes': csv_text(['nombre', 'descripcion'], [['Importado', 'Datos ficticios']]),
            'materias': csv_text(['plan', 'clave', 'nombre', 'creditos', 'semestre', 'prerrequisitos'],
                                 [['Importado', 'IMP1', 'Primera ficticia', 4, 1, ''],
                                  ['Importado', 'IMP2', 'Segunda ficticia', 4, 2, 'IMP1']]),
            'alumnos': csv_text(['matricula', 'nombre', 'apellido_paterno', 'apellido_materno', 'plan', 'aprobadas', 'password'],
                                [['CSV001', 'Persona ficticia', 'CSV', '', 'Importado', 'IMP1', 'DemoLocal2026!']]),
            'grupos': csv_text(['materia', 'clave', 'profesor', 'cupo', 'horarios'],
                               [['IMP2', 'G1', 'Profesor ficticio', 12, 'Lunes:08:00-10:00;Miercoles:10:00-12:00']]),
            'solicitudes': csv_text(['matricula', 'materia', 'preferencia', 'prioridad_institucional'],
                                    [['CSV001', 'IMP2', 1, 100]]),
        }}

    def test_validacion_no_escribe_y_confirmacion_idempotente(self):
        body = self.bundle()
        before = (Alumno.objects.count(), Nodo.objects.count(), Grupo.objects.count(), get_user_model().objects.count())
        data = self.response(self.client.post('/api/v1/demo/importaciones/validar/', body, format='json'), 200)
        self.assertTrue(data['valido'])
        self.assertEqual(data['errores'], [])
        self.assertEqual(data['filas']['materias'], 2)
        self.assertEqual(before, (Alumno.objects.count(), Nodo.objects.count(), Grupo.objects.count(), get_user_model().objects.count()))
        for _ in range(2):
            data = self.response(self.client.post('/api/v1/demo/importaciones/confirmar/', body, format='json'), 200)
            self.assertTrue(data['importado'])
        self.assertEqual(Alumno.objects.filter(numero_de_cuenta='CSV001').count(), 1)
        self.assertEqual(Nodo.objects.filter(tenant=self.tenant, clave__startswith='IMP').count(), 2)
        self.assertEqual(Grupo.objects.count(), 1)
        self.assertEqual(SolicitudMateria.objects.count(), 1)
        self.assertEqual(Prerrequisito.objects.count(), 1)
        actor = get_user_model().objects.get(username='CSV001')
        member = MembresiaTenant.objects.get(user=actor, tenant=self.tenant)
        self.assertTrue(member.es_alumno)
        self.assertFalse(member.es_administrador)
        alumno = Alumno.objects.get(user=actor, tenant=self.tenant)
        self.assertEqual(alumno.materias_aprobadas_ids, [Nodo.objects.get(tenant=self.tenant, clave='IMP1').pk])
        self.client.credentials()
        token = self.response(self.client.post('/api/v1/token/', {'matricula': 'CSV001', 'password': 'DemoLocal2026!'}, format='json'), 200)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token['access'])
        self.assertEqual(self.response(self.client.get('/api/v1/alumnos/me/'), 200)['id'], alumno.pk)

    def test_error_por_fila_y_confirmacion_totalmente_atomica(self):
        body = self.bundle()
        body['archivos']['grupos'] = csv_text(['materia', 'clave', 'profesor', 'cupo', 'horarios'],
                                             [['NO_EXISTE', 'G1', 'Profesor ficticio', 10, 'Lunes:08:00-10:00']])
        before = (PlanEstudios.objects.count(), Alumno.objects.count(), Nodo.objects.count(), get_user_model().objects.count())
        for action in ('validar', 'confirmar'):
            response = self.client.post(f'/api/v1/demo/importaciones/{action}/', body, format='json')
            data = self.response(response, 400)
            self.assertEqual(response['Content-Type'].split(';')[0], 'application/problem+json')
            self.assertTrue(data['errores'])
            error = next(e for e in data['errores'] if e['archivo'] == 'grupos')
            self.assertEqual(error['fila'], 2)
            self.assertIn('campo', error)
            self.assertIn('mensaje', error)
            self.assertEqual(before, (PlanEstudios.objects.count(), Alumno.objects.count(), Nodo.objects.count(), get_user_model().objects.count()))

    def test_csv_ciclico_se_rechaza_sin_datos_parciales(self):
        body = self.bundle()
        body['archivos']['materias'] = csv_text(['plan', 'clave', 'nombre', 'creditos', 'semestre', 'prerrequisitos'],
                                               [['Importado', 'IMP1', 'Primera', 4, 1, 'IMP2'],
                                                ['Importado', 'IMP2', 'Segunda', 4, 2, 'IMP1']])
        self.response(self.client.post('/api/v1/demo/importaciones/confirmar/', body, format='json'), 400)
        self.assertFalse(PlanEstudios.objects.filter(tenant=self.tenant, nombre='Importado').exists())
        self.assertFalse(Prerrequisito.objects.exists())

    def test_password_existente_no_se_resetea(self):
        body = self.bundle()
        self.response(self.client.post('/api/v1/demo/importaciones/confirmar/', body, format='json'), 200)
        actor = get_user_model().objects.get(username='CSV001')
        password_hash = actor.password
        body['archivos']['alumnos'] = body['archivos']['alumnos'].replace('DemoLocal2026!', 'OtraClave2026!')
        self.response(self.client.post('/api/v1/demo/importaciones/confirmar/', body, format='json'), 200)
        actor.refresh_from_db()
        self.assertEqual(actor.password, password_hash)
        self.assertTrue(actor.check_password('DemoLocal2026!'))

    def test_username_ajeno_no_se_vincula_por_importacion(self):
        actor = get_user_model().objects.create_user(username='CSV001', password='Ajena2026!')
        member = MembresiaTenant.objects.create(user=actor, tenant=self.other_tenant, es_administrador=True)
        self.response(self.client.post('/api/v1/demo/importaciones/confirmar/', self.bundle(), format='json'), 400)
        self.assertFalse(Alumno.objects.filter(user=actor, tenant=self.tenant).exists())
        self.assertFalse(MembresiaTenant.objects.filter(user=actor, tenant=self.tenant).exists())
        member.refresh_from_db()
        self.assertTrue(member.es_administrador)

    def test_grupos_con_cupo_negativo_o_bloques_invalidos_se_rechazan(self):
        for cupo, horario in ((-1, 'Lunes:08:00-10:00'), (10, 'Lunes:10:00-08:00'),
                              (10, 'Lunes:08:00-10:00;Lunes:09:00-11:00')):
            with self.subTest(cupo=cupo, horario=horario):
                body = self.bundle()
                body['archivos']['grupos'] = csv_text(['materia', 'clave', 'profesor', 'cupo', 'horarios'],
                                                     [['IMP2', 'G1', 'Profesor ficticio', cupo, horario]])
                self.response(self.client.post('/api/v1/demo/importaciones/validar/', body, format='json'), 400)

    def test_prioridad_institucional_inconsistente_se_rechaza(self):
        body = self.bundle()
        body['archivos']['solicitudes'] = csv_text(['matricula', 'materia', 'preferencia', 'prioridad_institucional'],
                                                   [['CSV001', 'IMP1', 1, 1], ['CSV001', 'IMP2', 2, 9]])
        self.response(self.client.post('/api/v1/demo/importaciones/validar/', body, format='json'), 400)


class DemoAssignmentTests(DemoApiBase):
    def test_100_alumnos_capacidad_persistencia_y_determinismo(self):
        node = self.material('MASIVA')
        groups = [self.group(node, 'G1', 30), self.group(node, 'G2', 30)]
        for index in range(100):
            self.request_subject(self.student(f'A{index:03d}'), node)
        first = self.generate()
        self.assertEqual(first['estado'], 'BORRADOR')
        rows = self.results(first['id'])
        self.assertEqual(len(rows), 100)
        self.assertEqual(first['resumen']['alumnos'], 100)
        assigned = [r for r in rows if r['estado'] == 'ASIGNADA']
        self.assertEqual(len(assigned), 60)
        self.assertEqual(first['resumen']['pendientes'], 40)
        counts = Counter(r['grupo'] for r in assigned)
        self.assertEqual(set(counts), {g.pk for g in groups})
        self.assertTrue(all(counts[g.pk] <= g.cupo for g in groups))
        self.assertEqual(ResultadoAsignacion.objects.filter(ejecucion_id=first['id']).count(), 100)
        self.assertEqual(len({(r['alumno'], r['materia']) for r in rows}), 100)
        second = self.generate()
        other = self.results(second['id'])
        projection = lambda data: sorted((r['alumno'], r['materia'], r['grupo'], r['estado'], r['motivo']) for r in data)
        self.assertEqual(projection(rows), projection(other))
        self.assertEqual(second['resumen'], first['resumen'])

    def test_prerrequisitos_aprobadas_plan_y_cruces(self):
        a, b, c, d, e = [self.material(code) for code in ('A', 'B', 'C', 'D', 'E')]
        self.group(a, start=480, end=600)
        self.group(b, start=540, end=660)
        self.group(c, start=600, end=720)
        self.group(d, start=720, end=780)
        self.group(e, start=780, end=840)
        Prerrequisito.objects.create(tenant=self.tenant, nodo=d, prerrequisito=a)
        alumno = self.student()
        alumno.materias_aprobadas_ids = [e.pk]
        alumno.save(update_fields=['materias_aprobadas_ids'])
        foreign_plan = PlanEstudios.objects.create(tenant=self.tenant, nombre='Otro plan')
        outside_plan = self.material('FUERA_PLAN', plan=foreign_plan)
        self.group(outside_plan)
        for preference, node in enumerate((a, b, c, d, e, outside_plan), 1):
            self.request_subject(alumno, node, preference)
        execution = self.generate()
        rows = {r['materia']: r for r in self.results(execution['id'])}
        self.assertEqual(rows[a.pk]['estado'], 'ASIGNADA')
        self.assertEqual(rows[c.pk]['estado'], 'ASIGNADA')
        self.assertEqual(rows[b.pk]['motivo'], 'CONFLICTO_HORARIO')
        self.assertEqual(rows[d.pk]['motivo'], 'PRERREQUISITOS')
        self.assertEqual(rows[e.pk]['motivo'], 'YA_APROBADA')
        self.assertEqual(rows[outside_plan.pk]['motivo'], 'PLAN_INCORRECTO')

    def test_prioridad_explicita_controla_cupo_y_politica_auditable(self):
        node = self.material('PRIORIDAD')
        self.group(node, cupo=1)
        first = self.student('A001')
        prioritized = self.student('Z999')
        self.request_subject(first, node, priority=100)
        self.request_subject(prioritized, node, priority=1)
        execution = self.generate()
        self.assertTrue(execution['politica'])
        rows = {r['alumno']: r for r in self.results(execution['id'])}
        self.assertEqual(rows[prioritized.pk]['estado'], 'ASIGNADA')
        self.assertEqual(rows[first.pk]['motivo'], 'SIN_CUPO')

    def test_sin_grupo_registra_pendiente(self):
        alumno = self.student()
        node = self.material('SIN_GRUPO')
        self.request_subject(alumno, node)
        execution = self.generate()
        row, = self.results(execution['id'])
        self.assertEqual(row['estado'], 'PENDIENTE')
        self.assertEqual(row['motivo'], 'SIN_GRUPO')
        self.assertIsNone(row['grupo'])

    def test_publicacion_horario_propio_y_sin_borradores_para_alumno(self):
        node = self.material('PUBLICAR')
        self.group(node)
        alumno = self.student('PUBLIC001', user=True)
        other = self.student('PUBLIC002', user=True)
        self.request_subject(alumno, node)
        self.request_subject(other, node)
        execution = self.generate()
        self.authenticate(alumno.user)
        self.response(self.client.get('/api/v1/demo/horario/me/'), 404)
        for path in ('/api/v1/demo/asignaciones/', f"/api/v1/demo/asignaciones/{execution['id']}/", f"/api/v1/demo/asignaciones/{execution['id']}/csv/"):
            self.response(self.client.get(path), 403)
        self.authenticate(self.admin)
        self.response(self.client.post(f"/api/v1/demo/asignaciones/{execution['id']}/publicar/", {}, format='json'), 200)
        self.authenticate(alumno.user)
        horario = self.response(self.client.get('/api/v1/demo/horario/me/'), 200)
        self.assertEqual(horario['ejecucion'], execution['id'])
        self.assertTrue(horario['resultados'])
        self.assertEqual({row['alumno'] for row in horario['resultados']}, {alumno.pk})
        self.response(self.client.get(f"/api/v1/demo/asignaciones/{execution['id']}/"), 403)
        self.authenticate(self.admin)
        second = self.generate()
        self.response(self.client.post(f"/api/v1/demo/asignaciones/{second['id']}/publicar/", {}, format='json'), 200)
        self.assertEqual(EjecucionAsignacion.objects.filter(tenant=self.tenant, estado='PUBLICADO').count(), 1)
        self.assertEqual(EjecucionAsignacion.objects.get(pk=execution['id']).estado, 'ARCHIVADO')

    def test_snapshot_persistente_y_descarga_csv(self):
        node = self.material('SNAPSHOT')
        group = self.group(node)
        self.request_subject(self.student(), node)
        execution = self.generate()
        before = self.results(execution['id'])
        group.profesor = 'Nuevo profesor ficticio'
        group.horarios = [{'dia': 'Martes', 'inicio': 900, 'fin': 960}]
        group.save()
        after = self.results(execution['id'])
        self.assertEqual(before, after)
        response = self.client.get(f"/api/v1/demo/asignaciones/{execution['id']}/csv/")
        self.response_csv(response)
        data = list(csv.DictReader(StringIO(response.content.decode('utf-8-sig'))))
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['matricula'], 'A001')
        self.assertEqual(set(data[0]), {'matricula', 'materia', 'grupo', 'estado', 'motivo', 'profesor', 'horarios'})

    def response_csv(self, response):
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response['Content-Type'].split(';')[0], 'text/csv')

    def test_aislamiento_estadisticas_grupos_ejecuciones_y_publicacion(self):
        other_admin = get_user_model().objects.create_user(username='otro_admin', password='DemoLocal2026!')
        MembresiaTenant.objects.create(user=other_admin, tenant=self.other_tenant, es_administrador=True)
        other_plan = PlanEstudios.objects.create(tenant=self.other_tenant, nombre='Externo')
        node = self.material('EXTERNA', plan=other_plan)
        group = self.group(node)
        alumno = self.student('EXTERNO001', plan=other_plan)
        self.request_subject(alumno, node)
        self.authenticate(other_admin)
        external_execution = self.generate()
        self.authenticate(self.admin)
        local_node = self.material('LOCAL')
        self.group(local_node)
        local_alumno = self.student('LOCAL001')
        self.request_subject(local_alumno, local_node)
        execution = self.generate()
        self.assertEqual({row['alumno'] for row in self.results(execution['id'])}, {local_alumno.pk})
        stats = self.response(self.client.get('/api/v1/demo/estadisticas/'), 200)
        self.assertEqual(stats['alumnos'], 1)
        self.assertEqual(stats['grupos'], 1)
        groups = self.response(self.client.get('/api/v1/demo/grupos/'), 200)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]['materia'], local_node.pk)
        for suffix in ('', 'csv/'):
            self.response(self.client.get(f"/api/v1/demo/asignaciones/{external_execution['id']}/{suffix}"), 404)
        self.response(self.client.post(f"/api/v1/demo/asignaciones/{external_execution['id']}/publicar/", {}, format='json'), 404)
        self.assertEqual(EjecucionAsignacion.objects.get(pk=external_execution['id']).estado, 'BORRADOR')

    def test_alumno_no_importa_genera_publica_ni_consulta_estadisticas(self):
        alumno = self.student('SOLO_PROPIO', user=True)
        node = self.material('ROL')
        self.group(node)
        self.request_subject(alumno, node)
        execution = self.generate()
        self.authenticate(alumno.user)
        for path in ('/api/v1/demo/importaciones/validar/', '/api/v1/demo/importaciones/confirmar/',
                     '/api/v1/demo/asignaciones/generar/', f"/api/v1/demo/asignaciones/{execution['id']}/publicar/"):
            self.response(self.client.post(path, {}, format='json'), 403)
        for path in ('/api/v1/demo/estadisticas/', '/api/v1/demo/grupos/'):
            self.response(self.client.get(path), 403)


class DemoGeneratedFixtureTests(DemoApiBase):
    def test_archivos_demo_flujo_real_100_alumnos_y_restricciones(self):
        from apps.core.services.datos_demo import archivos_demo
        body = {'archivos': archivos_demo(100)}
        report = self.response(self.client.post('/api/v1/demo/importaciones/validar/', body, format='json'), 200)
        self.assertTrue(report['valido'])
        self.assertFalse(Alumno.objects.filter(tenant=self.tenant).exists())
        report = self.response(self.client.post('/api/v1/demo/importaciones/confirmar/', body, format='json'), 200)
        self.assertTrue(report['importado'])
        self.assertEqual(Alumno.objects.filter(tenant=self.tenant).count(), 100)
        self.assertEqual(Grupo.objects.filter(tenant=self.tenant).count(), 24)
        self.assertEqual(Nodo.objects.filter(tenant=self.tenant).count(), 12)
        self.assertEqual(SolicitudMateria.objects.filter(tenant=self.tenant).count(), 400)
        self.assertFalse(MembresiaTenant.objects.filter(tenant=self.tenant, es_alumno=True, es_administrador=True).exists())
        execution = self.generate()
        rows = self.results(execution['id'])
        self.assertEqual(len(rows), 400)
        self.assertEqual(execution['resumen']['alumnos'], 100)
        self.assertEqual(execution['resumen']['asignadas'] + execution['resumen']['pendientes'], 400)
        students = {a.pk: a for a in Alumno.objects.filter(tenant=self.tenant)}
        nodes = {n.pk: n for n in Nodo.objects.filter(tenant=self.tenant).prefetch_related('prerrequisitos')}
        groups = {g.pk: g for g in Grupo.objects.filter(tenant=self.tenant)}
        capacity, schedules = Counter(), {}
        for row in rows:
            alumno, node = students[row['alumno']], nodes[row['materia']]
            self.assertEqual(alumno.plan_estudios_id, node.plan_estudios_id)
            if row['estado'] != 'ASIGNADA':
                self.assertTrue(row['motivo'])
                continue
            group = groups[row['grupo']]
            self.assertEqual(group.nodo_id, node.pk)
            self.assertNotIn(node.pk, alumno.materias_aprobadas_ids)
            self.assertTrue({n.pk for n in node.prerrequisitos.all()}.issubset(alumno.materias_aprobadas_ids))
            capacity[group.pk] += 1
            previous = schedules.setdefault(alumno.pk, [])
            for block in group.horarios:
                self.assertFalse(any(old['dia'] == block['dia'] and old['inicio'] < block['fin'] and block['inicio'] < old['fin'] for old in previous))
            previous.extend(group.horarios)
        self.assertGreater(sum(capacity.values()), 0)
        for group_id, count in capacity.items():
            self.assertLessEqual(count, groups[group_id].cupo)
        first_signature = [(r['alumno'], r['materia'], r['grupo'], r['estado'], r['motivo']) for r in rows]
        second = self.generate()
        self.assertEqual(first_signature, [(r['alumno'], r['materia'], r['grupo'], r['estado'], r['motivo']) for r in self.results(second['id'])])
        self.response(self.client.post(f"/api/v1/demo/asignaciones/{execution['id']}/publicar/", {}, format='json'), 200)
        self.client.credentials()
        token = self.response(self.client.post('/api/v1/token/', {'matricula': 'D001', 'password': 'DemoLocal2026!'}, format='json'), 200)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token['access'])
        profile = self.response(self.client.get('/api/v1/alumnos/me/'), 200)
        horario = self.response(self.client.get('/api/v1/demo/horario/me/'), 200)
        self.assertEqual({r['alumno'] for r in horario['resultados']}, {profile['id']})
        self.assertEqual(len(horario['resultados']), 4)
