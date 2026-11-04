#!/usr/bin/env python3
"""Validación local (sin servidor, sin base de datos) de los CSV de demo.

Reglas espejo de backend/apps/core/services/importacion_csv.py y del contrato
docs/DEMO_API_CONTRACT.md. No escribe nada: solo lee demo_data/.

Uso: python scripts/demo/validate_demo_csv.py [--data-dir demo_data]
"""
import argparse
import csv
import io
import re
import sys
from pathlib import Path

DIAS = {'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo',
        'Miercoles', 'Sabado'}  # el backend acepta ambos spellings y normaliza al acentuado
HEADER = {
    'planes': ['nombre', 'descripcion'],
    'materias': ['plan', 'clave', 'nombre', 'creditos', 'semestre', 'prerrequisitos'],
    'alumnos': ['matricula', 'nombre', 'apellido_paterno', 'apellido_materno', 'plan', 'aprobadas', 'password'],
    'grupos': ['materia', 'clave', 'profesor', 'cupo', 'horarios'],
    'solicitudes': ['matricula', 'materia', 'preferencia', 'prioridad_institucional'],
}
BLOQUE = re.compile(r'([^:]+):(\d{2}):(\d{2})-(\d{2}):(\d{2})')
HORARIO_ESPERADO = {'planes': 2, 'materias': 12, 'alumnos': 100, 'grupos': 24, 'solicitudes': 400}


def leer(nombre, ruta):
    with ruta.open('r', encoding='utf-8-sig', newline='') as fh:
        reader = csv.DictReader(fh)
        filas = list(reader)
        return reader.fieldnames or [], filas


def main():
    base = Path(__file__).resolve().parents[2] / 'demo_data'
    errores = []
    datos = {}
    for nombre, esperado in HEADER.items():
        encabezado, filas = leer(nombre, base / f'{nombre}.csv')
        if sorted(encabezado) != sorted(esperado):
            errores.append(f'{nombre}.csv: encabezado {encabezado} != {esperado}')
        datos[nombre] = filas
        if len(filas) != HORARIO_ESPERADO[nombre]:
            errores.append(f'{nombre}.csv: filas {len(filas)} != esperado {HORARIO_ESPERADO[nombre]}')

    # Materias: claves por plan y grafo acíclico.
    claves_por_plan = {}
    for fila in datos['materias']:
        plan, clave, nombre, creditos, semestre, prereqs = (
            fila['plan'].strip(), fila['clave'].strip(), fila['nombre'].strip(),
            int(fila['creditos']), int(fila['semestre']), fila['prerrequisitos'].strip())
        claves_por_plan.setdefault(plan, set()).add(clave)
        if semestre < 1:
            errores.append(f"materias.csv semestre < 1 en {clave}")
        if creditos < 0:
            errores.append(f"materias.csv creditos < 0 en {clave}")
        for prereq in filter(None, (x.strip() for x in prereqs.split(';'))):
            if prereq not in claves_por_plan[plan]:
                errores.append(f"materias.csv {clave}: prereq {prereq} inexistente en plan {plan}")
    for plan, claves in claves_por_plan.items():
        grafo = {}
        for f in datos['materias']:
            if f['plan'].strip() != plan:
                continue
            grafo[f['clave'].strip()] = {p.strip() for p in filter(None, (x.strip() for x in f['prerrequisitos'].split(';'))) if p}
        estado = {}
        def visita(nodo, pila):
            if estado.get(nodo) == 1:
                return nodo in pila
            if estado.get(nodo) == 2:
                return False
            estado[nodo] = 1
            pila.append(nodo)
            for nxt in grafo.get(nodo, ()):
                if visita(nxt, pila):
                    return True
            pila.pop()
            estado[nodo] = 2
            return False
        for c in sorted(claves):
            if visita(c, []):
                errores.append(f"materias.csv: ciclo detectado en plan {plan} con clave {c}")

    # Alumnos: referencias y contadores.
    cuentas = set()
    for fila in datos['alumnos']:
        cuentas.add(fila['matricula'].strip())
        if fila['plan'].strip() not in claves_por_plan:
            errores.append(f"alumnos.csv {fila['matricula']}: plan {fila['plan']} sin materias")
        if len(fila['password']) < 8:
            errores.append(f"alumnos.csv {fila['matricula']}: password invalido")

    # Grupos: cupo y horarios.
    por_materia = {}
    for fila in datos['grupos']:
        materia, clave, profesor, cupo, horarios = (
            fila['materia'].strip(), fila['clave'].strip(), fila['profesor'].strip(),
            int(fila['cupo']), fila['horarios'].strip())
        if materia not in {f['clave'] for f in datos['materias'] if f['plan'].strip() in claves_por_plan}:
            errores.append(f"grupos.csv {materia}/{clave}: materia inexistente")
        por_materia.setdefault(materia, []).append((clave, cupo, horarios))
        bloques = []
        for item in filter(None, (x.strip() for x in horarios.split(';'))):
            m = BLOQUE.fullmatch(item)
            if not m or m.group(1) not in DIAS:
                errores.append(f"grupos.csv {materia}/{clave}: horario invalido {item}")
                continue
            h1, m1, h2, m2 = map(int, m.groups()[1:])
            inicio, fin = h1 * 60 + m1, h2 * 60 + m2
            if fin <= inicio:
                errores.append(f"grupos.csv {materia}/{clave}: fin <= inicio en {item}")
            if any(b['dia'] == m.group(1) and b['inicio'] < fin and inicio < b['fin'] for b in bloques):
                errores.append(f"grupos.csv {materia}/{clave}: bloques solapados en {item}")
            bloques.append({'dia': m.group(1), 'inicio': inicio, 'fin': fin})
        if cupo < 0:
            errores.append(f"grupos.csv {materia}/{clave}: cupo negativo")

    # Solicitudes: unicidad, preferencia, prioridad consistente.
    por_alumno = {}
    for fila in datos['solicitudes']:
        matricula, materia = fila['matricula'].strip(), fila['materia'].strip()
        preferencia, prioridad = int(fila['preferencia']), int(fila['prioridad_institucional'])
        if matricula not in cuentas:
            errores.append(f"solicitudes.csv {matricula}: alumno inexistente")
            continue
        if preferencia < 1:
            errores.append(f"solicitudes.csv {matricula}/{materia}: preferencia < 1")
        if prioridad < 0:
            errores.append(f"solicitudes.csv {matricula}/{materia}: prioridad < 0")
        prev = por_alumno.setdefault(matricula, set())
        if any(m == materia for m, _ in prev):
            errores.append(f"solicitudes.csv {matricula}: duplicada materia {materia}")
        prev.add((materia, preferencia))
        if len({p for _, p in prev}) != len(prev):
            errores.append(f"solicitudes.csv {matricula}: preferencias repetidas")

    if errores:
        print('VALIDACION FALLIDA')
        for e in errores:
            print(' -', e)
        return 1
    print('VALIDACION OK: 5 CSV, encabezados exactos, filas esperadas, referencias y formatos consistentes.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
