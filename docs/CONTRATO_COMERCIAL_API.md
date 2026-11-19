# API comercial B2B — v1

Esta API vende software a instituciones (`core.Tenant`). No registra colegiaturas ni pagos de alumnos. Base: `/api/v1/comercial/`. JSON UTF-8, UUID para recursos, importes como cadenas decimales MXN, fechas ISO 8601 UTC. Contrato publicado para Antigravity y OpenCode; consultar el informe de validación para límites de implementación.

## Identidad y permisos

JWT: `Authorization: Bearer <access>`, renovación por `/api/v1/token/refresh/`. Administrador escolar: membresía activa con `es_administrador=True`, escuela activa, selector `X-Tenant-ID` obligatorio cuando tiene varias escuelas. No se acepta tenant del cuerpo para escoger la institución. Propietario SaaS: usuario activo `is_superuser=True`; `is_staff` solo no concede acceso global. El propietario selecciona escuela por `X-Tenant-ID`.

Login usa `{matricula,password}` en `/api/v1/token/`. JWT incluye `is_superuser` como ayuda para navegación Vue y lo conserva al refrescar; los permisos se resuelven contra usuario y membresía actuales en Django. `Tenant.licencia_requerida` es metadato de solo lectura, no una opción editable por la API.

## Control de acceso académico V2

Los endpoints académicos comprueban módulos contratados además del permiso original: `alumnos`, `planes_estudios` (incluye materias/prerrequisitos), `reportes`, `horarios` (incluye grupos), `asignaciones` e `importaciones`. CSV también exige el módulo de cada archivo. Ausencia de módulo/licencia vigente devuelve 403 `license_required`; exceso de capacidad devuelve 403 `license_limit`. Los límites de alumnos se comprueban en altas REST/CSV y al generar/publicar asignaciones. No se bloquean login, refresh, membresías, metadatos de institución ni la API comercial por falta de licencia.

Transición: `core.0005` conserva instituciones preexistentes con `licencia_requerida=False`; altas posteriores usan `True`. Una primera orden comercial termina la transición aunque permanezca pendiente. El campo no puede desactivar la política mediante API y el historial impide volver a transición tras vencimiento/revocación. `/acceso/` sigue representando licencias pagadas, no la excepción histórica. La nueva base de presentación usa control estricto desde su creación. Mapeo de rutas, reglas de cupo y límite actual de planteles en [GUIA_DEMO_PAGOS.md](GUIA_DEMO_PAGOS.md).

Respuestas de error existentes `application/problem+json`: `{type,title,status,detail,instance,code,invalid_params?}`. 400 validación/firma inválida; 401 JWT ausente/vencido; 403 rol o institución no autorizada; 404 recurso fuera de ámbito; 409 conflicto de idempotencia/estado; 503 proveedor sin configurar. Listas paginadas DRF `{count,next,previous,results}`.

## Recursos y relaciones

- Plan: catálogo global, nombre, código, funcionalidades JSON, límites de alumnos y planteles.
- Precio: FK plan, modalidad (`monthly`, `annual`, `process`, `institutional`, `perpetual`, `hybrid`, `enterprise`, `maintenance`), importe base, importe por alumno, moneda MXN, vigencia en días y estado activo. Mensual/anual/híbrido/mantenimiento son recurrentes. Precios publicados son inmutables: crear otro precio para cambiar condiciones.
- Contrato: tenant + precio + fechas + condiciones empresariales. Cotización empresarial requiere contrato aprobado por propietario. No implica pago ni acceso.
- Orden: tenant + precio + contrato opcional; snapshot de importe, límites y funcionalidades; cantidad de alumnos; proveedor `DEMO` o `stripe`; clave idempotente por institución; estado y sesión checkout.
- Suscripción: orden inicial, identificador externo, estado, fin de periodo y cancelación programada.
- Licencia: orden, estado, inicio y fin (null para perpetua), funcionalidades y límites comprados. Mantenimiento es una licencia separada.
- Transacción: orden, referencia única de proveedor, importe, moneda, estado. Historial inmutable de confirmaciones.
- Evento webhook: ID único del proveedor, tipo, hash del cuerpo, resultado de procesamiento. No se guardan tarjetas ni payloads con datos personales.
- Comprobante: transacción única, folio UUID interno, fecha. PDF sin validez fiscal.
- Solicitud de factura: orden pagada, RFC, razón social, régimen, código postal, uso CFDI, estado. Integración PAC pendiente; nunca se inventa UUID fiscal.

