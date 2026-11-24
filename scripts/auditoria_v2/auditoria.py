"""Auditoría API SQLite. Ejecutar con python auditoria.py --checkout RUTA --salida NUEVA."""
import argparse
import csv
import io
import json
import os
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from time import perf_counter

SEED = 20261124
SCHOOLS = ('A', 'B', 'C')
MODULES = dict.fromkeys(('alumnos', 'planes_estudios', 'horarios', 'reportes', 'asignaciones', 'importaciones'), True)
COMM = '/api/v1/comercial/'
API = '/api/v1/'
IMPORT = API + 'demo/importaciones/'
RUNS = API + 'demo/asignaciones/'


def csv_text(headers, rows):
    buffer = io.StringIO(newline='')
    writer = csv.writer(buffer, lineterminator='\n')
    writer.writerow(headers)
    writer.writerows(rows)
    return buffer.getvalue()


def fixture_password():
    value = os.environ.get('IME_AUDIT_PASSWORD', '')
    if len(value) < 8:
        raise ValueError('Define IME_AUDIT_PASSWORD con una contraseña de prueba de al menos ocho caracteres.')
    return value


def generate(letter, password):
    rng = random.Random(SEED + ord(letter))
    names = ['Ana', 'Luis', 'Elena', 'Rafael', 'Sofía', 'Miguel', 'Lucía', 'Pablo', 'Valeria', 'Diego']
    surnames = ['Ortega', 'Reyes', 'Cruz', 'Medina', 'Vega', 'Ríos', 'López', 'Salas']
    plans, subjects, students, groups, requests = [], [], [], [], []
    offerings = {
        2: ('Datos', 'Lunes', [22, 20]),
        3: ('Álgebra', 'Martes', [18, 24]),
        4: ('Redes', 'Lunes', [76, 68]),
        5: ('Taller', 'Miércoles', [24, 27]),
        6: ('Optativa', '', []),
        7: ('Proyecto', 'Jueves', [40, 38]),
        8: ('Comunicación', 'Viernes', [36, 41]),
    }
    for track, title in [('I', 'Informática'), ('G', 'Gestión')]:
        plan = f'{letter} · {title}'
        plans.append([plan, f'Plan de la escuela ficticia {letter}'])
        prefix = letter + track
        subjects.append([plan, prefix + '1', 'Fundamentos', 6, 1, ''])
        for number, (name, day, capacities) in offerings.items():
            prerequisite = prefix + str({2: 1, 5: 3}.get(number, '')) if number in (2, 5) else ''
            subjects.append([plan, prefix + str(number), name, 4 + number % 3, 2, prerequisite])
            for group, cap in enumerate(capacities, 1):
                block = '08:00-10:00' if number in (2, 4) or group == 1 else '10:00-12:00'
                groups.append([prefix + str(number), f'G{group}', f'{rng.choice(names)} {rng.choice(surnames)} · Docente {letter}', cap, f'{day}:{block}'])
    for number in range(1, 201):
        track, title = ('I', 'Informática') if number % 2 else ('G', 'Gestión')
        prefix = letter + track
        account = f'{letter}{number:03d}'
        approved = [prefix + str(n) for n in (1, 3) if rng.random() < (0.71 if n == 1 else 0.33)]
        students.append([account, rng.choice(names), rng.choice(surnames), rng.choice(surnames),
                         f'{letter} · {title}', ';'.join(approved), password])
        priority = rng.randrange(4)
        ordered = [2, 3, 4, 6]
        if number % 3 >= 1:
            ordered.insert(3, 5)
        if number % 3 == 2:
            ordered.append(rng.choice((7, 8)))
        if number % 4 == 0:
            ordered[0], ordered[2] = ordered[2], ordered[0]
        for rank, subject in enumerate(ordered, 1):
            requests.append([account, prefix + str(subject), rank, priority])
    return {
        'planes': csv_text('nombre descripcion'.split(), plans),
        'materias': csv_text('plan clave nombre creditos semestre prerrequisitos'.split(), subjects),
        'alumnos': csv_text('matricula nombre apellido_paterno apellido_materno plan aprobadas password'.split(), students),
        'grupos': csv_text('materia clave profesor cupo horarios'.split(), groups),
        'solicitudes': csv_text('matricula materia preferencia prioridad_institucional'.split(), requests),
    }


