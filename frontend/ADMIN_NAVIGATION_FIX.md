# Investigación del contenido administrativo vacío

## Causa raíz y reproducción

El template original de `ImportarView.vue` construía `new Blob(...)` para
mostrar el tamaño del CSV. El compilador de templates resuelve ese identificador
como `_ctx.Blob`; Blob no es un global permitido del template ni una propiedad
del componente. La primera renderización falla incluso con el CSV vacío.

Se reprodujo con los archivos originales de HEAD de ImportarView y AdminLayout
en una copia temporal del frontend, conservando intacto el árbol de trabajo.
La prueba previa `src/repro.test.js` produjo:

```text
1. Dashboard visible: true
2. Importar visible: false
3. Alumnos visible tras importar: false
4. Grupos visible tras importar: false
5. Planes visible tras importar: false
TypeError: _ctx.Blob is not a constructor
TypeError: Cannot destructure property 'type' of 'vnode' as it is null.
TypeError: Cannot read properties of null (reading 'component')
```

Esto reproduce el sidebar y encabezado persistentes con contenido vacío tras
navegar: falla el descendiente de RouterView y las actualizaciones posteriores
encuentran nodos inválidos. No depende del tiempo de expiración del JWT: visitar
importación es el disparador confirmado. No se ha demostrado otro disparador
temporal independiente.

## Estado recibido y cambios

Había modificaciones previas en api/index.js, AdminLayout.vue, AlumnoLayout.vue,
main.js e ImportarView.vue, además de una prueba de reproducción y archivos
ajenos al frontend. Se conservaron. Esos cambios ya trasladaban Blob al script,
añadían límites de error y sincronizaban la sesión mediante eventos.

En esta intervención:

- Se completó el cálculo de tamaño desde el script utilizando Blob del navegador,
  eliminando el fallback a Buffer, que no está disponible en navegadores.
- Se marcaron también las solicitudes en espera de renovación como reintentadas.
  Antes podían iniciar otra renovación si el servidor rechazaba el nuevo token.
- Un segundo 401 termina la sesión; se eliminan las cabeceras Authorization
  heredadas cuando no hay token y al notificar expiración.
- Se añadieron pruebas con aserciones de DOM y pruebas del interceptor. La
  prueba exploratoria previa se conserva sin cambios.

Se revisaron RouterView, rutas anidadas, guardas de roles, estado Pinia,
listeners de main.js y cargas de las vistas. Las vistas de catálogo ya capturan
errores HTTP; un 500 simulado no reproduce la destrucción del contenido.

## Verificación

`npm test`: 4 archivos, 17 pruebas aprobadas.

`npm run build`: compilación Vite aprobada, 117 módulos transformados.

Las nuevas pruebas cubren:

- Cuatro ciclos por importar, alumnos, grupos y planes con vistas y router reales.
- Edición de CSV con caracteres UTF-8 y cálculo correcto de tamaño.
- HTTP 500 sin perder el contenido de las rutas.
- Renovación JWT exitosa con sincronización de Pinia.
- Refresh fallido: salida hacia login y bloqueo posterior de rutas protegidas.
- Solicitudes 401 simultáneas: una renovación y un máximo de dos intentos por
  solicitud, incluso cuando el token renovado es rechazado.
- Rechazo de toda la cola al fallar refresh y uso posterior de otra sesión.
- Login rechazado sin renovar JWT y ausencia de Authorization obsoleto.

## Límites y pendientes

La reproducción y verificación usan jsdom y respuestas HTTP simuladas; queda
pendiente una prueba manual en navegador con un servidor y credenciales reales.
No se esperó una expiración JWT real ni se hicieron escrituras al backend.
No se modificaron backend, SQLite, migraciones ni configuración de producción;
no se hicieron commits ni push.
