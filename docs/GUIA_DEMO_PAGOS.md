# Demostración integral de pagos SaaS

Validación local del 12 de noviembre de 2026, rama `feature/fase2-ia`, HEAD `e61e3b7` con cambios sin commit. No se modificó frontend, no se hicieron commits/push, pagos reales ni llamadas a Stripe. No se detuvieron servidores. Los comandos siguientes parten de la raíz del repositorio.

## Cierre de integración V2: demostración visual

**Usar la base nueva `backend/demo_pagos_presentacion_v2_20261112.sqlite3`.** Ya está creada con 24 migraciones, datos académicos ficticios y sin órdenes/pagos. Los archivos de la primera fase conservan su estado anterior y no tienen la migración nueva; no apuntar el servidor V2 a ellos sin preparar una migración aislada. Django y Vue adicionales quedaron levantados en `127.0.0.1:8011` y `127.0.0.1:5174`. No se sustituyó ningún servidor existente.

Para volver a levantarlos cuando esos puertos estén libres, terminal 1 desde la raíz:

```bash
export PAGOS_DEMO_DATABASE="$PWD/backend/demo_pagos_presentacion_v2_20261112.sqlite3"
PAGOS_DEMO_DATABASE="$PAGOS_DEMO_DATABASE" backend/venv/bin/python backend/manage.py check --settings=config.settings_pagos_demo
PAGOS_DEMO_DATABASE="$PAGOS_DEMO_DATABASE" backend/venv/bin/python backend/manage.py migrate --check --settings=config.settings_pagos_demo
PAGOS_DEMO_DATABASE="$PAGOS_DEMO_DATABASE" backend/venv/bin/python backend/manage.py runserver 127.0.0.1:8011 --noreload --settings=config.settings_pagos_demo
```

Terminal 2 desde la raíz:

```bash
cd frontend
VITE_DEMO_MODE=commercial VITE_API_BASE_URL=http://127.0.0.1:8011/api/v1 npm run dev -- --host 127.0.0.1 --port 5174 --strictPort
```

No lanzar una segunda copia si ya están escuchando. Si hay que usar otros puertos, cambiar también la URL API de Vite; para otro puerto de Vue será necesario autorizar su origen en la configuración demo. `--strictPort` evita que Vite cambie el puerto silenciosamente. La API absoluta en `VITE_API_BASE_URL` es necesaria: no hay proxy Vite. La configuración demo admite CORS para 5173 y 5174, ignora `DATABASE_URL`, exige ruta existente absoluta `backend/demo_pagos_*.sqlite3`, fuerza DEMO y vacía las claves Stripe. Su firma JWT es distinta de la demo académica.

Abrir **dos perfiles de navegador separados** (por ejemplo normal e incógnito). Dos pestañas del mismo perfil comparten localStorage y cambiarían la identidad de ambas.

| Usuario | Contraseña ficticia | Entrada Vue |
|---|---|---|
| `admin_demo` | `Demo-Pagos-2026!` | `http://127.0.0.1:5174/login`, luego `/admin/comercial/planes` |
| `propietario_demo` | `Demo-Pagos-2026!` | mismo login, luego `/comercial/propietario/dashboard` |
| `admin_otro_demo` | `Demo-Pagos-2026!` | institución Alterna, para comprobar aislamiento |
| `staff_demo` | `Demo-Pagos-2026!` | administrador escolar/staff, sin autoridad SaaS |
| `alumno_pagos_demo` | `Demo-Pagos-2026!` | alumno ficticio de Horizonte; horario disponible tras contratar asignaciones y publicar |

El JWT ahora incluye `is_superuser` también al refrescarlo. La siembra otorga al propietario una membresía activa sin rol académico, necesaria para el login Vue actual. La autoridad real sigue comprobándose en Django con usuario y membresía actuales; el claim no concede permisos académicos. Si había sesión anterior, cerrar sesión y volver a entrar para obtener los nuevos claims.

### Recorrido visual reproducible

