# Estado de implementación

Corte de revisión: 13 de noviembre de 2026. Este documento separa la versión publicada del desarrollo local y define el alcance de la verificación.

## Versiones examinadas

| Fuente | Referencia | Contenido |
|---|---|---|
| GitHub `origin/main` | `1b8ddf2` | MVP académico, PR #4 documental y PR #5 de CI integrados |
| V2 local | `feature/fase2-ia`, HEAD `e61e3b7`, con cambios sin commit | Interfaz académica evolucionada, aplicación comercial y paneles de institución/propietario |
| Propuesta documental | `docs/limpieza-entrega`, basada en `1b8ddf2` | Edición de documentación; no incorpora código de V2 |

V2 se inspeccionó en `proyecto_desarrollo_web_v2`. Las rutas comerciales de evidencia que siguen son relativas a ese worktree; no existen todavía en el checkout de `main`. No se enlazan como archivos publicados para evitar aparentar que están disponibles al clonar el repositorio.

El trabajo local se distribuye entre Codex (backend y servicios comerciales), Antigravity (frontend principal y contratación institucional) y OpenCode (panel del propietario). Esta coordinación no sustituye la validación de integración.

## Criterios de clasificación

- **Implementada y verificada:** comportamiento respaldado por código y pruebas ejecutadas en esta revisión, dentro del alcance indicado.
- **Implementada parcialmente:** existen rutas o componentes operativos, pero falta una parte relevante del flujo o su integración.
- **En desarrollo:** trabajo concreto de integración o validación aún abierto.
- **Propuesta, sin implementación:** no se encontró un flujo que resuelva la capacidad solicitada; puede existir un puerto o dato preparatorio.

Las clasificaciones son por capacidad, no por mera presencia de archivos. «Verificada» no implica preparación productiva ni validación con servicios externos.

## Matriz funcional

En las referencias abreviadas, `core/` y `comercial/` corresponden a `backend/apps/core/` y `backend/apps/comercial/`. La evidencia de interfaz corresponde a `frontend/src/modules/comercial/`, salvo el router global. Las suites respaldan los comportamientos descritos; no implican cobertura exhaustiva de cada operación.

| Capacidad | Disponibilidad | Estado y evidencia |
|---|---|---|
| JWT, membresías y aislamiento institucional | main y V2 | **Implementada y verificada** en suites Django; `core/services/identidad.py`, permisos y pruebas API |
| Catálogo académico y prerrequisitos | main y V2 | **Implementada y verificada**: modelos/API, reglas y suite de grafos |
| Importación CSV transaccional | main y V2 | **Implementada y verificada**: validación, confirmación y rollback; pruebas de errores y aislamiento |
| Asignación, publicación y horario propio | main y V2 | **Implementada y verificada** por pruebas API y motor; greedy, sin garantía de óptimo global |
| Experiencia académica Vue | main; cambios visuales adicionales en V2 | **Implementada parcialmente** en términos de validación integral: reglas unitarias aprobadas; en V2 se prueban rutas y navegación, sin recorrido completo de navegador |
| Planes y precios comerciales | Solo V2 | **Implementada y verificada** por API: `comercial/models.py`, `api.py`, `services.py`, `tests.py`; importes MXN, precio base más cantidad declarada, condiciones copiadas a la orden |
| Contratos institucionales | Solo V2 | **Implementada y verificada** por API: estado, fechas y aprobación del propietario; requisito para modalidad empresarial. Sin negociación ni firma electrónica |
| Checkout DEMO | Solo V2 | **Implementada y verificada** por API: idempotencia por institución, orden pendiente, confirmación exclusiva del propietario, licencia y comprobante; sin cobro bancario |
| Checkout y webhooks Stripe | Solo V2 | **Implementada parcialmente**: SDK, verificación de firma, consulta de objetos, deduplicación y rechazo de eventos live probados con mocks/firma local. Falta sandbox externo extremo a extremo |
| Suscripciones y licencias | Solo V2 | **Implementada y verificada** en lógica/API simulada: activación, renovación, vencimiento, revocación y cancelación al fin del periodo. Renovación externa depende de la validación Stripe pendiente |
| Licencia como requisito académico | Solo V2 | **Implementada y verificada**: `comercial/academic.py`, migración `core.0005`, pruebas REST/CSV y asignación. Instituciones anteriores mantienen transición hasta su primera orden |
| Límite de alumnos | Solo V2 | **Implementada y verificada**: altas y generación/publicación comprueban capacidad; se cuentan también alumnos inactivos |
| Planteles | Solo V2, como límite contractual | **Implementada parcialmente**: se conserva límite y se exige capacidad para una institución; falta entidad académica de sedes y su administración |
| Comprobantes internos y solicitud fiscal | Solo V2 | **Implementada y verificada** por API: PDF sin validez fiscal, solicitud y validaciones de formato; `comercial/api.py`, `fiscal.py` y pruebas |
| Emisión CFDI mediante PAC | No publicada | **Propuesta, sin implementación** operativa: puerto abstracto, sin emisión ni timbrado |
| Contratación institucional Vue | Solo V2 | **Implementada parcialmente**: vistas y servicios de catálogo, configurador, checkout, suscripción y licencias; pruebas unitarias y de router, con fallbacks offline y desajustes descritos abajo |
| Panel del propietario SaaS | Solo V2 | **Implementada parcialmente**: listados, indicadores, cancelación, revocación, solicitud fiscal y descarga con pruebas; faltan acciones de alta/edición de catálogo, aprobación de contrato y confirmación DEMO desde ese panel |
| Integración comercial de extremo a extremo | Solo V2 | **En desarrollo**: falta verificar contratación real desde navegador y consistencia de todos sus estados con API |
| Reembolsos, disputas, prorrateo, cambio de plan y conciliación | No publicada | **Propuesta, sin implementación** de flujos en la API examinada |
| Cobranza escolar a alumnos | No publicada | **Propuesta, sin implementación** si se incorpora a futuro; fuera del dominio comercial B2B actual |