def unpack(data):
    return data['results'] if isinstance(data, dict) else data


def expect(response, status):
    assert response.status_code == status, (response.request.get('PATH_INFO'), response.status_code, status,
                                              str(getattr(response, 'data', None))[:400])
    return getattr(response, 'data', None)


def verify_policy(result, files):
    rows = lambda name: list(csv.DictReader(io.StringIO(files[name])))
    students = {row['matricula']: set(filter(None, row['aprobadas'].split(';'))) for row in rows('alumnos')}
    prerequisites = {row['clave']: set(filter(None, row['prerrequisitos'].split(';'))) for row in rows('materias')}
    groups = defaultdict(list)
    for row in rows('grupos'):
        day, time = row['horarios'].split(':', 1)
        start, end = time.split('-')
        groups[row['materia']].append((row['clave'], int(row['cupo']), day, start, end))
    requests = sorted(rows('solicitudes'), key=lambda s: (int(s['prioridad_institucional']), s['matricula'],
                                                        int(s['preferencia']), s['materia']))
    assert len({r['matricula'] for r in requests}) == 200
    assert set(Counter(r['matricula'] for r in requests).values()) == {4, 5, 6}
    expected, allocation = {}, Counter()
    occupied = defaultdict(list)
    for request in requests:
        student, subject = request['matricula'], request['materia']
        reason, assigned = '', None
        if subject in students[student]:
            reason = 'YA_APROBADA'
        elif not prerequisites[subject] <= students[student]:
            reason = 'PRERREQUISITOS'
        elif not groups[subject]:
            reason = 'SIN_GRUPO'
        else:
            candidates = [g for g in sorted(groups[subject]) if allocation[subject, g[0]] < g[1]]
            for key, cap, day, start, end in candidates:
                if all(day != used_day or end <= used_start or used_end <= start
                       for used_day, used_start, used_end in occupied[student]):
                    assigned = key
                    allocation[subject, key] += 1
                    occupied[student].append((day, start, end))
                    assert allocation[subject, key] <= cap
                    break
            if assigned is None:
                reason = 'CONFLICTO_HORARIO' if candidates else 'SIN_CUPO'
        expected[student, subject] = (assigned, reason, int(request['preferencia']),
                                      int(request['prioridad_institucional']))
    actual = {(r['matricula'], r['clave_materia']): (r['detalle']['grupo'], r['motivo'],
               r['detalle']['preferencia'], r['detalle']['prioridad_institucional']) for r in result['resultados']}
    assert len(actual) == len(result['resultados']) == len(requests)
    assert expected == actual, next(((key, value, actual.get(key)) for key, value in expected.items()
                                     if value != actual.get(key)), None)
    return dict(Counter(r['motivo'] for r in result['resultados'] if r['motivo']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout', type=Path, required=True)
    parser.add_argument('--salida', type=Path, required=True)
    parser.add_argument('--preparar', action='store_true', help='Crea instituciones licenciadas y CSV, sin importarlos.')
    args = parser.parse_args()
    password = fixture_password()
    backend = args.checkout.resolve() / 'backend'
    out = args.salida.resolve()
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    db = backend / f'demo_pagos_auditoria_{out.name}.sqlite3'
    if not out.name.replace('_', '').replace('-', '').isalnum():
        raise ValueError('Identificador de salida inválido')
    with db.open('xb'):
        pass
    db.chmod(0o600)
    os.environ['PAGOS_DEMO_DATABASE'] = str(db)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_pagos_demo'
    sys.path.insert(0, str(backend))
    import django
    django.setup()
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.core.management import call_command
    from rest_framework.test import APIClient
    from apps.core.models import Alumno, Grupo, MembresiaTenant, Nodo, PlanEstudios, SolicitudMateria
    from apps.comercial.models import Orden, Transaccion

    assert settings.COMMERCIAL_PROVIDER == 'DEMO' and not settings.STRIPE_SECRET_KEY
    summary = {'semilla': SEED, 'database': str(db), 'hashers': settings.PASSWORD_HASHERS,
               'escuelas': {}, 'pruebas': [], 'usuarios': {}, 'mediciones': {}, 'fallos': []}
    def save():
        (out / 'resultados.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n')

    def timed(label, func):
        t = perf_counter()
        try:
            return func()
        finally:
            elapsed = round(perf_counter() - t, 4)
            summary['mediciones'][label] = elapsed
            print(f'{label} {elapsed:.4f}s', flush=True)
            save()

    def checked(label, fn):
        try:
            fn()
        except AssertionError as err:
            summary['fallos'].append({'prueba': label, 'error': str(err)})
            print('FALLO', label, str(err), flush=True)
        else:
            summary['pruebas'].append(label)
        save()

    def login(user, tenant=None):
        client = APIClient()
        pair = expect(client.post(API + 'token/', {'matricula': user, 'password': password}, format='json'), 200)
        token = pair['access']
        expect(client.post(API + 'token/refresh/', {'refresh': pair['refresh']}, format='json'), 200)
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        memberships = expect(client.get(API + 'membresias/me/'), 200)
        if tenant:
            assert {str(row['tenant']) for row in memberships} == {tenant}
            client.credentials(HTTP_AUTHORIZATION='Bearer ' + token, HTTP_X_TENANT_ID=tenant)
        return client, token

    def counts(tenant):
        return {name: model.objects.filter(tenant_id=tenant).count() for name, model in
                [('planes', PlanEstudios), ('materias', Nodo), ('alumnos', Alumno),
                 ('grupos', Grupo), ('solicitudes', SolicitudMateria)]}

    def snapshot(tenant):
        return [(model.__name__, list(model.objects.filter(tenant_id=tenant).order_by('pk').values())) for model in
                (PlanEstudios, Nodo, Alumno, Grupo, SolicitudMateria)]

    try:
        timed('migraciones', lambda: call_command('migrate', interactive=False, verbosity=0))
        call_command('check')
        call_command('migrate', check=True, verbosity=0)
        users = get_user_model()
        root = users.objects.create_superuser('auditoria_propietario', password=password)
        owner, _ = login(root.username)
        summary['usuarios']['propietario'] = root.username
        clients, files_by_school = {}, {}

        def generate_all():
            for letter in SCHOOLS:
                folder = out / f'escuela_{letter}'
                folder.mkdir()
                files_by_school[letter] = generate(letter, password)
                assert files_by_school[letter] == generate(letter, password)
                for name, content in files_by_school[letter].items():
                    (folder / f'{name}.csv').write_text(content, encoding='utf-8')

        timed('generar_600_alumnos_y_csv', generate_all)
        plan = expect(owner.post(COMM + 'planes/', {'codigo': 'auditoria-600', 'nombre': 'Plan auditoría DEMO',
                             'funcionalidades': MODULES, 'max_alumnos': 200, 'max_planteles': 1}, format='json'), 201)
        price = expect(owner.post(COMM + 'precios/', {'plan': plan['id'], 'modalidad': 'monthly', 'importe': '100.00',
                              'por_alumno': '2.50', 'moneda': 'MXN', 'dias': 30}, format='json'), 201)

        def anonymous():
            c = APIClient()
            for path in (COMM + 'ordenes/', API + 'alumnos/', RUNS, COMM + 'demo/pendientes/'):
                expect(c.get(path), 401)
            expect(c.post(COMM + 'checkout/', {}, format='json'), 401)
            expect(c.get(COMM + 'ordenes/', HTTP_AUTHORIZATION='Bearer invalid-demo-token'), 401)
            expect(c.post(API + 'token/', {'matricula': root.username, 'password': 'no-valida'}, format='json'), 401)

        checked('anonimo, JWT invalido y credenciales incorrectas', anonymous)
        for letter in SCHOOLS:
            institution = expect(owner.post(COMM + 'instituciones/', {
                'nombre_comercial': f'Escuela {letter} · Auditoría ficticia', 'plan_suscripcion': 'demo',
            }, format='json'), 201)
            tenant = str(institution['id'])
            assert institution['licencia_requerida']
            admin = users.objects.create_user(f'auditoria_admin_{letter.lower()}', password=password)
            MembresiaTenant.objects.create(user=admin, tenant_id=tenant, es_administrador=True)
            if letter == 'A':
                MembresiaTenant.objects.create(user=root, tenant_id=tenant)
            client, token = login(admin.username, tenant)
            clients[letter] = (tenant, client, token)
            summary['usuarios'][letter] = {'admin': admin.username, 'alumno': f'{letter}001'}
            data = summary['escuelas'][letter] = {'tenant': tenant}
            files = files_by_school[letter]

            def commerce():
                assert not expect(client.get(COMM + 'acceso/'), 200)['activo']
                expect(client.get(RUNS), 403)
                expect(client.post(IMPORT + 'confirmar/', {'archivos': files}, format='json'), 403)
                assert any(str(p['id']) == str(plan['id']) for p in unpack(expect(client.get(COMM + 'planes/'), 200)))
                draft = {'precio': str(price['id']), 'alumnos': 200}
                quote = expect(client.post(COMM + 'cotizacion/', draft, format='json'), 200)
                assert quote['total'] == '600.00' and quote['moneda'] == 'MXN'
                wrong = {**draft, 'importe_esperado': '600.01', 'moneda_esperada': 'MXN'}
                expect(client.post(COMM + 'checkout/', wrong, format='json', HTTP_IDEMPOTENCY_KEY=f'aud-{letter}-mismatch'), 409)
                payload = {**draft, 'importe_esperado': quote['total'], 'moneda_esperada': quote['moneda']}
                def checkout():
                    return expect(client.post(COMM + 'checkout/', payload, format='json',
                                              HTTP_IDEMPOTENCY_KEY=f'aud-{letter}-checkout'), 201)
                order = checkout()
                assert order == checkout() and order['estado'] == 'pending' and order['proveedor'] == 'DEMO' and order['url'] is None
                assert not expect(client.get(COMM + 'acceso/'), 200)['activo']
                expect(client.get(RUNS), 403)
                confirm = {'orden': str(order['orden']), 'resultado': 'paid', 'referencia': f'demo_auditoria_{letter}'}
                expect(client.get(COMM + 'demo/pendientes/'), 403)
                expect(client.post(COMM + 'demo/confirmar/', confirm, format='json'), 403)
                assert str(order['orden']) in {str(row['id']) for row in expect(owner.get(COMM + 'demo/pendientes/'), 200)}
                approved = expect(owner.post(COMM + 'demo/confirmar/', confirm, format='json'), 200)
                assert approved == expect(owner.post(COMM + 'demo/confirmar/', confirm, format='json'), 200)
                assert Orden.objects.filter(tenant_id=tenant).count() == 1
                assert Transaccion.objects.filter(orden_id=order['orden']).count() == 1
                access = expect(client.get(COMM + 'acceso/'), 200)
                assert access['activo'] and access['max_alumnos'] == 200 and access['funcionalidades'] == MODULES
                subscriptions = unpack(expect(client.get(COMM + 'suscripciones/'), 200))
                licenses = unpack(expect(client.get(COMM + 'licencias/'), 200))
                docs = unpack(expect(client.get(COMM + 'comprobantes/'), 200))
                assert len(subscriptions) == len(licenses) == len(docs) == 1
                assert subscriptions[0]['estado'] == licenses[0]['estado'] == 'active'
                pdf = client.get(COMM + f"comprobantes/{docs[0]['id']}/pdf/")
                expect(pdf, 200)
                assert pdf.content.startswith(b'%PDF') and b'SIN VALIDEZ FISCAL' in pdf.content
                (out / f'escuela_{letter}' / 'comprobante-interno.pdf').write_bytes(pdf.content)
                data.update(orden=str(order['orden']), cotizacion=quote, suscripcion=str(subscriptions[0]['id']),
                            licencia=str(licenses[0]['id']), comprobante=str(docs[0]['id']))
            timed(f'{letter}_comercial_demostracion', commerce)
            summary['pruebas'].append(f'{letter}_comercial_demostracion')
            assert counts(tenant)['alumnos'] == 0
            if args.preparar:
                save()
                continue

            def negative_imports():
                rows = lambda name: list(csv.reader(io.StringIO(files[name])))
                plan_rows, student_rows, subject_rows, group_rows = map(rows, ('planes', 'alumnos', 'materias', 'grupos'))
                other = 'B' if letter == 'A' else 'A'
                invalid = {
                    'duplicado': {'planes': csv_text(plan_rows[0], [plan_rows[1], plan_rows[1]])},
                    'fila_incompleta': {'planes': csv_text(plan_rows[0], [plan_rows[1], ['Incompleto']])},
                    'prerrequisito_inexistente': {'planes': files['planes'], 'materias': csv_text(subject_rows[0],
                                                     [[*subject_rows[1][:-1], 'NO_EXISTE']])},
                    'referencia_otra_escuela': {'grupos': csv_text(group_rows[0], [[other + 'I2', *group_rows[1][1:]]])},
                    'formato': {'planes': files['planes'], 'alumnos': csv_text(student_rows[0],
                                            [student_rows[1], [*student_rows[2][:-1], 'corto']])},
                    'encabezado': {'planes': 'id,texto\n1,incorrecto\n'},
                }
                for name, broken in invalid.items():
                    before = snapshot(tenant)
                    n_users = users.objects.count()
                    response = expect(client.post(IMPORT + 'confirmar/', {'archivos': broken}, format='json'), 400)
                    assert response['errores'], name
                    assert snapshot(tenant) == before and users.objects.count() == n_users, name
                    summary['pruebas'].append(f'{letter}_CSV_{name}_atomico')

            timed(f'{letter}_importaciones_negativas', negative_imports)
            count_before = counts(tenant)
            users_before = users.objects.count()
            valid = timed(f'{letter}_validar_csv_200', lambda: expect(client.post(IMPORT + 'validar/', {'archivos': files}, format='json'), 200))
            assert valid['valido'] and counts(tenant) == count_before and users.objects.count() == users_before
            applied = timed(f'{letter}_importar_csv_200', lambda: expect(client.post(IMPORT + 'confirmar/', {'archivos': files}, format='json'), 200))
            assert applied['importado'] and applied['valido']
            measured = counts(tenant)
            assert measured == applied['filas'] and measured['alumnos'] == 200
            state_before = snapshot(tenant)
            student_hash = users.objects.get(username=f'{letter}001').password
            again = timed(f'{letter}_reimportar_csv_200', lambda: expect(client.post(IMPORT + 'confirmar/', {'archivos': files}, format='json'), 200))
            assert again['filas'] == measured and counts(tenant) == measured
            assert users.objects.get(username=f'{letter}001').password == student_hash
            new_state = snapshot(tenant)
            for (_, old), (_, new) in zip(state_before, new_state):
                stable = lambda xs: [{k: v for k, v in row.items() if k not in ('updated_at', 'modificado')} for row in xs]
                assert stable(old) == stable(new), (letter, old[0].keys())
            over = next(csv.reader(io.StringIO(files['alumnos'])))
            incoming = [f'{letter}201', 'Nueva', 'Persona', 'Demo', f'{letter} · Informática', '', password]
            cap = expect(client.post(IMPORT + 'confirmar/', {'archivos': {'alumnos': csv_text(over, [incoming])}}, format='json'), 403)
            assert counts(tenant)['alumnos'] == 200 and not users.objects.filter(username=f'{letter}201').exists()
            data['conteos'] = measured
            summary['pruebas'].append(f'{letter}_validar_confirmar_reimportar_y_tope_200')

            student, student_token = login(f'{letter}001', tenant)
            expect(student.get(RUNS), 403)
            expect(student.get(API + 'demo/horario/me/'), 404)
            expect(student.post(IMPORT + 'confirmar/', {'archivos': files}, format='json'), 403)
            run1 = timed(f'{letter}_generar', lambda: expect(client.post(RUNS + 'generar/', {}, format='json'), 201))
            run2 = timed(f'{letter}_repetir_motor', lambda: expect(client.post(RUNS + 'generar/', {}, format='json'), 201))
            results = timed(f'{letter}_detalle_asignacion', lambda: expect(client.get(RUNS + f"{run1['id']}/"), 200))
            second = expect(client.get(RUNS + f"{run2['id']}/"), 200)
            assert results['politica'] == second['politica'] and results['resultados'] == second['resultados']
            assert results['resumen'] == second['resumen']
            reasons = timed(f'{letter}_recalcular_motor_independiente', lambda: verify_policy(results, files))
            assert results['resumen']['asignadas'] + results['resumen']['pendientes'] == measured['solicitudes']
            assert sum(reasons.values()) == results['resumen']['pendientes']
            expect(student.get(API + 'demo/horario/me/'), 404)
            timed(f'{letter}_publicar', lambda: expect(client.post(RUNS + f"{run1['id']}/publicar/", {}, format='json'), 200))
            schedule_path = API + 'demo/horario/me/'
            own = timed(f'{letter}_consultar_horario_alumno', lambda: expect(student.get(schedule_path), 200))
            assert own['ejecucion'] == run1['id'] and own['resultados']
            assert all(r['matricula'] == f'{letter}001' for r in own['resultados'])
            expect(client.get(schedule_path), 403)
            published = client.get(RUNS + f"{run1['id']}/csv/")
            expect(published, 200)
            assert len(list(csv.DictReader(io.StringIO(published.content.decode())))) == measured['solicitudes']
            (out / f'escuela_{letter}' / 'resultado-asignacion.csv').write_bytes(published.content)
            timed(f'{letter}_consultar_estadisticas', lambda: expect(client.get(API + 'demo/estadisticas/'), 200))
            timed(f'{letter}_consultar_alumnos', lambda: expect(client.get(API + 'alumnos/'), 200))
            data.update(ejecucion=run1['id'], resumen=results['resumen'], motivos=reasons, alumno_id=own['resultados'][0]['alumno'])
            summary['pruebas'].append(f'{letter}_motor_determinista_publicado_y_horario_propio')
            save()

        if args.preparar:
            return 0

        def isolation():
            for letter, (tenant, client, token) in clients.items():
                for other, info in summary['escuelas'].items():
                    if letter == other:
                        continue
                    expect(client.get(COMM + f"ordenes/{info['orden']}/"), 404)
                    expect(client.get(COMM + f"suscripciones/{info['suscripcion']}/"), 404)
                    expect(client.get(COMM + f"licencias/{info['licencia']}/"), 404)
                    expect(client.get(COMM + f"comprobantes/{info['comprobante']}/pdf/"), 404)
                    expect(client.get(API + f"alumnos/{info['alumno_id']}/"), 404)
                    expect(client.get(RUNS + f"{info['ejecucion']}/"), 404)
                    expect(client.post(RUNS + f"{info['ejecucion']}/publicar/", {}, format='json'), 404)
                    expect(client.patch(API + f"alumnos/{info['alumno_id']}/", {'nombre': 'Alteración'}, format='json'), 404)
                    expect(client.post(COMM + f"suscripciones/{info['suscripcion']}/cancelar/", {}, format='json'), 404)
                    expect(client.post(COMM + f"licencias/{info['licencia']}/revocar/", {}, format='json'), 403)
                    alternative = APIClient()
                    alternative.credentials(HTTP_AUTHORIZATION='Bearer ' + token, HTTP_X_TENANT_ID=info['tenant'])
                    expect(alternative.get(API + 'alumnos/'), 403)
                    cross = {'solicitudes': csv_text('matricula materia preferencia prioridad_institucional'.split(),
                                                  [[letter + '001', other + 'I2', 1, 0]])}
                    before = counts(tenant)
                    expect(client.post(IMPORT + 'confirmar/', {'archivos': cross}, format='json'), 400)
                    assert counts(tenant) == before
                    _, student_token = login(f'{letter}001', tenant)
                    alternative.credentials(HTTP_AUTHORIZATION='Bearer ' + student_token, HTTP_X_TENANT_ID=info['tenant'])
                    expect(alternative.get(API + 'demo/horario/me/'), 403)
            assert Alumno.objects.count() == 600
            assert Orden.objects.count() == Transaccion.objects.count() == 3
        timed('aislamiento_matriz_6_pares', lambda: checked('aislamiento lectura y escritura de los seis pares dirigidos', isolation))
        income = expect(owner.get(COMM + 'ingresos/'), 200)
        assert len(income) == 1 and income[0]['proveedor'] == 'DEMO' and float(income[0]['total']) == 1800
        summary['ingresos'] = income
        print('COMPLETADA', len(summary['pruebas']), 'pruebas agrupadas', len(summary['fallos']), 'fallos', flush=True)
    except Exception as error:
        summary['fallos'].append({'prueba': 'ejecución principal', 'error': str(error)})
        raise
    finally:
        save()
    return int(bool(summary['fallos']))


if __name__ == '__main__':
    raise SystemExit(main())
