# InscripcionMadeEasy — QA y datos para la demostración local (docs/QA_DEMO.md)

**Responsabilidades de esta capa (QA / datos):** `demo_data/`, `scripts/demo/`, `docs/QA_DEMO.md`.
**Fuera de alcance (no se modifican aquí):** `backend/` y `frontend/`.

Contrato vigente de referencia: `docs/DEMO_API_CONTRACT.md` (base URL `http://127.0.0.1:8000/api/v1/`,
JSON UTF-8, JWT por matrícula, `X-Tenant-ID` para multi-tenant).

## 1. Objetivo de la demostración

Ejecutar, contra el entorno local de demostración, un escenario académico ficticio de 100 alumnos:

- 2 planes de estudios, 12 materias, 24 grupos (profesores, cupos, horarios), 400 solicitudes.
- Preferencias académicas realistas (orden por `preferencia`, `prioridad_institucional`).
- Casos deliberados: sobrecupo (`SIN_CUPO`), cruces de horario (`CONFLICTO_HORARIO`), prerrequisitos (`PRERREQUISITOS`), materias ya acreditadas (`YA_APROBADA`).

Todo el catálogo es ficticio: sin datos personales reales.

## 2. Estado de las pruebas (distinción ejecutada / aprobada / pendiente)

| # | Prueba | Tipo | Estado | Resultado | Evidencia |
|---|---|---|---|---|---|
| 1 | Validación local de los CSV de demo | Local (solo archivos) | **EJECUTADA** | **APROBADA** | `scripts/demo/validate_demo_csv.py` → `VALIDACION OK` |
| 2 | Suite HTTP integración demo (import → generar → publicar → permisos → horario) | HTTP contra local | **PENDIENTE** | **PENDIENTE** | `scripts/demo/integration_demo.py` (pendiente de ejecución autorizada por coordinación con Codex) |
| 3 | Pruebas aisladas del backend (motor de asignación, grafo, import, permisos demo) | Backend aislado (SQLite en memoria) | **EJECUTADA** (por Codex) | **APROBADA** (62 pruebas) | `backend/pruebas_aisoladas.py` |

**Lectura de los estados:**

- **Ejecutada:** la prueba fue lanzada y terminó.
- **Aprobada:** terminó en verde (o su expectativa documentada se cumplió).
- **Pendiente:** no fue ejecutada todavía en esta sesión de QA (o quedó bloqueada por coordinación:
  Codex es el único responsable de inicializar/configurar la base de demo y el servidor Django).

La suite HTTP (fila 2) está **pendiente** por instrucción de coordinación en curso: antes de ejecutar
pruebas HTTP se debe consultar/solicitar la configuración de base y los endpoints oficiales con Codex.
Los scripts ya están preparados (`scripts/demo/integration_demo.py`, `scripts/demo/run_demo_tests.sh`).

## 3. Datos de demostración (`demo_data/`)

| Archivo | Contenido | Filas esperadas |
|---|---|---|
| `planes.csv` | 2 planes: `Bachillerato General`, `Ciclo Técnico en Gestión` | 2 |
| `materias.csv` | 12 materias (`BG1..BG6`, `CT1..CT6`) con cadena de prerrequisitos | 12 |
| `alumnos.csv` | 100 alumnos ficticios `D001..D100` (credencial `DemoLocal2026!`) | 100 |
| `grupos.csv` | 24 grupos (2 por materia) con profesores ficticios, cupos y horarios | 24 |
| `solicitudes.csv` | 400 solicitudes (4 por alumno) con preferencias y prioridad institucional | 400 |

**Escenario deliberado de sobrecupo (`SIN_CUPO`):** materia `BG5` Historia de México con cupo `2`
en cada grupo (`G1`, `G2`). Alumnos con preferencia sobre esa materia agotan cupo → pendientes `SIN_CUPO`.

**Escenario deliberado de cruces (`CONFLICTO_HORARIO`):**
- `BG2` Física I (G1: `Lunes:10:00-14:00`) y `BG3` Química I (G1: `Lunes:12:00-16:00`; G2: `Lunes:08:00-12:00`).
- Alumnos que solicitan Física y Química (preferencias consecutivas) quedan con la segunda materia
  `PENDIENTE` por cruce con su propia asignación.

**Escenario deliberado de prerrequisitos (`PRERREQUISITOS`):**
- Química I sin Matemáticas I aprobada; Biología General sin Química I; Marketing/Digital sin Informática;
  Administración de Empresas sin Gestión Financiera, etc.

**Escenario deliberado de acreditación (`YA_APROBADA`):** alumnos que solicitan materias de su
`aprobadas` (`BG2`, `BG5`, `CT2`, `CT4`, `CT3`, `CT5`).

`PLAN_INCORRECTO` no es reproducible vía CSV de importación (el import exige que la materia pertenezca
al plan del alumno); se cubre en la suite aislada del backend (`test_prerrequisitos_aprobadas_plan_y_cruces`).

## 4. Guía reproducible de demostración (local)

1. Backend con settings demo: `backend/venv/bin/python -B backend/manage.py runserver 127.0.0.1:8000 --settings=config.settings_demo --noreload`.
2. Base demo nueva: `backend/venv/bin/python -B backend/manage.py inicializar_demo --settings=config.settings_demo --con-datos`
   (ruta base: `backend/demo_backend_20261105.sqlite3`; con `IME_DEMO_DATABASE` puede apuntar a otra ruta nueva;
   nunca reutilizar ni borrar bases existentes).
3. Credenciales: admin `demo_admin` / `DemoLocal2026!`; alumno demo `D001` / `DemoLocal2026!`.
4. `python scripts/demo/validate_demo_csv.py` → validar los CSV.
5. `python scripts/demo/integration_demo.py --base-url http://127.0.0.1:8000/api/v1` → suite HTTP completa.
   (o `bash scripts/demo/run_demo_tests.sh`).
6. Flujo manual de demostración: token admin → import validar/confirmar → grupos → estadísticas →
   generar → publicar → resultados → CSV → horario del alumno.

## 5. Verificaciones de restricciones sobre los resultados

Para cada resultado de la ejecución publicada:

- `ASIGNADA`: `grupo` pertenece a la materia; no se solapa con las materias ya asignadas del alumno;
  `cupo` del grupo no excedido; prerrequisitos ⊆ aprobadas; materia ∉ aprobadas.
- `PENDIENTE`: motivo en {`YA_APROBADA`, `PRERREQUISITOS`, `PLAN_INCORRECTO`, `SIN_GRUPO`, `SIN_CUPO`, `CONFLICTO_HORARIO`};
  sin grupo asignado.
- Totales: `resumen.alumnos=100`, `asignadas + pendientes = solicitudes (400)`.

## 6. Criterios de cierre para la demo

- Suite HTTP en verde (estado actual: **pendiente de ejecución**).
- Resultado de generación reproducible (segunda ejecución idéntica en firma).
- Sin errores de importación ni de validación en los 5 CSV.
- Sin datos personales reales; credenciales y escuelas ficticias.

## 7. Puertos y comandos

- Validación local: `python scripts/demo/validate_demo_csv.py`
- Suite HTTP: `python scripts/demo/integration_demo.py --base-url http://127.0.0.1:8000/api/v1`
- Wrapper: `bash scripts/demo/run_demo_tests.sh`