## Decisiones de implementación comercial observadas

La API `/api/v1/comercial/` usa el Tenant existente. El propietario global requiere `is_superuser`; `is_staff` no otorga autoridad comercial. Las operaciones institucionales conservan JWT, membresía y selección de escuela. No hay claves Stripe en el cliente.

`Precio` contempla `monthly`, `annual`, `process`, `institutional`, `perpetual`, `hybrid`, `enterprise` y `maintenance`. La modalidad por proceso vende una licencia temporal a la institución, no cobra cada inscripción individual. El híbrido calcula base más alumnos declarados al contratar, sin medición posterior de uso. Mantenimiento es recurrente e independiente de la licencia perpetua.

El servidor calcula el importe, conserva condiciones de compra y limita el checkout mediante `Idempotency-Key`. Los efectos de pago y la deduplicación de eventos usan transacciones y referencias únicas. El retorno del navegador no acredita un pago. En Stripe, las suscripciones dependen de facturas pagadas; la vigencia efectiva se calcula con fechas, estado y contrato.

Los módulos académicos verifican la licencia después de identidad y membresía. El login, la renovación JWT y la API comercial permanecen disponibles para recuperar el acceso. La transición conserva instituciones preexistentes; una primera orden la termina aunque quede pendiente. La migración y los tests respaldan ese comportamiento, no una política comercial aprobada para producción.

## Integración y problemas conocidos

Todos los problemas de esta sección corresponden a **V2 local**, no al MVP publicado en main.

| Punto | Evidencia del código local | Alcance y validación pendiente |
|---|---|---|
| Retorno de Stripe | `backend/config/settings.py`: URLs predeterminadas `/contratacion/exito` y `/contratacion/cancelado`; `frontend/src/router/index.js`: `/admin/comercial/checkout/resultado` | No coinciden. Alinear las URLs y el contexto de la orden; comprobar éxito y cancelación en navegador. El retorno no debe activar una licencia |
| Respuestas simuladas ante fallos de red | `cliente/api/comercialService.js`: ramas `!err.response` con catálogos, acceso y órdenes en memoria | La interfaz puede mostrar datos ficticios cuando el servidor no respondió; no acreditan persistencia ni acceso real. Separar y señalar el modo offline antes de presentar una contratación integrada |
| Confirmación visual DEMO | `cliente/components/DemoConfirmModal.vue` y `cliente/views/CheckoutResultadoView.vue`: `marcarOrdenDemoPagada` | Cambia una orden local, no llama a la confirmación persistida del propietario. No confundir con `POST /api/v1/comercial/demo/confirmar/` |
| Precio visual y precio del servidor | `cliente/domain/comercialCalculos.js`: recargos por sedes y complementos; `backend/apps/comercial/services.py`: `precio.importe + precio.por_alumno * alumnos` | El checkout admite precio, alumnos y contrato. Alinear el cotizador con esa fórmula o implementar las condiciones adicionales; no presentar los recargos visuales como contratados |
| Operaciones del propietario | `propietario/services/apiComercial.js` y vistas: consultas, cancelación, revocación, solicitud fiscal y descarga | Faltan alta/edición del catálogo, aprobación de contratos y confirmación DEMO desde el panel; las operaciones existentes por API no equivalen a una interfaz completa |
| Indicadores del propietario | `propietario/services/apiComercial.js`: consultas agregadas y delegación parcial al servicio compartido | Falta acreditar resultados completos con paginación y fallos parciales. Los tests unitarios no verifican todos esos escenarios |
| Stripe externo | `comercial/services.py`, webhook en `comercial/api.py` y mocks en `comercial/tests.py` | Checkout, firma y deduplicación tienen pruebas locales; no se ha validado una cuenta sandbox, entrega real de eventos, renovación y cancelación extremo a extremo |
| Emisión fiscal | `comercial/fiscal.py`: puerto abstracto y `FiscalNoConfigurado`; API de comprobantes internos | No hay PAC operativo ni timbrado CFDI. La solicitud de factura y el PDF interno no constituyen una factura fiscal |
| Despliegue productivo | Configuraciones SQLite de demostración y tests en memoria; PostgreSQL configurable | No se acreditaron concurrencia en PostgreSQL, operación live, capacidad, recuperación ni observabilidad productiva |

