# Fusión Frontend + API REST

El frontend ya no usa `mock_data.py`. Las vistas Django solo entregan HTML; el JS consume `/api/v1/`.

## Arquitectura JS (`src/infrastructure/static/js/`)
| Archivo | Rol |
|---|---|
| `api.js` | `apiFetch()` (headers, JSON, errores `ApiError`), `apiList()` (recorre paginación DRF), `API.*` (un método por recurso), `Session`, `Auth`, `requireSesion()` |
| `domain.js` | Adaptadores API→UI (`materiaDesdeNodo`, `cargarCatalogo`), reglas de UI, cuadrícula, avisos |
| `inscripcion.js`, `dashboard.js`, `horario.js`, `login.js` | Una por pantalla |

## Endpoints conectados
`GET /alumnos/?search=` (login por matrícula) · `GET /alumnos/{id}/` · `GET /planes-estudios/{id}/` ·
`GET /nodos/?plan_estudios=` · `GET /estadisticas-nodos/`. También definidos en `API`: tenants, prerrequisitos, planes (lista).

## Configuración (`.env` del frontend)
`API_BASE_URL` (default `http://127.0.0.1:8001/api/v1`), `API_DEV_TOKEN`, `API_LOGIN_PATH` (vacío = login simulado),
`API_TENANT_ID` (opcional), `API_WITH_CREDENTIALS`.

Requiere `python-decouple` en el entorno del frontend (ya lo usaba `settings.py`).

## Lo que el backend actual NO permite todavía (no modificado, por instrucción)
1. **Autenticación/tenant:** `TieneTenant` exige `request.user.tenant`, pero no existe un User con `tenant`
   ni endpoint de login, y la auth es `SessionAuthentication`. Hasta entonces **toda llamada responde 403**.
   El header `Authorization: Bearer` se envía, pero DRF no lo interpreta sin JWT. Tampoco se lee un header de tenant.
2. **CORS:** en el `.env` del backend: `CORS_ALLOWED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000`
   (y `CORS_ALLOW_CREDENTIALS=True` si se usa sesión + `API_WITH_CREDENTIALS=True`).
3. **Datos inexistentes en la API:** horarios, profesor, cupo, materias aprobadas por alumno, número y ventana de
   inscripción, y un endpoint de inscripciones. El frontend los lee de forma opcional (`cupo`, `profesor`, `horarios`,
   `alumno.materias_aprobadas_ids`, `alumno.ventana_inicio`, `API.inscripciones`): al agregarlos, las pantallas se activan
   sin cambiar el HTML.

## Comportamiento actual
- Login: solo busca la matrícula en la API; **la contraseña no se valida** (aviso visible en modo DEBUG).
- Inscripción: lista las materias reales del plan del alumno; la selección se guarda en `sessionStorage`.
  "Confirmar" avisa que falta el endpoint; no simula éxito.
- Home: el horario del hero es ilustración estática.
