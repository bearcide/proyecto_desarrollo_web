"""Reabre una SQLite de auditoría y verifica la matriz de aislamiento con JWT real."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import sys
from time import perf_counter

from auditoria import API, COMM, IMPORT, RUNS, csv_text, fixture_password, expect, unpack


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout', required=True, type=Path)
    parser.add_argument('--evidencia', required=True, type=Path)
    args = parser.parse_args()
    password = fixture_password()
    backend = args.checkout.resolve() / 'backend'
    evidence = args.evidencia.resolve()
    manifest = json.loads((evidence / 'resultados.json').read_text())
    db = (backend / f'demo_pagos_auditoria_{evidence.name}.sqlite3').resolve()
    assert db == Path(manifest['database']) and db.is_file() and db.name.startswith('demo_pagos_auditoria_')
    assert set(manifest['escuelas']) == {'A', 'B', 'C'}
    os.environ['PAGOS_DEMO_DATABASE'] = str(db)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_pagos_demo'
    sys.path.insert(0, str(backend))
    import django
    django.setup()
    from rest_framework.test import APIClient
    from apps.core.models import Alumno, EjecucionAsignacion, SolicitudMateria, Grupo
    from apps.comercial.models import Orden, Transaccion, Suscripcion, Licencia, Comprobante
    from django.contrib.auth import get_user_model

    output = {'comprobaciones': [], 'estados': {}}
    counts = Counter()
    started = perf_counter()

    def validate(label, response, status):
        data = expect(response, status)
        output['comprobaciones'].append({'prueba': label, 'http': status})
        counts[status] += 1
        return data

    def login(account, target=None):
        client = APIClient()
        token = validate(f'login {account}', client.post(
            API+'token/', {'matricula': account, 'password': password}, format='json'), 200)
        validate(f'refresh {account}', client.post(API+'token/refresh/', {'refresh': token['refresh']}, format='json'), 200)
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + token['access'], **(
            {'HTTP_X_TENANT_ID': target} if target else {}))
        return client, token['access']

    def snapshot():
        entities = (Alumno, EjecucionAsignacion, SolicitudMateria, Grupo, Orden, Transaccion,
                    Suscripcion, Licencia, Comprobante, get_user_model())
        return [list(model.objects.order_by('pk').values()) for model in entities]

    before = snapshot()
    anonymous = APIClient()
    validate('sin sesión', anonymous.get(COMM+'ordenes/'), 401)
    validate('JWT inválido', anonymous.get(COMM+'ordenes/', HTTP_AUTHORIZATION='Bearer invalid-demo-token'), 401)
    owner, _ = login(manifest['usuarios']['propietario'])
    totals = validate('ingresos de propietario', owner.get(COMM+'ingresos/'), 200)
    assert len(totals) == 1 and totals[0]['proveedor'] == 'DEMO' and float(totals[0]['total']) == 1800
    output['ingresos'] = totals
    output['persistencia'] = {}
    for school, info in manifest['escuelas'].items():
        tenant = info['tenant']
        admin, token = login(manifest['usuarios'][school]['admin'], tenant)
        student, student_token = login(manifest['usuarios'][school]['alumno'], tenant)
        assert list(Orden.objects.filter(tenant_id=tenant).values_list('estado', flat=True)) == ['paid']
        actual = validate(f'{school} horario propio reabierto', student.get(API+'demo/horario/me/'), 200)
        assert actual['ejecucion'] == info['ejecucion']
        qty = {
            'alumnos': Alumno.objects.filter(tenant_id=tenant).count(),
            'solicitudes': SolicitudMateria.objects.filter(tenant_id=tenant).count(),
            'publicaciones': EjecucionAsignacion.objects.filter(tenant_id=tenant, estado='PUBLICADO').count(),
        }
        assert qty == {'alumnos': 200, 'solicitudes': info['conteos']['solicitudes'], 'publicaciones': 1}
        assert len(unpack(validate(f'{school} lista órdenes propia', admin.get(COMM+'ordenes/'), 200))) == 1
        output['persistencia'][school] = qty
        validate(f'{school} alumno no modifica perfil', student.patch(API+f"alumnos/{info['alumno_id']}/",
                  {'nombre': 'No se guarda'}, format='json'), 403)
        for other, foreign in manifest['escuelas'].items():
            if school == other:
                continue
            tag = f'{school}→{other}'
            for resource, key in [('ordenes', 'orden'), ('suscripciones', 'suscripcion'), ('licencias', 'licencia')]:
                validate(f'{tag} {resource} ajena', admin.get(COMM + f"{resource}/{foreign[key]}/"), 404)
            validate(f'{tag} PDF ajeno', admin.get(COMM + f"comprobantes/{foreign['comprobante']}/pdf/"), 404)
            validate(f'{tag} alumno ajeno', admin.get(API + f"alumnos/{foreign['alumno_id']}/"), 404)
            validate(f'{tag} ejecución ajena', admin.get(RUNS + f"{foreign['ejecucion']}/"), 404)
            validate(f'{tag} publicación ajena', admin.post(RUNS + f"{foreign['ejecucion']}/publicar/", {}, format='json'), 404)
            validate(f'{tag} editar alumno ajeno', admin.patch(API + f"alumnos/{foreign['alumno_id']}/",
                     {'nombre': 'No se guarda'}, format='json'), 404)
            validate(f'{tag} cancelar suscripción ajena', admin.post(COMM + f"suscripciones/{foreign['suscripcion']}/cancelar/",
                     {}, format='json'), 404)
            validate(f'{tag} revocar licencia sin rol', admin.post(COMM + f"licencias/{foreign['licencia']}/revocar/",
                     {}, format='json'), 403)
            for actor, credential, resource in [('admin', token, 'alumnos/'), ('alumno', student_token, 'demo/horario/me/')]:
                different = APIClient()
                different.credentials(HTTP_AUTHORIZATION='Bearer ' + credential, HTTP_X_TENANT_ID=foreign['tenant'])
                validate(f'{tag} encabezado de institución ajena con {actor}', different.get(API+resource), 403)
            # La clave es real en la otra escuela y no existe en el tenant de esta solicitud.
            csv = csv_text('matricula materia preferencia prioridad_institucional'.split(), [[school+'001', other+'I2', 1, 0]])
            validate(f'{tag} clave foránea en importación', admin.post(IMPORT+'confirmar/',
                     {'archivos': {'solicitudes': csv}}, format='json'), 400)

    assert snapshot() == before
    assert Alumno.objects.count() == 600 and Orden.objects.count() == 3
    output['estados'] = counts
    output['segundos'] = round(perf_counter() - started, 4)
    (evidence / 'aislamiento.json').write_text(json.dumps(output, indent=2, ensure_ascii=False) + '\n')
    print(len(output['comprobaciones']), 'respuestas comprobadas en la matriz y persistencia', output['estados'],
          f"en {output['segundos']} s; ningún registro cambió.")


if __name__ == '__main__':
    main()
