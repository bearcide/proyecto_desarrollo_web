# ADR 002 — Evolución a API REST y Vue 3

- Estado: arquitectura observada; pendiente de ratificación por el equipo.
- Registro: 13 de noviembre de 2026. Fecha de adopción y responsables de la decisión: por confirmar.
- Antecedente: [ADR 001](../../frontend/documentacion/001-stack-y-arquitectura.md), conservado sin modificaciones.

## Contexto y problema

El ADR 001 adoptó Django, PostgreSQL, Django Templates con Bootstrap y una capa de servicios. También contempló una evolución hacia API REST. La implementación publicada utiliza DRF y Vue 3, mientras conserva archivos de las plantillas anteriores. Este registro establece qué cambió y cómo se distribuyen actualmente las responsabilidades.

## Alternativas documentadas

Django Templates + Bootstrap fue la elección inicial. El ADR 001 registra como alternativas descartadas Node/Express + React, MySQL, lógica concentrada en vistas, MongoDB y Tailwind. No se encontraron actas de una evaluación posterior que expliquen la selección de Vue ni una comparación formal para esta transición; no se atribuyen esas deliberaciones al equipo.

## Implementación adoptada

- **Presentación:** SPA Vue 3, Vue Router, Pinia y Axios. El cliente consume JSON y gestiona navegación y estado.
- **Contrato HTTP:** DRF bajo `/api/v1/`, JWT para autenticación y OpenAPI para describir la API.
- **Aislamiento institucional:** el servicio de identidad valida membresías; `X-Tenant-ID` selecciona una institución autorizada, sin conceder permisos por sí mismo.
- **Dominio académico:** servicios de prerrequisitos, importación y asignación separados de las vistas. El algoritmo greedy registra política y resultados; la publicación determina qué ejecución consulta el alumno.
- **Persistencia:** modelos y ORM Django; `DATABASE_URL` selecciona la base general, SQLite por defecto. La demo usa una configuración SQLite específica; PostgreSQL permanece como opción de despliegue.

## Justificación técnica

La separación existente permite reutilizar reglas desde la API y probar el dominio sin depender del cliente. Las comprobaciones de identidad mantienen el ámbito institucional en el servidor. La política determinista y la información conservada en resultados permiten explicar una asignación. Son propiedades verificables del diseño; las razones históricas de su adopción deben confirmarse con el equipo.

## Consecuencias

Se mantienen entornos Python y Node y un contrato que coordina API e interfaz. URL base, JWT y CORS forman parte de esa integración. Las plantillas antiguas requieren distinguir la interfaz activa al instalar el proyecto. SQLite facilita la demostración, pero no acredita concurrencia productiva. El greedy no garantiza un óptimo global y el dominio aún no contempla periodos, aulas ni ocupación de profesores.

## Evidencia

[Configuración DRF](../../backend/config/settings.py), [rutas](../../backend/config/urls.py), [dependencias Vue](../../frontend/package.json), [router](../../frontend/src/router/index.js), [cliente Axios](../../frontend/src/api/index.js), [identidad](../../backend/apps/core/services/identidad.py), [asignación](../../backend/apps/core/services/asignacion.py) y [pruebas aisladas](../../backend/pruebas_aisladas.py).

## Evolución comercial local

La V2 agrega una aplicación comercial separada y un control de capacidades académicas por licencia. No está publicada en `main` ni se incorpora como decisión formal aprobada en este ADR. Se recomienda registrar posteriormente:

1. Separación entre dominio académico y comercial, roles del propietario SaaS y transición de instituciones anteriores al licenciamiento.
2. Órdenes con snapshot de condiciones, importes calculados por servidor e idempotencia por institución.
3. Adaptadores DEMO/Stripe, activación por eventos verificados, deduplicación y recuperación de fallos.
4. Separación de comprobantes internos y emisión fiscal mediante un futuro proveedor PAC.

La [matriz de implementación](../ESTADO_IMPLEMENTACION.md) documenta evidencia y límites de estas capacidades. El equipo debe confirmar responsables, fecha y estado formal de la evolución respecto del ADR 001.