1. Entrar como `admin_demo`. El dashboard académico puede mostrar 403 antes de contratar: abrir directamente `/admin/comercial/planes`. La contratación, consulta del contrato, comprobantes, renovación y descubrimiento de membresías permanecen disponibles sin licencia.
2. Seleccionar **Básico DEMO**, modalidad **process**, desde el configurador. En el campo numérico de alumnos escribir **1** y dejar **1 plantel**. Continuar a checkout y crear orden DEMO por **50.00 MXN**. El modal muestra el UUID de orden y la aprobación pendiente.
3. En el perfil separado entrar como `propietario_demo` y abrir `/comercial/propietario/dashboard`. El panel actual permite consultas, cancelación y revocación, pero **no tiene botón para confirmar DEMO ni aprobar contratos**. Usar la consola del navegador para la petición autenticada indicada abajo. No introducir datos de tarjeta.
4. Regresar al perfil escolar y actualizar `/admin/comercial/licencias` o `/admin/comercial/suscripcion`. Abrir `/admin/grupos`: aparece `DEMO-G1`, materia y docente ficticios. `/admin/alumnos` y `/admin/planes` también están contratados. `/admin/dashboard` (reportes), `/admin/importar` y `/admin/asignaciones` reciben **403** porque Básico no los incluye. La respuesta API debe contener `code=license_required`.
5. Para ampliar capacidades, comprar **Horizonte DEMO mensual**, con **2 alumnos**, **105.00 MXN**, y confirmar otra orden como propietario. Ahora `/admin/dashboard`, `/admin/importar` y `/admin/asignaciones` están autorizados. En asignaciones generar propuesta y publicarla para que `alumno_pagos_demo` consulte `/alumno/horario`. La base trae un alumno, una materia, un grupo y una solicitud ficticia.
6. Con `admin_otro_demo` comprobar que no aparecen licencias ni transacciones de Horizonte. Su institución empieza sin acceso académico ni pagos.

Atajos exactos al checkout (con sesión escolar activa):

- Básico: `http://127.0.0.1:5174/admin/comercial/checkout?plan_id=3c8836bb-a5c2-5d4b-a978-510583fb84f9&precio_id=6729aa72-109f-5e9b-9fe2-3c9082df6fe3&alumnos=1&planteles=1`
- Horizonte mensual: `http://127.0.0.1:5174/admin/comercial/checkout?plan_id=1ff46135-8989-578d-82fe-05a4839cd4fb&precio_id=da85544d-2ff2-5210-94a0-5568072e122f&alumnos=2&planteles=1`

Esos parámetros evitan una limitación del frontend actual: «Contratar» directo omite cantidad y checkout usa 500 por defecto, superior a ambos planes de demo; además el slider del configurador comienza en 50, superior al límite de Básico (30). Usar el campo numérico o estos enlaces. Django rechaza cualquier exceso, independientemente del resumen visual. No se modificó Vue para ocultar esta limitación.

La matriz visual contiene algunas capacidades inferidas por código del plan, y hay estimaciones de add-ons/sedes que no se envían al checkout. Usar los módulos de `/comercial/acceso/` y el importe de la orden como evidencia contractual. No seleccionar add-ons ni sedes adicionales durante este recorrido. Vue también tiene respaldo offline que puede fabricar una orden local si no recibe respuesta: comprobar en Network que checkout responde **201 de Django** y que el propietario encuentra ese UUID en `/comercial/ordenes/`; un modal local por sí solo no demuestra contratación.

En el servicio del dashboard propietario, el mapa define `indicadores` pero la consulta de ingresos usa `RUTAS_COMERCIALES.ingresos` (no definida); el agregador tolera el fallo y puede calcular el total desde transacciones. El contador de pagos pendientes también usa transacciones pendientes, no órdenes pendientes. Para evidencia de ingresos separados por proveedor usar `demoApi('/comercial/ingresos/')`, y para órdenes usar `/comercial/ordenes/`. Son ajustes pendientes de frontend que no se modificaron por la restricción de esta tarea.

En DevTools del perfil **propietario**, definir este ayudante (también sirve en el perfil escolar para verificar rechazos con su propia sesión):

