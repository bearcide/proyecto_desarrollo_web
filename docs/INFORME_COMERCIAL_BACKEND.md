# Implementación comercial B2B — V2

## Diagnóstico de recuperación

Rama verificada: `feature/fase2-ia`. Al inicio no existían modificaciones versionadas. Se preservaron cinco archivos sin seguimiento: captura_swagger_classroom.png, scripts/Presentación.pdf, scripts/abrir_3_agentes.bash, scripts/diagrama_flujo_api.pdf y scripts/iniciar_demo.bash. No se encontraron instrucciones AGENTS.md en el árbol consultado. Los 54 archivos Python originales de apps/config pasaron análisis AST sin errores; esto verifica sintaxis, no constituye un análisis físico del almacenamiento. No se detectaron archivos Python truncados ni inconsistencias de migración.

Durante el desarrollo aparecieron cambios concurrentes en `frontend/src/components/AppIcon.vue` y `frontend/src/modules/comercial/`. No fueron editados por esta implementación. No se tocaron V1, servidores activos, bases existentes, commits ni remotos.

El sandbox de comandos falló con `bwrap: loopback: Failed RTM_NEWADDR`; los comandos necesarios se ejecutaron mediante solicitudes de autorización. La aplicación comercial usa el entorno virtual existente `backend/venv`; se instaló el SDK oficial Stripe 14.4.2 con sus dependencias.

## Entregado

- Contrato de coordinación: `docs/CONTRATO_COMERCIAL_API.md`.
- Aplicación separada `backend/apps/comercial`: catálogo, precios inmutables, contratos institucionales, órdenes con snapshot, suscripciones, licencias, transacciones, eventos webhook, comprobantes y solicitudes fiscales.
- Integración con Tenant y membresías existentes. Superusuario SaaS separado de staff y administradores escolares. Consultas de recursos restringidas por institución.
- Checkout único/recurrente con precio calculado en servidor, MXN/Decimal, clave idempotente por institución y orden persistida antes de contactar Stripe. Los timeouts reutilizan el identificador del proveedor.
- DEMO explícito predeterminado. Solo el propietario puede confirmar transacciones DEMO. Stripe rechaza claves live, eventos live, firmas inválidas y confirmaciones con importes incompatibles.
- Webhook usa cuerpo crudo, verificación oficial de firma, recuperación de objetos del proveedor, hash y deduplicación de evento; transacciones deduplicadas por referencia externa. Efectos locales atómicos. Fallos de procesamiento revierten cambios y permiten reintento. Los eventos fallidos no se conservan como registros procesados: se reintentan desde Stripe.
- Renovación desde `invoice.paid`, periodo tomado de la factura pagada; pagos pendientes no activan, facturas marcadas manualmente como pagadas no activan. Suscripciones cancelables al fin del periodo. Revocación permanente de licencia por propietario.
- `acceso()` calcula vigencia efectiva y funcionalidades, con límites combinados por máximo, no sumados. En el cierre V2 se integró `exigir_capacidad()` con los endpoints académicos y escrituras CSV/REST; existe transición explícita para instituciones anteriores. Ver [GUIA_DEMO_PAGOS.md](GUIA_DEMO_PAGOS.md) para reglas y evidencia actual: 95 pruebas Django y 87 Vue aprobadas. Las cifras de las secciones siguientes corresponden al informe inicial.
- Comprobantes PDF internos con folio propio y leyenda SIN VALIDEZ FISCAL. Solicitudes de factura y puerto abstracto para PAC; sin timbres ni UUID fiscales ficticios.
- Migración `backend/apps/comercial/migrations/0001_initial.py` preparada, validada mediante test runner en SQLite en memoria. Sin aplicación a la base de demostración.
- API OpenAPI incorporada al esquema existente; CORS permite `Idempotency-Key`.

## Verificación

Suite completa: **80 pruebas aprobadas**, incluidas las existentes de identidad, membresías, inscripciones, horarios y demo. La suite comercial cubre compras, modalidades, renovaciones, cancelaciones, pago pendiente/fallido, firmas inválidas, duplicación de eventos/transacciones, manipulación de importes, timeout, permisos, aislamiento, contratos vencidos, comprobantes, solicitudes fiscales y límites.

Comando reproducible, desde la raíz:

```bash
backend/venv/bin/python backend/manage.py test apps.comercial apps.core.tests --settings=apps.core.tests.settings_aislados --noinput
backend/venv/bin/python backend/manage.py makemigrations --check --dry-run --settings=apps.core.tests.settings_aislados
backend/venv/bin/python backend/manage.py spectacular --settings=apps.core.tests.settings_aislados --file /tmp/comercial-openapi.yaml --validate
```

`manage.py check` sin incidencias; migraciones sin cambios pendientes; `git diff --check` sin errores. OpenAPI se genera y valida sin errores. Tras los ajustes finales se repitieron las 18 pruebas comerciales y pasaron. Las llamadas de Stripe se simulan en pruebas; la firma webhook se verifica con el SDK real. No se hicieron cobros ni llamadas autenticadas a una cuenta Stripe.

## Configuración y operación

Variables documentadas en `backend/.env.example`; no contienen secretos. Para DEMO no se necesitan credenciales. El propietario crea plan y precio desde la API, selecciona institución con `X-Tenant-ID`, abre checkout y confirma mediante `/demo/confirmar/`. Para Stripe configurar `COMMERCIAL_PROVIDER=stripe`, `STRIPE_SECRET_KEY` de prueba y `STRIPE_WEBHOOK_SECRET`, además de URLs de retorno del frontend.

Registrar el webhook `/api/v1/comercial/webhooks/stripe/` para `checkout.session.completed`, `checkout.session.async_payment_succeeded`, `checkout.session.async_payment_failed`, `invoice.paid`, `invoice.payment_failed`, `customer.subscription.updated` y `customer.subscription.deleted`. La confirmación nunca depende de la URL de éxito. No exponer el webhook con credenciales live.

La aplicación necesita migraciones antes de usarse con una base persistente. **Aplicarlas a la base actual requiere autorización del usuario y no se ha hecho.** Las pruebas no necesitan esa autorización porque su base es desechable.

## Límites y siguientes integraciones

- Pendiente prueba extremo a extremo con una cuenta Stripe sandbox y su webhook real; requiere credenciales externas. Pruebas de concurrencia bajo PostgreSQL también quedan pendientes: SQLite en memoria no reproduce bloqueos reales de producción.
- El modelo híbrido cobra base más alumnos declarados por la institución al contratar; conserva cantidad y precio. No mide consumo variable, cambios de cantidad ni prorrateos posteriores.
- Contratos empresariales utilizan precio dedicado aprobado por el propietario y condiciones textuales. No hay negociación ni firma electrónica.
- Los límites de planteles y funcionalidades están representados y disponibles por servicio/API; no se crea un nuevo dominio académico de planteles ni se altera el existente.
- Mantenimiento tiene modalidad recurrente independiente. No prolonga automáticamente la licencia perpetua ni es requisito para conservarla.
- Reembolsos, disputas, contracargos, conciliación bancaria, impuestos automáticos, cupones, cambio de plan y cobros por consumo requieren flujos adicionales. No están expuestos como operaciones en esta versión.
- Integración PAC CFDI 4.0 y validación fiscal de catálogos SAT requieren proveedor autorizado; las validaciones locales de solicitudes son solo de formato.
- No existe tarea automática de reconciliación ni retención/alertas de webhooks. Stripe debe reintentar eventos fallidos; la vigencia efectiva no depende de cron.
