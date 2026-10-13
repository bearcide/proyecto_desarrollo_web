// Horario semanal de la selección del alumno. Requiere que las materias traigan `horarios`.
(function () {
  'use strict';
  const { esc, cargarCatalogo, Seleccion, cuadricula, avisoError } = window.IME;
  const alumno = window.IME.requireSesion();
  if (!alumno) return;
  const $ = (id) => document.getElementById(id);

  async function init() {
    try {
      const catalogo = await cargarCatalogo(alumno.plan_estudios);
      const ids = Seleccion.cargar(alumno.id);
      const elegidas = catalogo.filter((m) => ids.has(m.id));
      const conHorario = elegidas.filter((m) => m.horarios.length);

      $('resumen').textContent = `${elegidas.length} materias, ${elegidas.reduce((s, m) => s + m.creditos, 0)} créditos.`;
      $('estado-vacio').hidden = elegidas.length > 0;
      $('estado-lleno').hidden = elegidas.length === 0;
      if (!elegidas.length) return;

      $('sin-horarios').hidden = conHorario.length > 0;
      $('panel-horario').hidden = conHorario.length === 0;
      $('panel-horario-grid').innerHTML = conHorario.length ? cuadricula(conHorario) : '';
      $('leyenda').innerHTML = elegidas.map((m) =>
        `<li><span class="dot t${m.tono}"></span><strong>${esc(m.nombre)}</strong> ${esc(m.profesor || m.clave)}</li>`).join('');
    } catch (e) { avisoError($('alertas'), e); }
  }
  init();
})();
