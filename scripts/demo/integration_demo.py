#!/usr/bin/env python3
"""Suite de pruebas de integracion HTTP contra el entorno local de demo.

Contrato: docs/DEMO_API_CONTRACT.md. Base URL: http://127.0.0.1:8000/api/v1/
(no hay servicios externos; JSON UTF-8).

Uso:
    python scripts/demo/integration_demo.py [--base-url http://127.0.0.1:8000/api/v1]

Requisitos previos (gestionados por Codex):
    - backend con settings_demo (backend/demo_local_20261105.sqlite3)
    - servidor Django activo en 127.0.0.1:8000
    - inicializacion demo completada (admin demo_admin / DemoLocal2026!)
"""
import argparse
import csv
import io
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = 'http://127.0.0.1:8000/api/v1'
DATA_DIR = Path(__file__).resolve().parents[1] / 'demo_data'
ADMIN_MATRICULA = 'demo_admin'
ADMIN_PASSWORD = 'DemoLocal2026!'
ALUNO_MATRICULA = 'D001'
ALUNO_PASSWORD = 'DemoLocal2026!'
RESULTADOS = []


def registrar(nombre, ok, detalle=''):
    RESULTADOS.append((nombre, ok, detalle))
    print(f"[{'APROVADA' if ok else 'FALLIDA'}] {nombre}" + (f" | {detalle}" if detalle else ''))


def http(method, url, body=None, token=None, tenant=None, raw=False):
    data = None
    headers = {'Accept': 'application/json'}
    if body is not None:
        data = json.dumps(body).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if tenant:
        headers['X-Tenant-ID'] = tenant
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode('utf-8')
            payload = text if raw else (json.loads(text) if text.strip() else None)
            return resp.status, payload, text
    except urllib.error.HTTPError as exc:
        text = exc.read().decode('utf-8')
        try:
            payload = json.loads(text) if text.strip() else None
        except ValueError:
            payload = text
        return exc.code, payload, text


def post_json(url, body, token=None, tenant=None):
    return http('POST', url, body=body, token=token, tenant=tenant)


def get(url, token=None, tenant=None, raw=False):
    return http('GET', url, token=token, tenant=tenant, raw=raw)


def csv_body():
    archivos = {}
    for nombre in ('planes', 'materias', 'alumnos', 'grupos', 'solicitudes'):
        with (DATA_DIR / f'{nombre}.csv').open('r', encoding='utf-8-sig', newline='') as fh:
            reader = csv.DictReader(fh)
            out = io.StringIO()
            writer = csv.DictWriter(out, fieldnames=reader.fieldnames, lineterminator='\n')
            writer.writeheader()
            writer.writerows(reader)
            archivos[nombre] = out.getvalue()
    return {'archivos': archivos}