## Endpoints

| Ruta relativa | Métodos | Acceso / entrada |
|---|---|---|
| `planes/` y `planes/{id}/` | GET; POST/PATCH propietario | catálogo; `{codigo,nombre,funcionalidades,max_alumnos,max_planteles,activo}` |
| `precios/` y `precios/{id}/` | GET; POST propietario | `{plan,modalidad,importe,por_alumno,moneda,dias,activo}` |
| `instituciones/` y `instituciones/{id}/` | GET; POST/PATCH propietario | Tenant existente `{nombre_comercial,plan_suscripcion,estado}` |
| `contratos/` y `contratos/{id}/` | GET; POST/PATCH propietario | `{tenant,precio,inicio,fin,estado,condiciones}` |
| `ordenes/` y `ordenes/{id}/` | GET | propios; propietario global |
| `checkout/` | POST | `{precio:uuid,alumnos:1,contrato?:uuid}`; header `Idempotency-Key` obligatorio. No se permiten importe, moneda ni URL del cliente. Devuelve 201 `{orden,proveedor,url,estado}`. Repetición devuelve la misma orden. |
| `suscripciones/` y `suscripciones/{id}/` | GET | propias |
| `suscripciones/{id}/cancelar/` | POST | `{}`; cancelación al fin del periodo pagado |
| `licencias/` y `licencias/{id}/` | GET | propias |
| `licencias/{id}/revocar/` | POST | propietario; revocación permanente con evento interno auditable |
| `acceso/` | GET | `{activo,funcionalidades,max_alumnos,max_planteles}`; acceso efectivo calculado por fechas y contrato |
| `transacciones/` y `transacciones/{id}/` | GET | propias |
| `comprobantes/` y `comprobantes/{id}/` | GET | propios |
| `comprobantes/{id}/pdf/` | GET | application/pdf; JWT requerido |
| `facturas/` y `facturas/{id}/` | GET/POST; PATCH propietario | `{orden,rfc,razon_social,regimen,codigo_postal,uso_cfdi}` |
| `eventos/` | GET | propietario |
| `ingresos/` | GET | propietario; totales por proveedor/moneda; DEMO separado |
| `demo/confirmar/` | POST | solo propietario y proveedor DEMO; `{orden,resultado:"paid"\|"failed"\|"pending",referencia}`; nunca disponible como confirmación Stripe |
| `webhooks/stripe/` | POST | público; cuerpo crudo y `Stripe-Signature`; firma obligatoria; 200 tras procesamiento durable, reintentos seguros |

## Estados y Vue

Orden: `pending → paid` o `failed`; confirmación tardía válida puede recuperar fallo. Suscripción: `pending`, `active`, `past_due`, `canceled`; `cancel_at_period_end` conserva acceso hasta fin de periodo. Licencia: `active`, `revoked`; expiración efectiva por fecha, contrato y estado de suscripción, sin depender de cron. Contrato: `draft`, `active`, `canceled`; vencimiento efectivo por fecha. Factura: `requested`, `processing`, `rejected`; emisión fiscal reservada para futuro PAC.

Vue obtiene precios del catálogo, envía solamente IDs y cantidad, conserva Idempotency-Key durante reintentos y redirige al `url` HTTPS de Stripe. En DEMO `url=null`: mostrar claramente DEMO; el propietario confirma desde su panel. El retorno del navegador no activa nada: consultar orden y acceso. Descargar PDF con fetch autenticado y Blob. Frontends no deben inferir acceso de un pago pendiente ni almacenar claves Stripe.

## Stripe sandbox

Variables exclusivamente de entorno: `COMMERCIAL_PROVIDER=DEMO|stripe` (DEMO predeterminado), `STRIPE_SECRET_KEY=sk_test_...`, `STRIPE_WEBHOOK_SECRET`, `COMMERCIAL_SUCCESS_URL`, `COMMERCIAL_CANCEL_URL`. Se rechazan claves live y eventos livemode. SDK oficial, sesión idempotente y precios calculados en servidor. Pago único: checkout pagado confirmado; recurrentes: factura pagada y periodo confirmado mediante consulta al proveedor. Renovaciones se deduplican por factura. Reembolsos/disputas y prorrateos requieren flujo posterior y no se ofrecen en esta versión.

Referencias: https://docs.stripe.com/checkout/fulfillment ; https://docs.stripe.com/webhooks/signature ; https://docs.stripe.com/billing/subscriptions/webhooks .