El servicio del propietario ya usa rutas del contrato, aunque su README local conserva referencias antiguas a rutas provisionales. El límite contractual de planteles tampoco equivale a una entidad académica de sedes: los textos de la interfaz no demuestran administración multi-campus.

## Demostración comercial local

Estos comandos corresponden **solo a V2** con sus cambios comerciales presentes. Se verificaron contra los argumentos del script y la configuración; no se ejecutó una nueva siembra durante esta auditoría. Desde la raíz de una copia operativa de V2, con entorno Python activado y dependencias de su `backend/requirements.txt` instaladas:

```bash
export PAGOS_DEMO_DATABASE="$PWD/backend/demo_pagos_revision_nueva.sqlite3"
python -B backend/demo_pagos.py --database "$PAGOS_DEMO_DATABASE"
python -B backend/manage.py runserver 127.0.0.1:8011 --noreload --settings=config.settings_pagos_demo
```

El nombre debe ser nuevo: el script rechaza archivos existentes, symlinks y rutas fuera de `backend/demo_pagos_*.sqlite3`. Crea y migra esa base, siembra dos instituciones ficticias, catálogo, usuarios y datos académicos. Las credenciales locales se consultan en su salida. No utilizar las bases académicas existentes ni repetir la creación sobre el mismo archivo.

En otra terminal, desde `frontend/`, con dependencias instaladas y un puerto libre:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8011/api/v1 npm run dev -- --host 127.0.0.1 --port 5174
```

La configuración de pagos permite CORS para 5174 y fuerza proveedor DEMO, sin claves Stripe. Si los puertos están ocupados, elegir otros sin detener servicios y ajustar URL/CORS. La confirmación DEMO persistida se realiza por API como propietario; el botón de simulación local no la sustituye. El script admite `--verificar` para un recorrido adicional sobre una base nueva, que genera movimientos exclusivamente DEMO.

### Stripe sandbox

`settings_pagos_demo` no activa Stripe al exportar variables: fuerza DEMO y vacía las claves. Para probar Stripe se necesita una configuración local separada que conserve una base dedicada y lea del entorno `COMMERCIAL_PROVIDER=stripe`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `COMMERCIAL_SUCCESS_URL` y `COMMERCIAL_CANCEL_URL`. El servicio exige una clave de prueba; no acepta modo live.

Las URLs de retorno deben apuntar a las rutas reales del router Vue (`/admin/comercial/checkout/resultado` con el contexto necesario). Los valores predeterminados del backend usan `/contratacion/...`, que no está registrada en el router inspeccionado. Esa integración requiere corrección y prueba por los responsables del código antes de afirmar que el checkout de navegador está completo.

El contrato local `docs/CONTRATO_COMERCIAL_API.md` detalla `/webhooks/stripe/`, los eventos y los cuerpos esperados. `docs/GUIA_DEMO_PAGOS.md` contiene la guía operativa y sus verificaciones históricas; `docs/INFORME_COMERCIAL_BACKEND.md`, el informe de implementación. Los tres siguen solo en V2; no se copian aquí ni se publican sus datos de demostración como operaciones reales.

## Validación y preparación productiva

La auditoría que sustenta este corte ejecutó copias temporales del código, sin cargar archivos `.env` de los worktrees ni modificar V2. La revisión editorial final no repitió estas suites, porque no hubo cambios de código:

| Fuente | Ejecución | Resultado |
|---|---|---|
| main | Django `apps.core.tests` con settings aislados | 62 aprobadas |
| main | Vitest sin caché | 12 aprobadas, 1 archivo |
| V2 local | Django `apps.core apps.comercial` con settings aislados | 95 aprobadas |
| V2 local | Vitest sin caché | 88 aprobadas, 11 archivos |

Para repetir la suite comercial en una copia de V2 con dependencias instaladas, desde su raíz:

```bash
python -B backend/manage.py test apps.core apps.comercial --settings=apps.core.tests.settings_aislados --noinput
cd frontend
npm test -- --cache=false
```

La validación de los cinco CSV publicados también se ejecutó en esta revisión y aprobó encabezados, cantidades, referencias y formatos.

Se usó el entorno Python ya disponible y dependencias Node locales. No se verificó una instalación nueva de todos los paquetes. Las pruebas usan SQLite en memoria, Stripe simulado y firma local; no se ejecutó una nueva prueba de navegador, build, migración persistente, llamada autenticada a Stripe ni emisión fiscal. Los informes locales previos citan 87 Vue; el corte actual incluye una prueba adicional de navegación y ejecutó 88. No se publica una cifra de cobertura.

Antes de producción faltan validar Stripe y webhooks reales de sandbox, completar integración visual sin simulaciones ambiguas, probar concurrencia sobre PostgreSQL y definir despliegue, observabilidad, conciliación y recuperación de eventos. La presencia de modelos y tests no demuestra operación con clientes ni ingresos reales.
