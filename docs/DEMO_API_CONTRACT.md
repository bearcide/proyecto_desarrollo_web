# InscripcionMadeEasy — contrato local de demo (2026-11-04)

Contrato compartido para Antigravity (Vue) y OpenCode (CSV/QA). Base URL:
http://127.0.0.1:8000/api/v1/. No hay servicios externos. JSON UTF-8.
Todas las rutas terminan en /. IDs académicos enteros, tenant UUID.

## Sesión y permisos

POST token/ {"matricula":"demo_admin","password":"DemoLocal2026!"}
→ 200 {"access":"JWT","refresh":"JWT"}. matricula es el username del usuario,
incluido el administrador; no se infiere Alumno.id del claim user_id.
POST token/refresh/ {"refresh":"JWT"} → 200 {"access":"JWT"}.
Enviar Authorization: Bearer ACCESS. GET membresias/me/ → 200 lista:
[{"tenant":"UUID","nombre_escuela":"Demo","estado_escuela":"ACTIVO",
"activo":true,"es_alumno":false,"es_administrador":true}].
Enviar X-Tenant-ID: UUID; obligatorio si hay varias membresías activas.
GET alumnos/me/ → 200 objeto: id, tenant, plan_estudios, numero_de_cuenta,
nombre, apellido_paterno, apellido_materno, semestre, materias_pasadas,
materias_cursadas, creditos, promedio_acumulado, indicador_escolar,
materias_aprobadas_ids, numero_inscripcion, ventana_inicio, ventana_texto.
Solo alumno propio; administrador sin perfil recibe 403.
GET alumnos/ (admin: escuela; alumno: solo propio) → paginación DRF:
{"count":100,"next":null,"previous":null,"results":[...]}.
GET planes-estudios/, nodos/, estadisticas-nodos/, prerrequisitos/, tenants/
conservan paginación existente. Escrituras de catálogos solo administrador.

## Importación (solo administrador)

POST demo/importaciones/validar/ y POST demo/importaciones/confirmar/
comparten cuerpo {"archivos":{"planes":"CSV completo","materias":"CSV completo",
"alumnos":"CSV completo","grupos":"CSV completo","solicitudes":"CSV completo"}}.
Los cinco archivos son opcionales individualmente; al menos uno requerido.
No usar multipart. CSV con encabezado, coma, comillas estándar, UTF-8/BOM opcional.
Límite: 2 MB de texto total y 10000 filas por archivo.

Encabezados exactos (orden libre):
- planes: nombre,descripcion
- materias: plan,clave,nombre,creditos,semestre,prerrequisitos
- alumnos: matricula,nombre,apellido_paterno,apellido_materno,plan,aprobadas,password
- grupos: materia,clave,profesor,cupo,horarios
- solicitudes: matricula,materia,preferencia,prioridad_institucional

plan refiere al nombre único de plan en la escuela; materia refiere a clave.
prerrequisitos y aprobadas: claves separadas por ; (vacío permitido).
horarios: Lunes:08:00-10:00;Miercoles:10:00-12:00 (sin espacios; se aceptan
Miércoles y Sábado). Días Lunes..Domingo; intervalos de minutos, fin > inicio.
Un grupo puede tener varios bloques; no pueden solaparse entre sí.
cupo entero >= 0; preferencia entero >= 1; prioridad_institucional entero >= 0.
Menor prioridad_institucional va primero; empate por matrícula lexicográfica.
Todas las solicitudes de un alumno deben tener la misma prioridad institucional.
preferencia ordena materias de ese alumno; empate por clave. Grupos por clave.
La prioridad es explícita en CSV, sin IA ni datos de CV.

Validar → 200 {"valido":true,"filas":{"planes":2,...},"errores":[]}.
CSV inválido → 400 mismo informe, errores [{"archivo":"alumnos","fila":2,
"campo":"plan","mensaje":"..."}], dentro de Problem Details (extension errores).
Confirmar revalida dentro de una transacción; éxito → 200 mismo informe y
"importado":true. Ningún error deja escrituras parciales.
Claves naturales permiten repetición sin duplicados (upsert). No elimina filas.
No resetea contraseñas de usuarios existentes. Para altas, password obligatorio.
No vincula un username existente ajeno ni deduce roles administrativos.
Importar alumnos crea usuario y membresía de alumno únicamente.
No se pueden cambiar plan, aprobadas o grupo de registros usados alterando
resultados guardados: los resultados incluyen snapshot de grupo y horario.
Materias existentes conservan prerrequisitos; CSV añade aristas válidas.

## Asignación y publicación (solo administrador salvo horario/me)

