# Registro interno de revisión documental

Documento de trazabilidad de preparación; no es un manual del producto ni un entregable técnico principal. El alcance vigente se concentra en el README y en [Estado de implementación](ESTADO_IMPLEMENTACION.md).

## Antecedentes

La revisión inicial encontró ausencia de README en la raíz, un ADR conservado en `frontend/documentacion/001-stack-y-arquitectura.md` y documentación de una interfaz Django anterior. Después se identificó el PDF de secuencia en el worktree V2 y se prepararon una copia íntegra y una versión con cartela del equipo.

El README inicialmente estaba sin seguimiento y no ignorado por Git. Esas comprobaciones describen la preparación anterior a la publicación, no el estado actual. La validación inicial de los cinco CSV aprobó; las referencias a suites pendientes en los informes antiguos corresponden a sus respectivos cortes.

## Publicación anterior

Los siete documentos se publicaron en `bcc49e9856f4f4b6ada9b7525d1baa930ce3c4d7`, rama `origin/docs/readme-adr`. El PR #4 fue integrado en `main` mediante `fe992d2`. El PR #5 incorporó la corrección de CI mediante `1b8ddf2`: npm se ejecuta en `frontend/`, con `npm ci` y su lockfile. Por tanto, README y PDFs ya forman parte de la versión publicada.

El worktree documental anterior conserva una modificación pendiente del diagnóstico y su seguimiento a `origin/docs/readme-adr`. No se alteró esa modificación. Esta revisión trabaja en otro worktree, `proyecto_desarrollo_web_docs_limpio`, rama `docs/limpieza-entrega`, creada desde `origin/main` en `1b8ddf2`.

## Auditoría actual

Se inspeccionaron código y cambios sin commit de V2 (`feature/fase2-ia`, HEAD `e61e3b7`), incluidos modelos, servicios, rutas, componentes, contrato comercial y pruebas. La aplicación comercial y sus paneles todavía no están en `main`. Se detectaron fallbacks offline, simulaciones en memoria y diferencias entre el cotizador visual y el importe aceptado por servidor; se documentan en la matriz de implementación.

Se ejecutaron en copias temporales 62 pruebas Django y 12 Vue de main, y 95 Django y 88 Vue de V2: todas aprobaron. Los settings aislados usan SQLite en memoria; Stripe se simuló. No se cargaron archivos `.env` ni se operó sobre las bases existentes. No se ejecutó una nueva instalación de dependencias, build, navegación gráfica, integración HTTP académica completa ni Stripe externo.

La edición elimina repeticiones de integrantes en registros auxiliares, separa el estado local del publicado y conserva el ADR inicial y los dos PDF. La evidencia comercial detallada y los comandos locales se centralizan en `ESTADO_IMPLEMENTACION.md`. No se añadieron capturas: la imagen hallada solo en V2 no se utilizó como evidencia de la interfaz publicada.

## Validaciones documentales

Validación actual de los cinco CSV aprobada. Comprobación de enlaces relativos, encabezados y bloques de código; contraste de comandos con scripts, argumentos, configuración y scripts npm; consistencia de módulos con rutas/modelos; comparación del ADR original y los dos PDF contra el commit base; `git diff --check` y control de que el diff incluya únicamente Markdown.

Esta propuesta queda para revisión sin commit, push ni merge. No modifica backend, frontend, bases, CI, integración Stripe ni archivos de otros agentes.

## Pendientes

Completar las dos matrículas faltantes; ratificar el ADR 002 con fechas/responsables históricos; registrar decisiones comerciales en ADR independientes cuando se formalicen. La validación comercial externa y los requisitos productivos se enumeran en la matriz de implementación, sin presentarlos como funcionalidades concluidas.
