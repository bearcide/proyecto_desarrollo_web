# InscripcionMadeEasy

Proyecto académico para apoyar la inscripción escolar y la asignación de materias por institución. Busca reducir la incertidumbre, los conflictos de horario y la carga administrativa mediante un catálogo académico, reglas de prerrequisitos y propuestas de asignación verificables.

El repositorio contiene un MVP local con API Django REST Framework y una interfaz Vue 3. Su demostración usa datos ficticios; no constituye una validación de operación en producción.

## Integrantes del equipo

Integrantes oficiales confirmados por el equipo:

| Integrante | Matrícula |
|---|---|
| Cristian Michael Aguilar Chávez | 318039026 |
| Cecilia Sayuri Hernández Martínez | 320313503 |
| Emilio García Riba | **PENDIENTE: completar** |
| Violeta Camacho Ignacio | **PENDIENTE: completar** |

**Datos académicos pendientes:** institución, asignatura, grupo, profesor y periodo. El ADR original conserva los nombres y roles tal como se registraron históricamente; esta lista oficial actualiza la identificación del equipo sin alterar ese antecedente.

## Alcance implementado

- Autenticación JWT por matrícula y contraseña, renovación de tokens y selección de institución mediante membresías y `X-Tenant-ID`.
- API de instituciones, alumnos, planes, materias (nodos), prerrequisitos y estadísticas, con permisos y aislamiento por institución.
- Interfaz con áreas de administración y alumno, catálogo curricular y simulador de preselección. La simulación del alumno no equivale a una inscripción persistida.
- Demostración académica: validación y confirmación de CSV, consulta de grupos y estadísticas, generación de propuestas, publicación, resultados y exportación CSV.
- Motor de asignación greedy determinista: prioridad institucional, matrícula y preferencias; verifica plan, materias aprobadas, prerrequisitos, cupos y cruces del alumno. Conserva política y resultados para auditoría.
- Consulta del horario propio publicado y documentación OpenAPI.

El motor no garantiza un óptimo global. La demo mantiene una propuesta publicada por escuela, sin periodos académicos ni control de ocupación de profesores y aulas. SQLite se usa para la demo local secuencial.

### Propuestas futuras y alcance pendiente

Gestión de periodos, conflictos de aulas/profesores, optimización global y pruebas de carga para operación concurrente son ampliaciones pendientes. La integración institucional, el despliegue productivo y los pagos no se presentan aquí como funcionalidades verificadas de esta rama. El ADR inicial contiene objetivos de producto que deben distinguirse del alcance actual.

## Arquitectura

El navegador ejecuta una SPA Vue 3 con Vue Router, Pinia y Axios, servida en desarrollo por Vite. Consume JSON en `/api/v1/`; Axios adjunta JWT y el selector de institución. Django REST Framework expone vistas y serializadores; los servicios concentran reglas de identidad, importación, prerrequisitos y asignación. Los modelos Django persisten los datos mediante el ORM.

La configuración general usa `DATABASE_URL` y, si falta, SQLite. PostgreSQL está contemplado por el driver y Docker Compose. La configuración `config.settings_demo` selecciona exclusivamente una SQLite local `backend/demo_*.sqlite3`.

El [registro de arquitectura](docs/adr/README.md) conserva el ADR inicial de Django Templates + Bootstrap y explica por separado la evolución observada a DRF + Vue 3. Las plantillas y configuración Django dentro de `frontend/` son remanentes de una interfaz anterior; la guía siguiente ejecuta Vue mediante Vite.

## Organización del repositorio

| Ruta | Contenido |
|---|---|
| `backend/config/` | Configuración Django, rutas y configuración de demo |
| `backend/apps/core/api/` | Vistas REST, serializadores, permisos y errores |
| `backend/apps/core/models/` | Modelos académicos, membresías y asignaciones |
| `backend/apps/core/services/` | Reglas de negocio e importación |
| `backend/apps/core/repositories/` | Acceso especializado a prerrequisitos |
| `backend/apps/core/tests/` | Pruebas Python |
| `frontend/src/` | SPA Vue, módulos, componentes, stores y cliente API |
| `frontend/documentacion/` | ADR original |
| `demo_data/` | CSV ficticios para demostración |
| `scripts/demo/` | Validación de CSV y pruebas HTTP |
| `docs/` y `backend/docs/` | Contrato de API, QA y documentación técnica |

## Requisitos

- Python 3.10 o superior, `pip` y soporte para `venv`, según [requirements.txt](backend/requirements.txt).
- Node.js 18 o superior y npm para Vite 5; para reproducibilidad, usar el [package-lock.json](frontend/package-lock.json) con `npm ci`.
- Dos terminales y puertos locales 8000 (API) y 5173 (interfaz).
- PostgreSQL es opcional para la configuración general; no se requiere para la demo SQLite.

## Instalación y ejecución local

