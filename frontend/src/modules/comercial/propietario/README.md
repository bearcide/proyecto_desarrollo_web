# Panel Comercial del Propietario SaaS — InscripcionMadeEasy

Modulo independiente para la administración de la comercialización del SaaS por parte
del propietario (organización que factura a las escuelas). No confunde con el panel
administrativo escolar (`/admin`), que gestiona alumnos, materias, grupos y horarios.

## Fases

| Fase | Alcance | Estado |
|---|---|---|
| 0 | Auditoría, separación de responsabilidades y creación del módulo | Completa |
| 1 | Dashboard comercial: indicadores de instituciones, suscripciones, licencias, ingresos, pagos, contratos, renovaciones | Completa (frontend) |
| 2 | Gestión de clientes: listado, búsqueda, filtros, detalles, contrato vigente, plan, historial | Completa (frontend) |
| 3 | Gestión de planes: precios, periodicidad, límites, planteles, módulos, disponibilidad | Completa (frontend) |
| 4 | Suscripciones, contratos, licencias, renovaciones, cancelaciones, vencimientos, estados | Frontend de lectura/listado completo; acciones de cancelación (`POST /suscripciones/{id}/cancelar/`) y revocación (`POST /licencias/{id}/revocar/`) implementadas con confirmación, estados y manejo de errores |
| 5 | Transacciones y facturación: historial, filtros, estados, comprobantes, solicitudes | Frontend de lectura/listado completo; solicitudes y descarga de comprobantes integradas |
| 6 | Integración con `docs/CONTRATO_COMERCIAL_API.md` | Alineado al contrato publicado; checkout/redirección de pago y flujo DEMO pendientes de UI propietaria |

## Estructura

```
frontend/src/modules/comercial/propietario/
├── README.md
├── services/            # API facade + normalizadores (capa de acceso a datos)
├── composables/         # Estado y orquestación de datos por dominio
├── views/               # Vistas del panel propietario
└── *.test.js            # Pruebas unitarias de los servicios normalizados
```

## Contrato y endpoints

- Base de recursos: `/api/v1/comercial/` (misma base que el módulo comercial de cliente).
- Recursos consumidos a través de `services/apiComercial.js` y de la fachada compartida
  `modules/comercial/cliente/api/comercialService.js` (catálogos, suscripciones, licencias,
  transacciones, comprobantes y solicitudes de factura).
- Indicadores y listado de instituciones propietario: rutas provisionales marcadas en
  `RUTAS_COMERCIALES` (`/comercial/propietario/...`). **No usar en integración productiva**
  hasta que Codex publique `docs/CONTRATO_COMERCIAL_API.md` y las sustituya.

## Responsabilidades

Este módulo **no** debe modificar:

- Router global (`frontend/src/router/index.js`).
- Layouts compartidos (`frontend/src/layouts/`).
- Estilos globales (`frontend/src/infrastructure/static/css/main.css`).
- Componentes compartidos (`frontend/src/components/`).
- Backend, modelos y migraciones.
- El panel administrativo escolar (`frontend/src/modules/admin/`) y la experiencia de
  cliente comercial (`frontend/src/modules/comercial/cliente/`).

Antigravity (frontend) será responsable de integrar las rutas del panel comercial en la
navegación principal y de registrar los permisos requeridos.

## Reglas del producto aplicadas en el frontend

- No se generan comprobantes fiscales (CFDI) ni se simulan pagos: la descarga de
  comprobantes responde únicamente el recurso que el backend ya haya emitido.
- No se almacenan secretos ni se registran pagos reales.
- Las cifras mostradas provienen de indicadores y catálogos del backend; los normalizadores
  nunca rellenan valores ausentes.

## Estado final verificado

- Suite de pruebas del módulo (`vitest`): 46 pruebas en 6 archivos, todos en verde.
- Compilación de producción (`vite build`): sin errores.
- Alineación verificada contra `docs/CONTRATO_COMERCIAL_API.md` y el backend
  (`backend/apps/comercial/`): estados (`ACTIVE`, `PAID`, `FAILED`, `PENDING`, `CANCELED`,
  `PAST_DUE`, `REVOKED`, `REQUESTED`, `PROCESSING`, `REJECTED`), periodicidades, límites,
  vigencias y moneda MXN.
- El módulo no registra rutas: la integración en el router y navegación es responsabilidad
  de Antigravity.