```javascript
async function demoApi(ruta, metodo = 'GET', datos) {
  const respuesta = await fetch('http://127.0.0.1:8011/api/v1' + ruta, {
    method: metodo,
    headers: {
      'Content-Type': 'application/json',
      Authorization: 'Bearer ' + localStorage.getItem('ime_token'),
      'X-Tenant-ID': localStorage.getItem('ime_tenant_id'),
    },
    ...(datos === undefined ? {} : {body: JSON.stringify(datos)}),
  });
  const cuerpo = await respuesta.json();
  console.log(respuesta.status, cuerpo);
  if (!respuesta.ok) throw new Error(cuerpo.detail || 'Error API');
  return cuerpo;
}
const ordenes = await demoApi('/comercial/ordenes/');
console.table(ordenes.results.map(o => ({id:o.id, tenant:o.tenant, estado:o.estado, importe:o.importe})));
const ordenDemo = prompt('Pega el UUID de la orden DEMO pendiente de Horizonte');
await demoApi('/comercial/demo/confirmar/', 'POST', {
  orden: ordenDemo,
  resultado: 'paid',
  referencia: 'demo_visual_' + ordenDemo,
});
```

Repetir con la misma orden/referencia es idempotente. El mismo POST desde el perfil escolar da 403. Para verificar el control en Django desde ese perfil:

```javascript
await demoApi('/comercial/acceso/');    // Básico: activo=true, alumnos/planes_estudios/horarios
await demoApi('/demo/grupos/');          // 200 con Básico
await demoApi('/demo/estadisticas/');    // 403 con Básico; 200 tras pagar Horizonte
```

El contrato empresarial opcional se aprueba desde el perfil propietario con:

```javascript
await demoApi('/comercial/contratos/c1ce3935-8127-5318-a8f8-0a109a4476c4/', 'PATCH', {estado:'active'});
```

Después usar checkout con precio empresarial y `contrato_id=c1ce3935-8127-5318-a8f8-0a109a4476c4` en la URL. El flujo mensual/Básico anterior no necesita ese contrato. La aprobación de contrato por sí sola no activa licencia.

### Política de licencias académicas y transición

`core.0005_licencia_institucional` agrega `Tenant.licencia_requerida`. Las filas que existían al aplicar la migración reciben `False` para conservar compatibilidad; las instituciones nuevas reciben `True`. El campo no es editable en ninguna API pública, incluida la comercial. Una institución en transición pasa a control estricto al crear su **primera orden**, aun pendiente o fallida; la existencia de órdenes lo mantiene tras vencer o revocar. No borrar historial para recuperar transición.

Para una adopción voluntaria anterior a la primera compra, un operador autorizado puede establecer `licencia_requerida=True` mediante gestión interna, previa contratación. No existe apagado global de controles. Esta transición no inventa licencias: `/comercial/acceso/` continúa describiendo exclusivamente derechos pagados, y puede devolver `activo=false` para una institución histórica que aún conserva acceso por transición. Las pruebas de identidad y CSV anteriores usan explícitamente fixtures históricas; las nuevas pruebas usan instituciones estrictas.

| Funcionalidad JSON contratada | Rutas académicas protegidas |
|---|---|
| `alumnos` | `/alumnos/`, detalles y `/alumnos/me/` |
| `planes_estudios` | `/planes-estudios/`, `/nodos/`, `/prerrequisitos/` |
| `reportes` | `/estadisticas-nodos/`, `/demo/estadisticas/`, exportación CSV de resultados |
| `horarios` | `/demo/grupos/`, `/demo/horario/me/` |
| `importaciones` | validación y confirmación CSV; además cada archivo exige su módulo de destino |
| `asignaciones` | generar, listar, consultar y publicar asignaciones; CSV requiere `reportes` |

Se valida autenticación y membresía antes de licencia y se conserva el filtrado por tenant. No hay bypass académico de staff/superusuario ni tenant elegido por el cuerpo. Login, refresh, membresías, metadatos de institución y toda la API comercial permanecen fuera del bloqueo por licencia. Sigue aplicándose el permiso original de cada ruta.

