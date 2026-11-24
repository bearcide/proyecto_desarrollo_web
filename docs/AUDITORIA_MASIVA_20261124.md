# Auditoría integral de InscripcionMadeEasy V2

**Fecha:** 24 de noviembre de 2026 · **Base de código:** `e3568e42145d1df63f77f935d5908c395b81726c` · **Semilla:** `20261124`.

El PR #8 estaba abierto contra `main`, con CI en verde y la rama de entrega sincronizada. La auditoría utilizó el worktree `auditoria/masiva-v2-20261124` y bases SQLite independientes. La base de presentación se verificó mediante SHA-256 antes y después. Las mediciones corresponden al worktree aislado de auditoría. La rama de entrega y su base quedaron intactas.

## Resultado cuantitativo

| Escuela | Alumnos | Solicitudes | Asignadas | Pendientes | Licencias / suscripciones activas |
|---|---:|---:|---:|---:|---:|
| A | 200 | 1001 | 402 | 599 | 1 / 1 |
| B | 200 | 1001 | 393 | 608 | 1 / 1 |
| C | 200 | 1001 | 400 | 601 | 1 / 1 |
| **Total** | **600** | **3003** | **1195** | **1808** | **3 / 3** |

Cada escuela recibió dos planes curriculares, 16 materias, cuatro aristas de prerrequisitos y 24 grupos. Los docentes se registraron en el campo `profesor` de cada grupo, conforme al modelo actual. Hubo entre cuatro y seis solicitudes por alumno. Los administradores y el propietario bootstrap se crearon con el gestor oficial de usuarios de Django. Las instituciones, el catálogo comercial y las órdenes se crearon por API. Los alumnos, credenciales de alumnos, planes curriculares, materias, grupos y solicitudes se cargaron por el endpoint oficial CSV.

| Motivo | A | B | C | Total |
|---|---:|---:|---:|---:|
| `CONFLICTO_HORARIO` | 116 | 113 | 109 | 338 |
| `PRERREQUISITOS` | 133 | 150 | 147 | 430 |
| `SIN_CUPO` | 80 | 84 | 77 | 241 |
| `SIN_GRUPO` | 200 | 200 | 200 | 600 |
| `YA_APROBADA` | 70 | 61 | 68 | 199 |

Cada propuesta se ejecutó dos veces por escuela. Coincidieron política, resultados y resúmenes. Un verificador independiente, alimentado por los CSV, comparó cada decisión en orden de prioridad, matrícula y preferencia. Verificó materias acreditadas, requisitos cumplidos, oferta, cupos y cruces del alumno. Se publicó una propuesta por escuela y la consulta devolvió solo el horario del alumno autenticado. El motor es greedy y la prueba valida la política vigente. La disponibilidad de aulas o profesores y la optimalidad global quedan fuera de alcance.

## Importación, consistencia y permisos

- Se ejecutaron validación sin persistencia, confirmación y reimportación por institución. Se compararon los datos de negocio y el hash de contraseña del alumno de muestra antes y después de reimportar.
- Cada institución rechazó duplicados, filas incompletas, prerrequisitos inexistentes, referencias ajenas, contraseña de formato inválido y encabezados incorrectos. Se verificó rollback también cuando una fila previa ya había creado un usuario dentro de la transacción. Se comprobó que el alumno 201 no se crea si la licencia permite 200.
- Se probaron credenciales incorrectas, falta de sesión, JWT inválido, emisión y refresco, membresías y restricciones por rol. La matriz utilizó las seis direcciones entre las tres escuelas. Incluyó lectura, edición, publicación, cancelación, acceso a PDFs, importación con una referencia válida en la otra escuela y selección explícita del tenant ajeno.
- Se reabrió SQLite en otro proceso después de la carga. Los horarios y las órdenes persistieron y el snapshot de los modelos permaneció igual después de las peticiones de aislamiento.

**104 respuestas verificadas en 7.921 s** (`200` × 21, `400` × 6, `401` × 2, `403` × 21, `404` × 54). El archivo JSON conserva el detalle de cada solicitud.

## Comercial y navegador

Para cada escuela se comprobó el catálogo, la cotización de **600,00 MXN**, el conflicto por importe discrepante, la orden pendiente y el reintento idempotente. La importación y asignación se bloquearon con licencia ausente o pago pendiente. El administrador recibió rechazo al intentar confirmar una orden. El propietario la aprobó por la API DEMO, se verificó su repetición sin duplicar la transacción y se consultaron el acceso efectivo, la licencia activa, la suscripción mensual y el PDF interno marcado sin validez fiscal. Tres transacciones DEMO verificadas sumaron **1.800,00 MXN**. El recorrido de Chromium usó una copia separada para la revocación, una nueva compra, la nueva publicación y las demás operaciones visuales.

