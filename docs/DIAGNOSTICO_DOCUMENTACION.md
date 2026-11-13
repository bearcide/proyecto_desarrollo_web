# Diagnóstico documental

Revisión del worktree `proyecto_desarrollo_web_docs`, rama `docs/readme-adr`. Diagnóstico comunicado antes de crear los archivos; registro completado el 2026-11-13.

## Hallazgos

| Observación | Evidencia | Tratamiento |
|---|---|---|
| Falta README en la raíz | Inventario inicial del repositorio | Crear guía en español con identificación, alcance y ejecución |
| ADR inicial existente | `frontend/documentacion/001-stack-y-arquitectura.md`; historial `1e42040`, `a7e8810` | Conservar íntegro y enlazar desde índice y README |
| Diferencia entre ADR y código | ADR propone Templates/Bootstrap; `frontend/package.json` y API usan Vue/DRF | Registro separado de evolución observada pendiente de validación |
| Integrantes oficiales confirmados | Cuatro nombres y dos matrículas proporcionados por el equipo | Actualizar documentación vigente y cartela; conservar ADR histórico |
| Diagrama localizado posteriormente | PDF proporcionado desde V2 por el equipo | Copiar original y preparar versión con cartela en este worktree |
| Documentación anterior contradictoria | `frontend/README_FUSION.md` describe falta de JWT y endpoints ahora presentes | Referenciar el código actual, conservar el documento histórico |
| Pruebas históricas no equivalen a nueva ejecución | QA marca HTTP pendiente y verificación backend registra una ejecución previa | Separar resultados históricos de verificaciones de esta tarea |

## Verificación y límites

Se contrastaron comandos con los scripts, las opciones del inicializador, configuración demo, rutas de API, dependencias y scripts npm. Se comprobó que `DATABASE_URL` selecciona la base general; `POSTGRES_*` no sustituye esa variable en Django. La demo rechaza una base ya existente y el inicializador aplica migraciones por sí mismo.

El entorno disponible tiene Python 3.12.3, Node 20.20.2 y npm 10.8.2. Este worktree no tiene `backend/venv/bin/python` ni `frontend/node_modules/.bin/vitest`. No se instalaron dependencias, levantaron servidores, inicializaron bases ni ejecutaron pruebas HTTP que escriben datos. Los comandos de arranque y suites se verificaron por inspección; no se declara una ejecución integral nueva.

Verificación final ejecutada: todos los enlaces relativos de los cinco archivos nuevos resuelven; bloques de código Markdown balanceados; ADR original idéntico byte a byte a HEAD; ningún archivo previamente versionado modificado; `git diff --check` sin incidencias. Se ejecutó `python3 -B scripts/demo/validate_demo_csv.py`: **VALIDACION OK**, cinco CSV con encabezados, filas, referencias y formatos consistentes. Las suites Django, Vitest y HTTP y el build siguen sin ejecutarse en esta tarea. No se realizaron commits ni push.

## Comprobación del README y Git

`README.md` existe en la raíz. `git ls-files -- README.md` no devuelve entradas porque aún no está versionado. `git status --short` lo muestra como `?? README.md`; `git status --untracked-files=all` también lo enumera. `git check-ignore -v README.md` no devuelve reglas (salida 1: no ignorado). No se reproduce la ausencia indicada en una consulta anterior y no hay evidencia para atribuirle una causa concreta. No se ha añadido nada al índice.

## Integrantes oficiales actuales

| Integrante | Matrícula |
|---|---|
| Cristian Michael Aguilar Chávez | 318039026 |
| Cecilia Sayuri Hernández Martínez | 320313503 |
| Emilio García Riba | PENDIENTE |
| Violeta Camacho Ignacio | PENDIENTE |

## Pendientes del equipo

Completar las matrículas de Emilio García Riba y Violeta Camacho Ignacio y los datos de asignatura; validar el registro posterior de evolución arquitectónica. El diagrama ya fue localizado y se preparó su versión identificada. El ADR 001 conserva íntegros su contenido y formato originales.