El máximo de alumnos cuenta **todos los registros de la institución**, incluso inactivos: alta REST e importación que agrega alumnos se rechazan si superan capacidad; repetir importaciones o editar un registro existente no consume otra plaza. El bloqueo se comprueba dentro de transacción con bloqueo de Tenant, compartido por ambos caminos. Si hay un descenso de capacidad, las lecturas/ediciones/bajas de los módulos contratados quedan disponibles para reducir uso; se rechazan altas, generación y publicación que excedan el nuevo máximo. Una licencia vencida/revocada bloquea el módulo completo. Renovar continúa disponible.

**Planteles:** el modelo académico actual no tiene entidad Plantel ni endpoint de alta de sedes. Se comprueba capacidad de al menos 1 plantel para operar esta institución, se conserva el límite comprado en acceso y `exigir_capacidad` permite validar una cantidad explícita. No se puede demostrar alta de múltiples sedes ni inferirlas de grupos/planes. El selector de sedes de Vue no provisiona sedes ni cambia el precio enviado al backend. Debe integrarse el conteo cuando exista ese recurso.

### Resultados actuales y alcance de verificación

- **95 pruebas Django aprobadas**, 11.067 s: las 80 anteriores y 15 nuevas, incluida migración real (anteriores en transición/altas estrictas), JWT/refresco del propietario, HTTP/CORS real con servidor efímero de pruebas, módulos distintos, upgrade, vencimiento, inicio futuro, revocación, contrato vencido, suscripción cancelada/vencida, REST/CSV sin escrituras parciales, límites, actualización en cupo e identidad multi-tenant.
- **87 pruebas Vue aprobadas**, 10 archivos, 4.92 s, ejecutadas sin modificar frontend. Son pruebas locales; no equivalen a una sesión automatizada completa de navegador.
- `makemigrations --check --dry-run`: **No changes detected**. `check` sin incidencias. 24 migraciones aplicadas y `migrate --check` correcto en cada base V2 nueva.
- `backend/demo_pagos_integracion_v2_20261112.sqlite3`: recorrido comercial previo más compra Básico para la otra institución; Django admite grupos, rechaza reportes y genera una asignación real con Horizonte. Tras el recorrido: 3 órdenes pagadas, 1 pendiente, 3 transacciones/comprobantes/licencias, 1 suscripción y **1355 MXN DEMO**. El script imprime 1305 antes de la compra Básico y 1355 al finalizar.
- `backend/demo_pagos_cierre_v2_20261112.sqlite3`: repetición final correcta del script, que también comprueba rechazo académico antes del primer pago e imprime los ingresos finales `1355 MXN`.
- `backend/demo_pagos_presentacion_v2_20261112.sqlite3`: base independiente lista para navegador, sin compras. Verificados por HTTP real login de ambos usuarios, claims, membresías, CORS de 5174, catálogo y acceso inicialmente inactivo, además del servicio Vite de rutas de ambos paneles. No se ejecutó una navegación gráfica automatizada ni se validó cada interacción visual.
- Las dos SQLite académicas originales y los archivos de `frontend/src` conservan sus hashes iniciales. No se ejecutaron migraciones ni siembras sobre las bases académicas. No se usa Stripe externo ni se valida Stripe E2E.

Comandos para repetir todas las pruebas y crear otro recorrido independiente:

```bash
backend/venv/bin/python backend/manage.py test apps.core apps.comercial --settings=apps.core.tests.settings_aislados --noinput
backend/venv/bin/python backend/manage.py makemigrations --check --dry-run --settings=apps.core.tests.settings_aislados
backend/venv/bin/python backend/demo_pagos.py --database "$PWD/backend/demo_pagos_recorrido_v2_nuevo.sqlite3" --verificar
```

```bash
cd frontend
npm test -- --cache=false
```

El script exige archivo inexistente. Para repetir con estado limpio escoger un nombre nuevo; no borrar bases ni aplicar migraciones a las académicas. Para otra presentación nueva omitir `--verificar`. Los comandos de las secciones siguientes conservan el recorrido API y la evidencia de la primera fase.

## Preparar una base nueva

Python disponible: `backend/venv/bin/python`. Dependencias declaradas en `backend/requirements.txt`. No ejecutar `migrate` con la configuración habitual.

