/**
 * Adaptadores API -> vista y utilidades compartidas por las páginas.
 *
 * TODO el mapeo "campo del backend -> campo de la UI" vive aquí. Los campos que el
 * backend todavía no expone (profesor, cupo, horarios, materias aprobadas) se leen de
 * forma opcional: cuando el backend los agregue, las pantallas se activan solas.
 */
(function (root) {
  'use strict';
  const { API } = root.IME;

  const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'];
  const H0 = 8, H1 = 14;

  const esc = (t) => String(t ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  // ---------- adaptadores ----------
  function nombreCompleto(a) {
    return [a.nombre, a.apellido_paterno, a.apellido_materno].filter(Boolean).join(' ');
  }

  function materiaDesdeNodo(n, nodosPorId, stats) {
    return {
      id: n.id,
      clave: n.clave,
      nombre: n.nombre,
      creditos: n.creditos,
      semestre: n.semestre,
      requisitosIds: n.prerrequisitos || [],
      requisitos: (n.prerrequisitos || []).map((id) => (nodosPorId.get(id) || {}).nombre || `#${id}`),
      inscritos: stats ? stats.alumnos_inscritos : null,
      // Aún no existen en el backend (null/[] = "no disponible"):
      cupo: n.cupo ?? null,
      profesor: n.profesor ?? null,
      horarios: n.horarios ?? [],
      tono: n.id % 6,
    };
  }

  /** Catálogo de materias del plan del alumno: /nodos/ + /estadisticas-nodos/. */
  async function cargarCatalogo(planId) {
    const [nodos, estadisticas] = await Promise.all([
      API.nodos.list({ plan_estudios: planId, ordering: 'semestre' }),
      API.estadisticas.list(),
    ]);
    const nodosPorId = new Map(nodos.map((n) => [n.id, n]));
    const statsPorNodo = new Map(estadisticas.map((e) => [e.nodo, e]));
    return nodos.map((n) => materiaDesdeNodo(n, nodosPorId, statsPorNodo.get(n.id)));
  }

  // ---------- reglas de UI (el backend debe revalidar siempre) ----------
  const choca = (a, b) => a.horarios.some((x) => b.horarios.some((y) => x.dia === y.dia && x.ini < y.fin && y.ini < x.fin));
  /** Solo se puede validar con la lista de aprobadas (ids). Si el backend no la da, devuelve []. */
  const faltantes = (m, aprobadasIds) => (aprobadasIds ? m.requisitosIds.filter((id) => !aprobadasIds.includes(id)) : []);
  const hayCupo = (m) => m.cupo == null || (m.inscritos ?? 0) < m.cupo;
  const txtHorario = (m) => m.horarios.map((h) => `${h.dia.slice(0, 3)} ${h.ini}:00 a ${h.fin}:00`).join(', ');

  // ---------- selección local (borrador) ----------
  const claveSel = (alumnoId) => `ime.seleccion.${alumnoId}`;
  const Seleccion = {
    cargar(alumnoId) {
      try { return new Set(JSON.parse(root.sessionStorage.getItem(claveSel(alumnoId))) || []); } catch (_) { return new Set(); }
    },
    guardar(alumnoId, set) {
      try { root.sessionStorage.setItem(claveSel(alumnoId), JSON.stringify([...set])); } catch (_) { /* noop */ }
    },
  };

  // ---------- cuadrícula semanal (solo materias con horarios) ----------
  function cuadricula(materias) {
    let h = '<div class="tt">';
    DIAS.forEach((d, i) => { h += `<div class="tt-day" style="grid-column:${i + 2};grid-row:1">${d.slice(0, 3)}</div>`; });
    for (let x = H0; x < H1; x++) h += `<div class="tt-hour" style="grid-row:${x - H0 + 2}">${x}:00</div>`;
    materias.forEach((m) => m.horarios.forEach((b) => {
      const col = DIAS.indexOf(b.dia);
      if (col < 0 || b.ini < H0 || b.fin > H1) return;
      h += `<div class="tt-block t${m.tono}" style="grid-column:${col + 2};grid-row:${b.ini - H0 + 2} / span ${b.fin - b.ini}">
        <strong>${esc(m.nombre)}</strong><span>${esc(m.clave)}</span></div>`;
    }));
    return h + '</div>';
  }

  // ---------- avisos ----------
  function aviso(contenedor, html, tipo) {
    contenedor.innerHTML = `<div class="aviso ${tipo || 'error'}" role="alert"><span>${html}</span>
      <button type="button" aria-label="Cerrar aviso">&times;</button></div>`;
    contenedor.querySelector('button').addEventListener('click', () => { contenedor.innerHTML = ''; });
  }
  const avisoError = (contenedor, err) => aviso(contenedor, esc(err && err.message ? err.message : 'Ocurrió un error inesperado.'), 'error');

  Object.assign(root.IME, {
    DIAS, esc, nombreCompleto, materiaDesdeNodo, cargarCatalogo,
    choca, faltantes, hayCupo, txtHorario, Seleccion, cuadricula, aviso, avisoError,
  });
})(typeof window !== 'undefined' ? window : globalThis);