Comandos para Bash en Linux/macOS, desde la raíz del repositorio. En Windows deben adaptarse la activación del entorno y las variables de entorno.

### 1. Instalar dependencias

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cd frontend
npm ci
cd ..
```

### 2. Inicializar la demo (una sola vez)

```bash
source .venv/bin/activate
python -B backend/manage.py inicializar_demo --settings=config.settings_demo --con-datos
```

El comando crea una base **nueva** `backend/demo_backend_20261105.sqlite3`, aplica migraciones e importa 100 alumnos ficticios, 2 planes, 12 materias, 24 grupos y 400 solicitudes. Rechaza una base existente: si ya fue inicializada, omitir este paso y arrancar el servidor. No borrar una base para repetirlo. Para otra demo se puede definir `IME_DEMO_DATABASE` con otra ruta absoluta, nueva, dentro de `backend/`, cuyo nombre cumpla `demo_*.sqlite3`; usar la misma variable al inicializar y ejecutar.

### 3. Iniciar la API

```bash
source .venv/bin/activate
python -B backend/manage.py runserver 127.0.0.1:8000 --settings=config.settings_demo --noreload
```

### 4. Iniciar Vue en otra terminal

```bash
cd frontend
npm run dev -- --host 127.0.0.1
```

Abrir `http://127.0.0.1:5173`. El cliente usa por defecto `http://127.0.0.1:8000/api/v1`; para cambiarlo, definir `VITE_API_BASE_URL` antes de iniciar Vite. La API debe permitir el origen mediante CORS.

Usar las credenciales ficticias que informa el inicializador local para acceder como administrador o alumno de demostración. Seleccionar la escuela demo si la interfaz solicita institución. Generar y publicar una propuesta desde administración antes de consultar el horario del alumno; el inicializador no publica resultados.

Documentación local de API: `http://127.0.0.1:8000/docs/` y esquema `http://127.0.0.1:8000/api/v1/schema/`. Los recursos protegidos requieren autenticación y membresía válida.

### Configuración general (alternativa a la demo)

[backend/.env.example](backend/.env.example) enumera variables de seguridad y CORS. `backend/config/settings.py` selecciona la base mediante **`DATABASE_URL`**; los campos `POSTGRES_*` del ejemplo no la seleccionan por sí solos. Para PostgreSQL, configurar una URL `postgres://usuario:contraseña@host:5432/base`, aprovisionar la base y ejecutar `python backend/manage.py migrate`. El Compose de la raíz solo levanta PostgreSQL y requiere sus variables `POSTGRES_*`; no ejecuta Django ni Vue. Esta ruta requiere crear usuarios y membresías; consultar [identidad multi-tenant](backend/docs/identidad_multi_tenant.md). No usar las credenciales ni la clave fija de la demo en producción.

## Pruebas disponibles

Desde la raíz, con las dependencias instaladas:

```bash
source .venv/bin/activate
python -B backend/pruebas_aisladas.py
python3 scripts/demo/validate_demo_csv.py
cd frontend
npm test
npm run build
cd ..
```

La suite aislada comprueba modelos, identidad, permisos, grafos y el flujo de asignación/importación usando SQLite en memoria; bloquea conexiones SQLite a disco. Vitest prueba las reglas de `ValidadorInscripcion`. El build comprueba la compilación de Vue.

La integración HTTP necesita el servidor y una base demo dedicada inicializada; importa datos, genera y publica propuestas, por lo que modifica esa demo:

```bash
python3 scripts/demo/integration_demo.py --base-url http://127.0.0.1:8000/api/v1
```

[QA de la demo](docs/QA_DEMO.md) y [verificación previa del backend](backend/docs/DEMO_VERIFICACION.md) contienen resultados históricos, no una ejecución nueva. Hay referencias históricas a `backend/venv` y una errata `pruebas_aisoladas.py`; el archivo vigente es `backend/pruebas_aisladas.py`. El workflow de la raíz ejecuta npm sin cambiar a `frontend/`, donde está `package.json`; no se debe asumir que valida toda la aplicación.

## Documentación para la entrega

- [Diagnóstico y verificación documental](docs/DIAGNOSTICO_DOCUMENTACION.md).
- [Índice de decisiones de arquitectura](docs/adr/README.md).
- [ADR original, conservado sin cambios](frontend/documentacion/001-stack-y-arquitectura.md).
- [Evolución observada de la arquitectura](docs/adr/002-evolucion-observada.md).
- [Diagrama con proyecto e integrantes](docs/diagramas/diagrama_flujo_api_equipo.pdf).
- [Copia del diagrama original](docs/diagramas/diagrama_flujo_api_original.pdf).
- [Registro de incorporación del equipo al diagrama](docs/PROPUESTA_DIAGRAMA.md).
- [Contrato de la API de demostración](docs/DEMO_API_CONTRACT.md).