```bash
export PAGOS_DEMO_DATABASE="$PWD/backend/demo_pagos_presentacion_v2_20261112.sqlite3"
backend/venv/bin/python backend/demo_pagos.py --database "$PAGOS_DEMO_DATABASE"
```

La base de presentación anterior ya se creó durante esta validación: para repetir la preparación escoger otro nombre `backend/demo_pagos_*.sqlite3`. El script rechaza archivos existentes con apertura exclusiva, también symlinks y rutas fuera de backend. No borra, copia ni reutiliza bases. Si falla a mitad del recorrido, conservar el archivo para diagnóstico y usar otro nombre. `DATABASE_URL` no selecciona esta base. La configuración fuerza proveedor DEMO y vacía claves Stripe incluso si el entorno contiene otras.

La siembra V2 crea dos instituciones ficticias, cinco usuarios, un plan con todos los módulos académicos y límites de 100 alumnos/2 planteles, un plan básico de 30 alumnos/1 plantel (alumnos, planes de estudio y horarios), tres precios (mensual, empresarial y por proceso) y contrato empresarial en borrador. Incluye datos académicos ficticios para el recorrido visual. Los UUID del catálogo e instituciones son deterministas; fechas relativas al momento de creación y UUID de órdenes/transacciones varían. Contraseña exclusivamente local para todos: `Demo-Pagos-2026!`.

| Recurso | Identificador |
|---|---|
| Instituto Horizonte Ficticio | `1a1a6fea-6403-5d74-b74f-4861c38600e4` |
| Academia Alterna Ficticia | `9e166ed9-566a-5c51-96d3-4fa883086e3a` |
| Precio mensual (100 + 2.50 por alumno) | `da85544d-2ff2-5210-94a0-5568072e122f` |
| Precio empresarial (1200 MXN) | `47c2182d-60a6-5a7b-9685-21390fc7d74c` |
| Contrato empresarial | `c1ce3935-8127-5318-a8f8-0a109a4476c4` |

Usuarios: `propietario_demo` (superusuario), `admin_demo` (administrador Horizonte), `admin_otro_demo` (administrador Alterna), `staff_demo` (staff y administrador Horizonte, sin autoridad SaaS). No hay personas ni datos bancarios reales.

## Recorrido manual por API

Iniciar opcionalmente un servidor adicional en un puerto libre; no sustituir los activos. Si 8011 está ocupado, elegir otro y ajustar `BASE`.

```bash
PAGOS_DEMO_DATABASE="$PAGOS_DEMO_DATABASE" backend/venv/bin/python backend/manage.py runserver 127.0.0.1:8011 --noreload --settings=config.settings_pagos_demo
```

En otra terminal, con `curl` y `jq` disponibles:

```bash
export BASE=http://127.0.0.1:8011
export ADMIN=$(curl -fsS "$BASE/api/v1/token/" -H 'Content-Type: application/json' -d '{"matricula":"admin_demo","password":"Demo-Pagos-2026!"}' | jq -r .access)
export OWNER=$(curl -fsS "$BASE/api/v1/token/" -H 'Content-Type: application/json' -d '{"matricula":"propietario_demo","password":"Demo-Pagos-2026!"}' | jq -r .access)
export OTHER=$(curl -fsS "$BASE/api/v1/token/" -H 'Content-Type: application/json' -d '{"matricula":"admin_otro_demo","password":"Demo-Pagos-2026!"}' | jq -r .access)
export CONTRACT=c1ce3935-8127-5318-a8f8-0a109a4476c4
export PRICE=47c2182d-60a6-5a7b-9685-21390fc7d74c
export PURCHASE="{\"precio\":\"$PRICE\",\"contrato\":\"$CONTRACT\",\"alumnos\":2}"
curl -sS "$BASE/api/v1/comercial/acceso/" -H "Authorization: Bearer $ADMIN"
curl -i "$BASE/api/v1/comercial/checkout/" -H "Authorization: Bearer $ADMIN" -H 'Content-Type: application/json' -H 'Idempotency-Key: presentacion_empresa_0001' -d "$PURCHASE"
```