Chromium completó **18 escenarios**. Registró **0 excepciones JavaScript**, **0 escenarios fallidos** y **4 respuestas HTTP de error** durante los estados negativos intencionales: `400` en `/api/v1/demo/importaciones/confirmar/` × 1; `403` en `/api/v1/alumnos/me/` × 2; `403` en `/api/v1/demo/horario/me/` × 1.

| Escenario | Duración (s) |
|---|---:|
| login de administrador, alumno y propietario | 6.0991 |
| dashboard institucional | 0.5686 |
| catálogo curricular | 0.4411 |
| grupos y cupos | 0.4124 |
| alumnos | 0.3889 |
| planes comerciales | 0.5095 |
| suscripción institucional | 0.4496 |
| licencias institucionales | 0.6546 |
| formulario CSV valida, reimporta y presenta filas del archivo | 13.6520 |
| propuesta académica y publicación desde interfaz | 2.8999 |
| alumno A consulta perfil, materias y horario propio | 1.5693 |
| panel propietario | 0.4676 |
| instituciones propietario | 0.4090 |
| planes propietario | 0.3890 |
| suscripciones propietario | 0.3834 |
| licencias propietario | 0.3820 |
| transacciones propietario | 0.6893 |
| alumno C sin licencia y reposición mediante checkout DEMO del propietario | 6.8872 |

El registro también conserva las cancelaciones de solicitudes al navegar (net::ERR_ABORTED: 4).


## Mediciones

| Operación | A (s) | B (s) | C (s) |
|---|---:|---:|---:|
| Validar CSV y solicitudes por primera vez | 123.2544 | 128.4454 | 128.2425 |
| Confirmar CSV con 200 altas | 121.7928 | 127.3283 | 127.0379 |
| Reimportar el mismo paquete | 4.7712 | 4.2741 | 4.2409 |
| Ejecutar casos CSV negativos | 0.1114 | 0.1110 | 0.6789 |
| Generar propuesta | 0.3186 | 0.3139 | 0.3236 |
| Repetir propuesta | 0.2552 | 0.3248 | 0.2618 |
| Consultar detalle de asignación | 0.0412 | 0.0399 | 0.0416 |
| Publicar | 0.0128 | 0.0130 | 0.0131 |
| Horarios del alumno | 0.0083 | 0.0069 | 0.0074 |
| Consultar estadísticas | 0.0096 | 0.0078 | 0.0105 |
| Consultar alumnos | 0.0115 | 0.0106 | 0.0133 |
| Recorrido comercial DEMO completo | 0.1055 | 0.1039 | 0.0968 |

Generar los 15 CSV tomó **0.0141 s**. Las tres validaciones iniciales sumaron **379.94 s** y las tres confirmaciones **376.16 s**. En Chromium, validar nuevos alumnos tomó **136.61 s** y confirmarlos **134.35 s** en ejecuciones separadas del formulario.

Los tiempos de API se midieron con `perf_counter` alrededor de solicitudes DRF en proceso, en segundos de pared, con los hashers normales de Django. No representan latencia de red, capacidad concurrente ni un SLA. La validación genera temporalmente los usuarios dentro de una transacción que revierte, por lo que paga el coste de hash aunque no persista registros. La reimportación reutiliza las cuentas. La prueba de Chromium mide el recorrido HTTP con Vite y Django locales. Hubo ejecución paralela de otras comprobaciones sobre archivos SQLite distintos, por lo que los tiempos de CPU pueden variar.

## Hallazgos y correcciones

| Severidad | Hallazgo | Corrección o estado |
|---|---|---|
| Bloqueante para la carga masiva en la presentación | Axios limitaba ambas operaciones CSV a 15 segundos, frente a más de dos minutos medidos con 200 usuarios nuevos. | Aumenté a 300 segundos el límite solo para validar y confirmar CSV. Chromium verificó ambas operaciones con datos nuevos. |
| Grave para la demostración | La vista de licencias esperaba un arreglo y, al recibir el mapa real de Django, mostraba módulos de ejemplo, incluso soporte que la licencia no ofrecía. También podía rotular el valor cero como ilimitado. | La vista enumera únicamente los módulos habilitados y conserva los límites devueltos por el servidor. |
| Moderado | Después de una importación exitosa, un segundo intento fallido podía conservar el mensaje verde anterior. | Se limpia el resultado anterior al iniciar una validación o confirmación. La regresión en navegador contrasta éxito seguido de CSV rechazado. |
| Moderado | La importación inicial sigue siendo síncrona. El límite de 300 segundos está probado para estos lotes de 200; el tamaño máximo admitido por el parser no implica que todo lote termine a tiempo. | La corrección se limita al tamaño demostrado. Un flujo asíncrono con progreso queda pendiente. |
| Menor | Un alumno con horario bloqueado puede ver el encabezado «Horarios en proceso» junto al aviso de falta de licencia. | El acceso continúa bloqueado. Se documenta como mejora visual. |
| Funcionalidad futura | La preinscripción es un simulador del catálogo. La publicación oficial proviene de las solicitudes importadas y del motor del servidor. | Se verifican por separado. Quedan fuera CFDI/PAC, ERP, checkout externo y la disponibilidad de aulas o docentes. |

