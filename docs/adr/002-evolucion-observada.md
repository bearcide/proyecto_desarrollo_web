# ADR 002 — Evolución observada a DRF y Vue 3

- Estado: **reconstrucción técnica pendiente de validación por el equipo**.
- Fecha del registro documental: 2026-11-13. Fecha de adopción: **pendiente de confirmar**.
- Autores de la decisión: **pendiente de confirmar por el equipo**.
- Antecedente: [ADR 001 original](../../frontend/documentacion/001-stack-y-arquitectura.md).

## Contexto

El ADR 001 adoptó Django, PostgreSQL, plantillas HTML con Bootstrap y una capa de servicios. Anticipó una posible API REST. El código actual contiene una API DRF y una SPA Vue 3; también conserva archivos de la interfaz Django anterior. Este registro describe hechos comprobables, sin modificar la decisión original.

## Problema arquitectónico

Documentar cómo se distribuyen hoy presentación, autenticación, aislamiento institucional, reglas académicas y persistencia, y explicar la diferencia entre la propuesta inicial y el sistema entregado. No se dispone de actas que documenten el motivo histórico del cambio a Vue.

## Alternativas con evidencia

La alternativa Django Templates + Bootstrap está documentada como decisión inicial en el ADR 001. Ese documento también enumera Node/Express + React, MySQL, lógica en vistas, MongoDB y Tailwind como alternativas descartadas en aquel momento. No hay evidencia consultada que permita afirmar que se reconsideraron para la evolución actual ni que Vue fuera elegido mediante una comparación formal.

## Decisión observada

1. Exponer una API JSON versionada mediante DRF, autenticada con JWT y documentada con OpenAPI.
2. Implementar el cliente activo como SPA Vue 3 con Vue Router, Pinia y Axios.
3. Mantener servicios de dominio para identidad, prerrequisitos, importación y asignación, apoyados por modelos y ORM Django.
4. Resolver el contexto de escuela mediante membresías y permisos; el encabezado `X-Tenant-ID` selecciona contexto, no concede acceso.
5. Seleccionar persistencia general con `DATABASE_URL` (SQLite por defecto); utilizar una configuración SQLite separada para la demo local. PostgreSQL sigue disponible mediante driver y Compose.
6. Generar propuestas con un algoritmo greedy determinista, registrar política/resultados y publicar una ejecución por escuela.

## Justificación comprobable y límites de interpretación

Las rutas y configuración acreditan el contrato API; los módulos Vue y el cliente Axios acreditan un consumidor separado. Los servicios permiten reutilizar las reglas desde las vistas y someterlas a pruebas aisladas. Las comprobaciones de membresía restringen el contexto institucional. El inicializador demo rechaza archivos existentes para evitar reutilizar bases. La política explícita del algoritmo permite explicar sus resultados.

Estos son efectos y mecanismos observables del diseño. No se afirma que fueran las razones expresadas por el equipo al decidir, ni se atribuyen mejoras de rendimiento sin mediciones.

## Consecuencias

- Se mantienen dos entornos de desarrollo: Python/Django y Node/Vite; deben coordinarse URL base, CORS y contrato JSON.
- La SPA gestiona tokens; el servidor debe validar identidad y membresía en cada operación protegida.
- La coexistencia de plantillas antiguas puede confundir la puesta en marcha; el README identifica Vite como cliente activo.
- La configuración de demo facilita pruebas locales, pero no demuestra concurrencia o capacidad productiva con PostgreSQL.
- El greedy es reproducible y explicable, pero no garantiza el mejor horario global; carece de periodos y restricciones de aulas/profesores.
- El documento inicial queda como antecedente histórico; la adopción formal de esta evolución requiere validación del equipo.

## Evidencia del repositorio

- [Configuración DRF, JWT y base de datos](../../backend/config/settings.py) y [rutas principales](../../backend/config/urls.py).
- [Dependencias Vue](../../frontend/package.json), [router](../../frontend/src/router/index.js) y [cliente API](../../frontend/src/api/index.js).
- [Servicio de identidad](../../backend/apps/core/services/identidad.py) y [documentación de membresías](../../backend/docs/identidad_multi_tenant.md).
- [Motor de asignación](../../backend/apps/core/services/asignacion.py), [importación](../../backend/apps/core/services/importacion_csv.py) y [pruebas aisladas](../../backend/pruebas_aisladas.py).
- [Configuración demo](../../backend/config/settings_demo.py), [inicializador](../../backend/apps/core/management/commands/inicializar_demo.py) y [Compose](../../docker-compose.yml).

## Validación pendiente

El equipo debe confirmar responsables, fecha de adopción y razones históricas de la evolución; resolver el estado formal respecto del ADR 001 y aprobar o corregir esta reconstrucción. No se cambia el estado histórico «Aceptado» del original.

## Integrantes oficiales actuales

| Integrante | Matrícula |
|---|---|
| Cristian Michael Aguilar Chávez | 318039026 |
| Cecilia Sayuri Hernández Martínez | 320313503 |
| Emilio García Riba | PENDIENTE |
| Violeta Camacho Ignacio | PENDIENTE |

Identificación confirmada por el equipo; no atribuye autoría histórica de decisiones ni modifica el ADR 001.