Acceso inicial `activo=false`; compra con contrato draft devuelve 400. Intentar aprobar con ADMIN devuelve 403. Aprobar como propietario:

```bash
curl -i -X PATCH "$BASE/api/v1/comercial/contratos/$CONTRACT/" -H "Authorization: Bearer $ADMIN" -H 'Content-Type: application/json' -d '{"estado":"active"}'
curl -fsS -X PATCH "$BASE/api/v1/comercial/contratos/$CONTRACT/" -H "Authorization: Bearer $OWNER" -H 'Content-Type: application/json' -d '{"estado":"active"}'
export ORDER=$(curl -fsS "$BASE/api/v1/comercial/checkout/" -H "Authorization: Bearer $ADMIN" -H 'Content-Type: application/json' -H 'Idempotency-Key: presentacion_empresa_0001' -d "$PURCHASE" | jq -r .orden)
curl -fsS "$BASE/api/v1/comercial/ordenes/$ORDER/" -H "Authorization: Bearer $ADMIN"
export CONFIRM="{\"orden\":\"$ORDER\",\"resultado\":\"paid\",\"referencia\":\"demo_presentacion_pago_0001\"}"
curl -i "$BASE/api/v1/comercial/demo/confirmar/" -H "Authorization: Bearer $ADMIN" -H 'Content-Type: application/json' -d "$CONFIRM"
curl -fsS "$BASE/api/v1/comercial/demo/confirmar/" -H "Authorization: Bearer $OWNER" -H 'Content-Type: application/json' -d "$CONFIRM"
```

La orden nace `pending`, proveedor `DEMO`, `url=null`, importe calculado por servidor `1200.00 MXN`. No hay redirección de pago real. El administrador no puede confirmarla (403); el propietario sí. Repetir checkout con la misma clave y cuerpo devuelve la misma orden (201); modificar alumnos conservando clave devuelve 409. Repetir la confirmación exacta devuelve la misma transacción, sin duplicar comprobante ni licencia. Una renovación usa otra referencia, no se simula repitiendo la referencia anterior.

```bash
curl -fsS "$BASE/api/v1/comercial/ordenes/$ORDER/" -H "Authorization: Bearer $ADMIN"
curl -fsS "$BASE/api/v1/comercial/transacciones/" -H "Authorization: Bearer $ADMIN"
curl -fsS "$BASE/api/v1/comercial/licencias/" -H "Authorization: Bearer $ADMIN"
curl -fsS "$BASE/api/v1/comercial/acceso/" -H "Authorization: Bearer $ADMIN"
export RECEIPT=$(curl -fsS "$BASE/api/v1/comercial/comprobantes/" -H "Authorization: Bearer $ADMIN" | jq -r '.results[0].id')
curl -fsS "$BASE/api/v1/comercial/comprobantes/$RECEIPT/pdf/" -H "Authorization: Bearer $ADMIN" -o /tmp/comprobante-demo-pagos.pdf
curl -i "$BASE/api/v1/comercial/ordenes/$ORDER/" -H "Authorization: Bearer $OTHER"
curl -sS "$BASE/api/v1/comercial/licencias/" -H "Authorization: Bearer $OTHER"
curl -i "$BASE/api/v1/comercial/ordenes/"
curl -fsS "$BASE/api/v1/comercial/ingresos/" -H "Authorization: Bearer $OWNER"
```

Esperado: `paid`, una transacción, licencia activa con horarios/reportes y límites 100/2, PDF interno sin validez fiscal; otra institución obtiene 404 para la orden y lista de licencias vacía; sin JWT, 401. Ingresos DEMO quedan separados por proveedor/moneda. Una orden empresarial no crea suscripción. Para demostrar suscripción comprar precio mensual sin contrato con una clave nueva y confirmar otra referencia DEMO: dos alumnos suman `105.00 MXN`, suscripción activa y periodo de 30 días. No se concede acceso por el retorno del navegador.

## Recorrido automático y pruebas ejecutadas

