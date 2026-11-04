// Pantalla de inscripción: catálogo real desde /nodos/ + /estadisticas-nodos/.
(function () {
  'use strict';
  const { API, esc, cargarCatalogo, choca, faltantes, hayCupo, txtHorario, Seleccion, cuadricula, aviso, avisoError } = window.IME;
  const alumno = window.IME.requireSesion();
  if (!alumno) return;

  const $ = (id) => document.getElementById(id);
  const $lista = $('lista-materias'), $sel = $('seleccion'), $total = $('total-creditos'),
        $alertas = $('alertas'), $confirmar = $('confirmar'), $buscador = $('buscador'),
        $semestre = $('filtro-semestre'), $tt = $('tt-mini');

  let materias = [];
  const aprobadas = alumno.materias_aprobadas_ids || null; // el backend aún no lo expone: sin él no se valida prerrequisito en cliente
  const seleccion = Seleccion.cargar(alumno.id);

  const porId = (id) => materias.find((m) => m.id === id);
  const conflictoCon = (m) => materias.find((o) => o.id !== m.id && seleccion.has(o.id) && choca(m, o));

  function alternar(id) {
    const m = porId(id);
    if (seleccion.has(id)) { seleccion.delete(id); $alertas.innerHTML = ''; return commit(); }
    const falta = faltantes(m, aprobadas);
    if (falta.length) return aviso($alertas, `Para inscribir <strong>${esc(m.nombre)}</strong> necesitas haber aprobado: ${esc(falta.map((i) => (porId(i) || {}).nombre).join(', '))}.`);
    if (!hayCupo(m)) return aviso($alertas, `El grupo de <strong>${esc(m.nombre)}</strong> está lleno. Elige otro grupo o materia.`);
    const c = conflictoCon(m);
    if (c) return aviso($alertas, `<strong>${esc(m.nombre)}</strong> se cruza con <strong>${esc(c.nombre)}</strong>. Quita una de las dos para continuar.`);
    seleccion.add(id); $alertas.innerHTML = ''; commit();
  }
  function commit() { Seleccion.guardar(alumno.id, seleccion); render(); }

  function fila(m) {
    const falta = faltantes(m, aprobadas);
    const elegida = seleccion.has(m.id);
    const lleno = !hayCupo(m);
    const boton = elegida ? '<button class="btn-line btn-quitar" type="button">Quitar</button>'
      : lleno ? '<button class="btn-line" type="button" disabled>Grupo lleno</button>'
      : falta.length ? '<button class="btn-line" type="button" disabled>No disponible</button>'
      : '<button class="btn-brand" type="button">Agregar</button>';

    let cupo = '';
    if (m.cupo != null) {
      const pct = Math.min(100, Math.round(((m.inscritos ?? 0) / m.cupo) * 100));
      const libres = m.cupo - (m.inscritos ?? 0);
      cupo = `<div class="cupo-bar ${lleno ? 'lleno' : pct >= 85 ? 'alto' : ''}"><span style="width:${pct}%"></span></div>
        <div class="cupo-txt">${libres > 0 ? `${libres} lugares libres de ${m.cupo}` : 'Sin lugares libres'}</div>`;
    } else if (m.inscritos != null) {
      cupo = `<div class="cupo-txt">${m.inscritos} alumnos inscritos</div>`;
    }

    const meta = [`${m.creditos} créditos`, `Semestre ${m.semestre}`, m.profesor].filter(Boolean).map(esc).join(', ');
    const li = document.createElement('li');
    li.className = 'mat' + (elegida ? ' elegida' : '');
    li.innerHTML = `
      <div>
        <div class="mat-name">${esc(m.nombre)}<small>${esc(m.clave)}</small></div>
        <div class="mat-meta">${meta}</div>
        ${m.horarios.length ? `<div class="mat-meta">${esc(txtHorario(m))}</div>` : ''}
        ${m.requisitos.length ? `<div class="mat-meta mat-req ${falta.length ? 'falta' : ''}">Requiere: ${esc(m.requisitos.join(', '))}</div>` : ''}
      </div>
      <div class="cupo">${cupo}</div>
      <div class="accion">${boton}</div>`;
    li.querySelector('button:not([disabled])')?.addEventListener('click', () => alternar(m.id));
    return li;
  }

  function render() {
    const q = $buscador.value.trim().toLowerCase();
    const sem = $semestre.value;
    const visibles = materias.filter((m) =>
      (!q || [m.nombre, m.clave, m.profesor || ''].some((t) => t.toLowerCase().includes(q))) &&
      (!sem || String(m.semestre) === sem));
    $lista.replaceChildren(...visibles.map(fila));
    if (!visibles.length) $lista.innerHTML = '<li class="mat"><span class="muted">No hay materias que coincidan con tu búsqueda.</span></li>';

    const elegidas = materias.filter((m) => seleccion.has(m.id));
    const conHorario = elegidas.filter((m) => m.horarios.length);
    $tt.innerHTML = conHorario.length ? cuadricula(conHorario) : '';
    $sel.innerHTML = elegidas.length
      ? elegidas.map((m) => `<li>${esc(m.nombre)}<span>${esc(m.horarios.length ? txtHorario(m) : m.clave)}</span></li>`).join('')
      : '<li class="vacio">Agrega materias de la lista para armar tu selección.</li>';
    $total.textContent = elegidas.reduce((s, m) => s + m.creditos, 0);
    $confirmar.disabled = !elegidas.length;
  }

  async function confirmar() {
    if (!API.inscripciones) {
      return aviso($alertas, 'Tu selección quedó guardada en este navegador, pero el servidor todavía no tiene un endpoint de inscripciones para registrarla.', 'warn');
    }
    $confirmar.disabled = true;
    try {
      await API.inscripciones.confirmar(alumno.id, [...seleccion]);
      aviso($alertas, 'Inscripción confirmada.', 'ok');
    } catch (e) { avisoError($alertas, e); } finally { render(); }
  }

  async function init() {
    $lista.innerHTML = '<li class="mat"><span class="muted">Cargando materias…</span></li>';
    try {
      materias = await cargarCatalogo(alumno.plan_estudios);
    } catch (e) { $lista.innerHTML = ''; return avisoError($alertas, e); }
    [...new Set(materias.map((m) => m.semestre))].sort((a, b) => a - b)
      .forEach((s) => $semestre.insertAdjacentHTML('beforeend', `<option value="${s}">Semestre ${s}</option>`));
    // Descarta ids guardados que ya no existan en el catálogo.
    [...seleccion].forEach((id) => { if (!porId(id)) seleccion.delete(id); });
    render();
  }

  $buscador.addEventListener('input', render);
  $semestre.addEventListener('change', render);
  $confirmar.addEventListener('click', confirmar);
  init();
})();
