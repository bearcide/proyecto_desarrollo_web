# Verificación del MVP local

Base nueva: `/home/crismi/Escritorio/proyecto_CeciyEmilio/proyecto_desarrollo_web/backend/demo_backend_20261105.sqlite3`.
La creación verificó ruta absoluta y ausencia antes de `O_EXCL`. Se aplicaron
0001–0004 únicamente a esa base nueva y a SQLite en memoria para pruebas.
La ruta alternativa demo_local_20261105.sqlite3 estaba ocupada: fue rechazada.

Fixture: 100 alumnos, 2 planes, 12 materias, 24 grupos, 400 solicitudes.
Pruebas finales: 62 aprobadas, incluidos snapshots auditables; repetir con
`backend/venv/bin/python -B backend/pruebas_aisladas.py`.

HTTP real: WSGI local en puerto efímero 127.0.0.1, detenido al terminar:
- token administrador y alumno: 200
- descubrimiento de membresías, estadísticas, grupos, validar CSV: 200
- generar: 201; 100 alumnos, 307 asignadas, 93 pendientes
- resultados administrativos: 200, 400 filas persistidas
- horario alumno sin publicación: 404
- intento alumno de consultar ejecución administrativa: 403
- publicar: 200
- horario propio publicado: 200, 4 resultados de D001
- CSV administrativo: 200, 24113 bytes

La base queda con ejecución 1 publicada para demostración inmediata. Se puede
generar otra propuesta y publicarla desde Vue; la anterior quedará archivada.
El inicializador no publica por sí mismo.

Limitaciones: algoritmo greedy determinista sin óptimo global; una propuesta
vigente por escuela y sin periodos; sin ocupación de profesores ni aulas;
SQLite para operación secuencial local. Importaciones añaden/actualizan, nunca
eliminan; prerrequisitos existentes no se retiran. Validar ejecuta la importación
en una transacción que se revierte; confirmar revalida y confirma toda la transacción.
La auditoría de prioridades/oferta se guarda en politica; resultados guardan snapshots.
Ningún servicio externo ni API de IA interviene. No se modificó frontend,
demo_data/ ni scripts/demo/ por parte del backend.

Verificación final: huellas de ambas bases originales y migraciones0001–0003 intactas.
Reinicializar la base demo existente fue rechazado y su huella no cambió.