GET demo/grupos/ → 200 lista [{"id":1,"materia":1,"clave":"G1",
"profesor":"Profesor ficticio","cupo":20,"horarios":[{"dia":"Lunes","inicio":480,"fin":600}]}].
Los horarios de grupos/resultados usan MINUTOS desde medianoche, no horas.
GET demo/estadisticas/ → 200 {"alumnos":100,"planes":2,"materias":12,
"grupos":24,"solicitudes":400,"ejecuciones":1,"publicacion_id":1 o null}.
POST demo/asignaciones/generar/ cuerpo {} → 201 {"id":1,"estado":"BORRADOR",
"resumen":{"alumnos":100,"asignadas":350,"pendientes":50},"politica":{...}}.
Cada ejecución reemplaza lógicamente la propuesta: no consume cupos de ejecuciones
anteriores. No representa reservas adicionales. Motor greedy determinista,
sin promesa de óptimo global; registra resultado por solicitud incluso pendiente.
GET demo/asignaciones/ → 200 lista de ejecuciones, más recientes primero.
GET demo/asignaciones/{id}/ → 200 ejecución + "resultados": [{"alumno":1,
"matricula":"A001","materia":1,"clave_materia":"MAT1","grupo":1 o null,
"estado":"ASIGNADA" o "PENDIENTE","motivo":"" o código,
"detalle":{... snapshot de materia/grupo/profesor/horarios ...}}].
Motivos: YA_APROBADA, PRERREQUISITOS, PLAN_INCORRECTO, SIN_GRUPO,
SIN_CUPO, CONFLICTO_HORARIO. No se consideran aprobadas materias asignadas
simultáneamente. Cupos y choques se validan en toda la ejecución por alumno.
POST demo/asignaciones/{id}/publicar/ {} → 200 ejecución PUBLICADO.
Solo una publicación vigente por escuela; anteriores quedan ARCHIVADO.
GET demo/asignaciones/{id}/csv/ → 200 text/csv; admin, incluidos borradores.
Encabezado: matricula,materia,grupo,estado,motivo,profesor,horarios.
GET demo/horario/me/ → 200 {"ejecucion":1,"resultados":[solo propios]}.
Sin publicación → 404. Alumno no puede leer listados ni detalle de ejecuciones,
ni CSV administrativo, incluso publicados. Horario incluye pendientes propios.

## Errores

application/problem+json: {"type":"urn:inscripcionmadeeasy:problem:...",
"title":"...","status":400,"detail":"...","instance":"/api/v1/.../",
"code":"validation_error","invalid_params":[{"name":"campo","reason":"..."}]}.
401 sin JWT/vencido; 403 rol insuficiente, membresía inactiva o escuela no activa;
400 header inválido, falta selección múltiple o entrada inválida; 404 registro
fuera de escuela, perfil ausente o publicación inexistente; 409 identidad ambigua;
405 método no permitido. Errores CSV añaden errores por fila; no simular éxitos.

## Inicialización local (backend)

Se proporcionará config.settings_demo y comando inicializar_demo. La ruta será
backend/demo_backend_20261105.sqlite3 (absoluta verificada antes de crearla).
No usar backend/db.sqlite3 ni la SQLite raíz. Las credenciales son ficticias y
exclusivas de demo. El comando crea escuela y administrador; CSV lo prepara
OpenCode conforme a este documento. Frontend y scripts externos no son editados
por el agente backend.


## Comandos exactos y credenciales ficticias

Desde la raíz del repositorio, para una base NUEVA:

```bash
backend/venv/bin/python -B backend/manage.py inicializar_demo --settings=config.settings_demo --con-datos
```

El inicializador se niega a tocar una ruta existente (creación O_EXCL). Para crear
otra demo independiente se puede definir IME_DEMO_DATABASE con una ruta absoluta
nueva dentro de backend/, nombre demo_*.sqlite3. Mantener esa variable también
al levantar el servidor. No borrar ni reinicializar bases existentes.

La base preparada por el agente backend es backend/demo_backend_20261105.sqlite3.
La ruta demo_local_20261105.sqlite3 estaba ocupada y se preservó.

```bash
backend/venv/bin/python -B backend/manage.py runserver 127.0.0.1:8000 --settings=config.settings_demo --noreload
```

Administrador: demo_admin / DemoLocal2026!
Alumno: D001 / DemoLocal2026! (también D002..D100).
Obtener tenant mediante GET membresias/me/. Autenticar administrador con campo
matricula=demo_admin. Las cuentas y contraseñas son públicas, solo para demo local.
El inicializador carga 100 alumnos, 2 planes, 12 materias, 24 grupos y 400 solicitudes.
No publica automáticamente: demostrar generar → revisar → publicar → horario alumno.
No hay llamadas externas, servicios IA ni dependencias nuevas.

Pruebas aisladas:

```bash
backend/venv/bin/python -B backend/pruebas_aisladas.py
```

Limitaciones deliberadas: greedy no óptimo global; sin periodos académicos ni
reservas acumuladas entre ejecuciones; CSV solo JSON con texto (no multipart);
profesor como texto, sin validación de choques entre profesores; SQLite serializa
escrituras y la demo se opera secuencialmente. Las materias del frontend heredado
siguen teniendo horarios en horas: no confundirlos con los minutos de demo/grupos/.
Para el horario final usar demo/horario/me/ y sus snapshots. No hay endpoints de
edición de asignaciones ni eliminación de datos importados.