Chromium reprodujo un bloqueo adicional en **Transacciones del propietario**. La vista no montaba
por la referencia `solicuciones` escrita incorrectamente, y la descarga usaba el identificador de
transacción cuando el endpoint exige el del comprobante. La API ahora expone el comprobante y la institución
en lectura, sin cambiar los pagos ni las migraciones. La regresión monta la vista, consulta transacciones y
solicitudes y descarga el PDF interno real. Los filtros de fecha, institución y estado que la vista envía
siguen sin un contrato de filtrado en el endpoint de transacciones. Es un hallazgo moderado de alcance operativo.

La primera ejecución masiva registró una discrepancia del arnés al seleccionar una escuela ajena. El cliente
de pruebas sobrescribía el encabezado suministrado y enviaba la escuela propia. La matriz final, con un cliente
independiente por encabezado, reemplaza esa comprobación. También se ajustaron selectores del arnés de navegador
para usar la matrícula tal como se muestra en la interfaz.

## Validación técnica

- Django 6.1.3 sobre SQLite 3.45.1, Node v20.20.2, arquitectura x86_64.
- Suites académica y comercial Django: **97 pruebas aprobadas**. `check`, `makemigrations --check --dry-run` y `migrate --check` correctos.
- Vitest: **90 pruebas aprobadas en 11 archivos**. Vite: **176 módulos compilados**. `git diff --check` correcto.
- PostgreSQL concurrente no se ejecutó. No había una instancia accesible y el socket de Docker denegó acceso. Tampoco se ejecutó Stripe externo. Todos los pagos del ejercicio usaron el proveedor DEMO sin Stripe y los comprobantes fueron internos.

## Reproducción y protección de la presentación

Usa un worktree de auditoría con estas correcciones y una carpeta de salida **nueva** fuera del repositorio. Los scripts crean la SQLite con apertura exclusiva. El modo de navegador usa una copia independiente para la revocación, reposición y publicación. Nunca apuntes los scripts a la base ni a los puertos de presentación.

Desde la raíz del worktree de auditoría:

```bash
export CHECKOUT="$PWD"
export PYTHON=/ruta/al/venv/bin/python
export IME_PLAYWRIGHT=/ruta/herramientas/node_modules/playwright
# Generar una clave exclusiva de la ejecución. No reutilizar contraseñas reales.
export IME_AUDIT_PASSWORD="$(openssl rand -hex 16)"
AUDIT_RUN="$(mktemp -d /tmp/ime-auditoria.XXXXXX)"
SCRIPTS="$CHECKOUT/scripts/auditoria_v2"

"$PYTHON" -m pip install -r "$CHECKOUT/backend/requirements.txt"
npm --prefix "$CHECKOUT/frontend" ci
"$PYTHON" "$SCRIPTS/auditoria.py" --checkout "$CHECKOUT" --salida "$AUDIT_RUN/masiva"
bash "$SCRIPTS/validar-y-navegar.sh" "$CHECKOUT" "$AUDIT_RUN/masiva" "$AUDIT_RUN/chromium"

"$PYTHON" "$SCRIPTS/auditoria.py" --checkout "$CHECKOUT" --salida "$AUDIT_RUN/fresca" --preparar
bash "$SCRIPTS/correr-navegador.sh" "$CHECKOUT" \
  "$CHECKOUT/backend/demo_pagos_auditoria_fresca.sqlite3" \
  15175 18085 "$SCRIPTS/importar-nuevo.cjs" "$AUDIT_RUN/fresca"
unset IME_AUDIT_PASSWORD
```

Prepara Playwright y Chromium en un directorio de herramientas aparte antes de ejecutar el navegador. Si repites las pruebas en el mismo worktree, usa nombres de salida nuevos e incluye ese nombre en la ruta SQLite. Los scripts conservan JSON con mediciones y resultados, CSV sintéticos, PDF internos y capturas en la carpeta de salida. Estos archivos se mantuvieron fuera de Git. Los puertos de auditoría son distintos de Vue 5174 y API 18082 usados para presentar.

## Integración de este cambio

La rama de auditoría parte de `fix/entrega-v2-20261124` (PR #8). Su PR separado tiene esa rama como base temporal para mostrar solo las correcciones y los materiales de auditoría. Tras integrar el PR #8, cambia la base del PR de auditoría a `main` y revisa los archivos y CI. Si el PR #8 ingresó por squash o rebase y GitHub vuelve a mostrar sus cambios, traslada únicamente el commit de auditoría a una rama nueva desde `main` y revisa ese diff antes de integrar.