def main():
    global BASE
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default=os.environ.get('IME_DEMO_BASE_URL', BASE))
    args = parser.parse_args()
    BASE = args.base_url.rstrip('/') + '/'

    fallos = 0
    aprobadas = 0
    ejecutadas = 0

    def paso(nombre, ok, detalle=''):
        nonlocal aprobadas, ejecutadas, fallos
        ejecutadas += 1
        if ok:
            aprobadas += 1
        else:
            fallos += 1
        registrar(nombre, ok, detalle)

    token = None
    status, data, _ = post_json(f'{BASE}token/', {'matricula': ADMIN_MATRICULA, 'password': ADMIN_PASSWORD})
    token = data.get('access') if status == 200 and data else None
    paso('POST /token/ admin demo_admin valido', token is not None, f'status={status}')

    status, data, _ = get(f'{BASE}membresias/me/', token=token)
    ok = status == 200 and data and data[0]['es_administrador'] and not data[0]['es_alumno']
    paso('GET /membresias/me/ admin es administrador', ok, f'status={status}')
    tenant = data[0]['tenant'] if ok else None
    paso('Se resolvio el tenant de la membresia', tenant is not None, f'tenant={tenant}')

    status, data, _ = post_json(f'{BASE}demo/importaciones/validar/', csv_body(), token=token, tenant=tenant)
    ok = status == 200 and data and data.get('valido') is True and data.get('errores') == []
    ok = ok and data.get('filas') == {'planes': 2, 'materias': 12, 'alumnos': 100, 'grupos': 24, 'solicitudes': 400}
    paso('POST /demo/importaciones/validar/ con CSV ficticios validos', ok,
         f'status={status} filas={data.get("filas") if data else None} errores={data.get("errores") if data else None}')

    status, data, _ = post_json(f'{BASE}demo/importaciones/confirmar/', csv_body(), token=token, tenant=tenant)
    paso('POST /demo/importaciones/confirmar/ importa sin errores', status == 200 and data and data.get('importado') is True,
         f'status={status}')

    status, grupos, _ = get(f'{BASE}demo/grupos/', token=token, tenant=tenant)
    paso('GET /demo/grupos/ lista 24 grupos del catalogo', status == 200 and isinstance(grupos, list) and len(grupos) == 24,
         f'status={status} n={len(grupos) if isinstance(grupos, list) else "n/a"}')

    status, stats, _ = get(f'{BASE}demo/estadisticas/', token=token, tenant=tenant)
    ok = status == 200 and stats and stats.get('alumnos') == 100 and stats.get('planes') == 2 and stats.get('materias') == 12 \
        and stats.get('grupos') == 24 and stats.get('solicitudes') == 400 and stats.get('publicacion_id') is None
    paso('GET /demo/estadisticas/ reporta escenario de 100 alumnos', ok, f'status={status} stats={stats}')

    status, _, _ = get(f'{BASE}demo/horario/me/', token=token, tenant=tenant)
    paso('GET /demo/horario/me/ admin sin publicacion -> 404', status == 404, f'status={status}')

    status, _, _ = get(f'{BASE}demo/horario/me/', token=None, tenant=tenant)
    paso('GET /demo/horario/me/ sin token -> 401', status == 401, f'status={status}')

    status, ejecucion, _ = post_json(f'{BASE}demo/asignaciones/generar/', {}, token=token, tenant=tenant)
    ok = status == 201 and ejecucion and ejecucion.get('estado') == 'BORRADOR'
    paso('POST /demo/asignaciones/generar/ crea Borrador', ok, f'status={status} ejecucion={ejecucion}')
    ejecucion_id = (ejecucion or {}).get('id') if ejecucion else None

    status, resultados, _ = get(f'{BASE}demo/asignaciones/{ejecucion_id}/', token=token, tenant=tenant)
    ok = status == 200 and isinstance(resultados, dict) and isinstance(resultados.get('resultados'), list)
    paso('GET /demo/asignaciones/{id}/ devuelve resultados', ok, f'status={status}')

    filas = (resultados or {}).get('resultados') or []
    resumen = (ejecucion or {}).get('resumen') or {}
    paso('GET /demo/asignaciones/{id}/ resumen consistente',
         resumen.get('alumnos') == 100 and resumen.get('asignadas', 0) + resumen.get('pendientes', 0) == len(filas),
         f'resumen={resumen} resultados={len(filas)}')

    status, data, _ = post_json(f'{BASE}demo/asignaciones/{ejecucion_id}/publicar/', {}, token=token, tenant=tenant)
    paso('POST /demo/asignaciones/{id}/publicar/ publica', status == 200 and data and data.get('estado') == 'PUBLICADO',
         f'status={status}')

    status, data, _ = post_json(f'{BASE}token/', {'matricula': ALUMIN_MATRICULA, 'password': ALUMIN_PASSWORD})
    token_alumno = data.get('access') if status == 200 and data else None
    status, data, _ = get(f'{BASE}demo/horario/me/', token=token_alumno, tenant=tenant)
    ok = status == 200 and data and data.get('ejecucion') == ejecucion_id and isinstance(data.get('resultados'), list) and len(data['resultados']) > 0
    paso('GET /demo/horario/me/ alumno con publicacion devuelve resultados propios', ok, f'status={status}')

    status, data, _ = get(f'{BASE}demo/asignaciones/', token=token, tenant=tenant)
    paso('GET /demo/asignaciones/ admin lista ejecuciones', status == 200 and isinstance(data, list) and len(data) >= 1,
         f'status={status} n={len(data) if isinstance(data, list) else "n/a"}')

    status, data, _ = get(f'{BASE}demo/asignaciones/{ejecucion_id}/csv/', token=token, tenant=tenant, raw=True)
    encabezado_ok = status == 200 and data is not None and data.splitlines()[0] == 'matricula,materia,grupo,estado,motivo,profesor,horarios'
    paso('GET /demo/asignaciones/{id}/csv/ encabezado exacto', encabezado_ok, f'status={status} header={data.splitlines()[0] if data else None}')

    status, _, _ = get(f'{BASE}demo/grupos/', token=token_alumno, tenant=tenant)
    paso('GET /demo/grupos/ alumno -> 403', status == 403, f'status={status}')
    status, _, _ = post_json(f'{BASE}demo/asignaciones/generar/', {}, token=token_alumno, tenant=tenant)
    paso('POST /demo/asignaciones/generar/ alumno -> 403', status == 403, f'status={status}')
    status, _, _ = get(f'{BASE}demo/asignaciones/', token=token_alumno, tenant=tenant)
    paso('GET /demo/asignaciones/ alumno -> 403', status == 403, f'status={status}')
    status, _, _ = get(f'{BASE}demo/estadisticas/', token=token_alumno, tenant=tenant)
    paso('GET /demo/estadisticas/ alumno -> 403', status == 403, f'status={status}')
    status, _, _ = post_json(f'{BASE}demo/importaciones/validar/', csv_body(), token=token_alumno, tenant=tenant)
    paso('POST /demo/importaciones/validar/ alumno -> 403', status == 403, f'status={status}')

    status, data, _ = post_json(f'{BASE}token/', {'matricula': ALUMIN_MATRICULA, 'password': 'Incorrecta2026!'})
    paso('POST /token/ credenciales invalidas -> 401', status == 401, f'status={status}')

    print(f"\nResumen: {aprobadas}/{ejecutadas} verificaciones HTTP APROBADAS, {fallos} fallidas.")
    return 1 if fallos else 0


if __name__ == '__main__':
    raise SystemExit(main())