```bash
backend/venv/bin/python backend/demo_pagos.py --database "$PWD/backend/demo_pagos_otro_recorrido.sqlite3" --verificar
backend/venv/bin/python backend/manage.py test apps.core apps.comercial --settings=apps.core.tests.settings_aislados --noinput
backend/venv/bin/python backend/manage.py makemigrations --check --dry-run --settings=apps.core.tests.settings_aislados
PAGOS_DEMO_DATABASE="$PAGOS_DEMO_DATABASE" backend/venv/bin/python backend/manage.py migrate --check --settings=config.settings_pagos_demo
```

Resultados observados en la primera fase (antes del cierre V2):

- 80 pruebas core/comercial, **OK**, 11.200 s, SQLite de pruebas en memoria creada/destruida; system check sin incidencias. Incluyen expiración, cancelación, recuperación tras fallo, snapshot, precios inmutables, revocación y facturación interna.
- `makemigrations --check --dry-run`: **No changes detected**. Aplicadas las 23 migraciones a la nueva base; `migrate --check` y `check`: correctos.
- Base `backend/demo_pagos_integral_20261112.sqlite3`: recorrido completo **OK** usando APIClient dentro del proceso Django, JWT obtenido por login y refresh reales, sin servidor HTTP ni proveedor externo. Dos órdenes pagadas (1200 + 105), una pendiente de otra institución; ingresos DEMO `1305 MXN`.
- Base `backend/demo_pagos_final_20261112.sqlite3`: repetición del recorrido con la siembra final de dos planes y tres precios. Base de presentación separada `backend/demo_pagos_presentacion_20261112.sqlite3`: migrada y sembrada, sin órdenes ni pagos, contrato en borrador.
- Comprobados 401 JWT ausente/inválido, 403 aprobación escolar/staff, 404 recurso ajeno, 409 clave incompatible, 400 manipulación de importe/contrato draft; aislamiento en contratos, órdenes, licencias, transacciones y comprobantes. Misma clave en instituciones distintas es independiente.
- La primera ejecución (`demo_pagos_validacion_20261112.sqlite3`) migró/sembró y falló por enviar `username`: la API exige `matricula`. Corregido el script; repetición completa en una base nueva. No reutilizar ese primer archivo para presentar.
- En la primera fase `exigir_capacidad` solo se probaba como servicio. Esa limitación queda corregida por la integración académica V2 descrita al principio de esta guía.

SHA-256 de las bases preexistentes, iguales antes y después de preparar/verificar la demo:

| Archivo | SHA-256 |
|---|---|
| `db.sqlite3` | `5597ef15f903c7da8841172d850e07bc56d1b655f7f518bec6a4014e2a523d94` |
| `backend/demo_backend_20261105.sqlite3` | `b596fdb537eeda0c052bb8e3337b203aaa28770abfd60cb6f3cbadaa46d373cd` |

## Revisión del contrato y límites pendientes

Los modelos y router implementan los recursos de `CONTRATO_COMERCIAL_API.md`: UUID, importes decimales, relaciones protegidas, snapshots, clave única por institución, transacción única por proveedor/referencia y comprobante por transacción. JWT y membresía activa resuelven tenant; superusuario activo tiene autoridad global, `is_staff` solo no la concede. Solo propietario publica catálogo, aprueba contratos, confirma DEMO, revoca licencias y consulta ingresos/eventos. Los precios no admiten PATCH por API. Contrato no otorga acceso sin pago.

Matices que impiden afirmar coincidencia absoluta o preparación productiva:

- El contrato generaliza 409 para conflictos de estado/idempotencia; reutilizar una referencia de transacción con otros datos genera actualmente 400 (`ValidationError`). Checkout incompatible sí genera 409.
- La inmutabilidad de precios/transacciones es una garantía de las rutas públicas actuales; no hay prohibición general de modificaciones por ORM/admin SQL.
- `demo/confirmar/` registra una transacción y comprobante, pero no crea un `Evento` con la identidad del propietario que aprobó. La revocación sí tiene evento interno. Auditoría personal de aprobación ampliada queda pendiente.
- Pruebas secuenciales de idempotencia correctas. SQLite no demuestra garantías concurrentes de bloqueos de fila de PostgreSQL; falta prueba de concurrencia sobre el motor de despliegue.
- Stripe usa intervalos mes para monthly/hybrid y año para annual/maintenance; `dias` no permite escoger intervalos recurrentes arbitrarios. DEMO mensual/híbrido fija 30 días.
- PDF es comprobante interno; PAC, emisión CFDI, reembolsos, disputas y prorrateos quedan fuera del recorrido.

