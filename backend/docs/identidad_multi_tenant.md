# Identidad y autorización: Fase 2

La API autentica con JWT. Los permisos proceden exclusivamente de MembresiaTenant;
is_staff e is_superuser no conceden acceso escolar en la API.

## Contexto

Cada petición académica verifica usuario activo, membresía activa y escuela ACTIVO.
Una sola membresía se selecciona automáticamente; con varias se exige X-Tenant-ID.
Un header ajeno nunca activa fallback. La resolución se comparte entre permisos,
querysets y serializadores dentro de la petición y se renueva en la siguiente.

- GET /api/v1/membresias/me/: lista sin paginación de membresías propias, incluidas
  inactivas o escuelas no disponibles, para descubrimiento. Solo exige autenticación.
- GET /api/v1/alumnos/me/: perfil académico individual de solo lectura, resuelto
  mediante user + tenant. No interpreta el identificador JWT como Alumno.id.

AlumnoPerfilSerializer enumera los campos; excluye domicilio, edad, usuario y
atributos de autenticación. El mismo perfil se usa para lectura de alumnos por
usuarios sin capacidad administrativa. Alumno solo lee su expediente y los
catálogos de su escuela. Administrador gestiona recursos de su escuela; no puede
editar membresías, estado de escuela o suscripción por los endpoints académicos.
Una persona con ambas capacidades puede administrar y consultar su propio perfil.
La ruta me requiere capacidad de alumno y un único perfil activo incluso para
administradores. Los perfiles duplicados responden 409; no se fusionan.

Todos los detalles ajenos responden 404. Las relaciones FK y los IDs de materias
aprobadas se validan contra la escuela seleccionada. Se rechazan campos no
editables o desconocidos, incluido tenant en escrituras. No hay endpoints públicos
para asignar roles. Las rutas no implementadas conservan 405.

## Errores

Content-Type: application/problem+json. Campos: type (URN estable), title, status,
detail, instance (ruta sin query sensible), code. Las validaciones incorporan
invalid_params: [{name, reason}]. Se conservan WWW-Authenticate, Allow y Retry-After.
Los errores internos no exponen trazas. Códigos de identidad: invalid_tenant (400),
tenant_required (400), tenant_access_denied (403), tenant_unavailable (403),
permission_denied (403), alumno_inactive (403), alumno_not_found (404),
ambiguous_alumno_identity (409). Los fallos JWT usan authentication_failed (401).

## Aprovisionamiento operativo

El comando aprovisionar_admin_escolar requiere --user-id, --tenant-id y
--referencia. --simular no escribe. Una membresía inactiva exige --reactivar.
El comando no crea usuarios, no cambia credenciales, is_staff, is_superuser ni
expedientes, y preserva es_alumno. Solo acepta usuario y escuela activos.

Emite JSON en stdout y, tras confirmar la transacción, al logger apps.core.auditoria:
operador del sistema, referencia, IDs, simulación y estado antes/después. La
retención y control de acceso del log corresponden a la operación del entorno;
no es una tabla de auditoría inmutable ni valida por sí sola la aprobación externa.

## Verificación aislada

Desde la raíz: backend/venv/bin/python -B backend/pruebas_aisladas.py

El runner reemplaza DATABASES antes de django.setup, permite únicamente SQLite
en memoria y rechaza conexiones SQLite a disco. Ejecuta makemigrations --check
--dry-run y la suite core completa. No usar manage.py test contra la configuración
local para reproducir este aislamiento. No se han aplicado migraciones a bases
existentes. El frontend anterior requiere adaptación en una fase posterior.
