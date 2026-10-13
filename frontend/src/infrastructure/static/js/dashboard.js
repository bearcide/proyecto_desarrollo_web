// Panel del alumno: /alumnos/{id}/, /planes-estudios/{id}/ y /nodos/?plan_estudios=
(function () {
  'use strict';
  const { API, esc, nombreCompleto, cargarCatalogo, avisoError } = window.IME;
  const sesion = window.IME.requireSesion();
  if (!sesion) return;

  const $ = (id) => document.getElementById(id);
  const set = (id, v) => { $(id).textContent = v; };

  function cuentaRegresiva(iso) {
    const el = $('cuenta-regresiva');
    const inicio = new Date(iso).getTime();
    if (!iso || Number.isNaN(inicio)) { el.textContent = 'Tu ventana aún no está definida.'; return; }
    (function tick() {
      const d = inicio - Date.now();
      if (d <= 0) { el.textContent = 'Ya puedes inscribirte'; el.classList.add('open'); return; }
      const dias = Math.floor(d / 864e5), h = Math.floor(d % 864e5 / 36e5), m = Math.floor(d % 36e5 / 6e4), s = Math.floor(d % 6e4 / 1e3);
      el.textContent = `Faltan ${dias} d ${h} h ${m} min ${s} s`;
      setTimeout(tick, 1000);
    })();
  }

  async function init() {
    try {
      const [alumno, plan] = await Promise.all([API.alumnos.get(sesion.id), API.planes.get(sesion.plan_estudios)]);
      window.IME.Session.setAlumno(alumno);
      set('alumno-nombre', `Hola, ${nombreCompleto(alumno)}`);
      set('alumno-detalle', `${plan.nombre}, semestre ${alumno.semestre}. Cuenta ${alumno.numero_de_cuenta || 'sin asignar'}.`);
      set('num-cuenta', alumno.numero_de_cuenta || '—');
      // Estos dos campos no existen aún en /alumnos/: se muestran si el backend los agrega.
      set('num-inscripcion', alumno.numero_inscripcion ?? '—');
      set('ventana-texto', alumno.ventana_texto || 'Por definir');
      cuentaRegresiva(alumno.ventana_inicio);
      set('stat-cursadas', alumno.materias_cursadas);
      set('stat-creditos', `${alumno.creditos} créditos acumulados`);

      const catalogo = await cargarCatalogo(alumno.plan_estudios);
      const delSemestre = catalogo.filter((m) => m.semestre === alumno.semestre);
      $('tabla-materias').innerHTML = delSemestre.length
        ? delSemestre.map((m) => `<tr><td class="mono">${esc(m.clave)}</td><td>${esc(m.nombre)}</td>
            <td class="num">${m.creditos}</td><td>${esc(m.requisitos.join(', ') || '—')}</td></tr>`).join('')
        : `<tr><td colspan="4" class="muted">No hay materias registradas para tu semestre.</td></tr>`;
    } catch (e) {
      $('tabla-materias').innerHTML = '<tr><td colspan="4" class="muted">No se pudo cargar la información.</td></tr>';
      avisoError($('alertas'), e);
    }
  }
  init();
})();