## Integrar Stripe sandbox cuando haya credenciales

**Stripe no está validado de extremo a extremo.** La suite ejecutó mocks del SDK para checkout, pago único, factura inicial/renovación, timeout y cancelación; la firma HMAC local fue comprobada con secreto ficticio. Eso no comprueba conectividad, credenciales, versión de eventos del sandbox ni entrega real de webhooks.

Usar otra base nueva sembrada sin `--verificar`. `settings_pagos_demo` fuerza DEMO: crear una configuración local ignorada `backend/config/settings_local.py` que importe `config.settings_pagos_demo` y después sobrescriba únicamente proveedor y claves desde entorno:

```python
from .settings_pagos_demo import *
import os
COMMERCIAL_PROVIDER = 'stripe'
STRIPE_SECRET_KEY = os.environ['STRIPE_SECRET_KEY']
STRIPE_WEBHOOK_SECRET = os.environ['STRIPE_WEBHOOK_SECRET']
if not STRIPE_SECRET_KEY.startswith('sk_test_'):
    raise RuntimeError('Solo sandbox')
COMMERCIAL_SUCCESS_URL = os.environ['COMMERCIAL_SUCCESS_URL']
COMMERCIAL_CANCEL_URL = os.environ['COMMERCIAL_CANCEL_URL']
```

Si ese archivo ya existe, conservarlo y usar otro módulo local excluido de Git. No escribir secretos en archivos ni en frontend. Cargar `STRIPE_SECRET_KEY=sk_test_...` mediante un gestor seguro o entrada de terminal sin eco; `STRIPE_WEBHOOK_SECRET=whsec_...` debe corresponder al listener concreto. Configurar URLs de retorno al frontend de demostración. Mantener `PAGOS_DEMO_DATABASE` apuntando a la nueva base sandbox.

En una terminal con Stripe CLI autenticado exclusivamente al sandbox:

```bash
stripe listen --events checkout.session.completed,checkout.session.async_payment_succeeded,checkout.session.async_payment_failed,invoice.paid,invoice.payment_failed,customer.subscription.updated,customer.subscription.deleted --forward-to http://127.0.0.1:8012/api/v1/comercial/webhooks/stripe/
```

Con el secreto que imprima ese listener cargado en el entorno del backend, iniciar otro servidor en puerto libre:

```bash
backend/venv/bin/python backend/manage.py runserver 127.0.0.1:8012 --noreload --settings=config.settings_local
```

Repetir login y checkout sobre 8012 con nueva clave. Abrir la URL HTTPS devuelta por Stripe y usar únicamente un medio de pago de prueba publicado por Stripe. Para pago único utilizar precio empresarial y aprobar contrato; para recurrente usar el mensual. No usar `demo/confirmar/`: debe responder 403 bajo proveedor stripe.

Confirmar en sandbox y DB: sesión enlazada a la orden, importe/moneda coincidentes, webhook 200 y evento durable, transacción única, licencia y periodo correctos. El mensual se activa por `invoice.paid`, no por retorno ni sesión completada. Reenviar el mismo evento desde sandbox y comprobar que no duplica movimientos. Probar firma errónea, pago fallido y cancelación al fin del periodo, y conservar IDs de sesión/factura/evento y resultados sin claves ni datos de tarjeta. Los eventos genéricos de `stripe trigger` sin vínculo con una orden local no validan la contratación completa. Si se prueban renovaciones con reloj de prueba, comprobar también fin de periodo y una transacción por factura.

Referencias oficiales consultadas: [fulfillment de Checkout](https://docs.stripe.com/checkout/fulfillment), [firmas y reintentos](https://docs.stripe.com/events/manage-webhook-endpoints), [Stripe CLI](https://docs.stripe.com/cli). Registrar la versión del SDK instalado y la versión de eventos configurada cuando se ejecute sandbox.
