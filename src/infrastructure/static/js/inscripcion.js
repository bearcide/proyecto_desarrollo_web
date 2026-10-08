// Validaciones de frontend (reflejan ValidadorInscripcion). El backend debe revalidar siempre.
(function () {
  const materias = JSON.parse(document.getElementById('datos-materias').textContent);
  const aprobadas = JSON.parse(document.getElementById('datos-aprobadas').textContent);
  const seleccion = new Set(JSON.parse(document.getElementById('datos-inscritas').textContent));

  const $lista = document.getElementById('lista-materias');
  const $sel = document.getElementById('seleccion');
  const $total = document.getElementById('total-creditos');
  const $alertas = document.getElementById('alertas');
  const $confirmar = document.getElementById('confirmar');
  const $buscador = document.getElementById('buscador');

  const cumpleRequisitos = (m) => m.requisitos.every((r) => aprobadas.includes(r));
  const hayCupo = (m) => m.inscritos < m.cupo;
  const choca = (a, b) => a.horarios.some((x) => b.horarios.some((y) => x.dia === y.dia && x.ini < y.fin && y.ini < x.fin));
  const conflictoCon = (m) => materias.find((o) => o.id !== m.id && seleccion.has(o.id) && choca(m, o));
  const txtHorario = (m) => m.horarios.map((h) => `${h.dia.slice(0, 3)} ${h.ini}-${h.fin}h`).join(' · ');

  function aviso(msg, tipo = 'danger') {
    $alertas.innerHTML = `<div class="alert alert-${tipo} alert-dismissible fade show">${msg}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button></div>`;
  }

  function alternar(id) {
    const m = materias.find((x) => x.id === id);
    if (seleccion.has(id)) { seleccion.delete(id); return render(); }
    if (!cumpleRequisitos(m)) return aviso(`Te falta cumplir: <strong>${m.requisitos.filter((r) => !aprobadas.includes(r)).join(', ')}</strong>.`);
    if (!hayCupo(m)) return aviso(`El grupo de <strong>${m.nombre}</strong> está lleno.`);
    const c = conflictoCon(m);
    if (c) return aviso(`<strong>${m.nombre}</strong> choca en horario con <strong>${c.nombre}</strong>.`);
    seleccion.add(id); $alertas.innerHTML = ''; render();
  }

  function tarjeta(m) {
    const pct = Math.round((m.inscritos / m.cupo) * 100);
    const lleno = !hayCupo(m), ok = cumpleRequisitos(m), elegida = seleccion.has(m.id);
    const barra = pct >= 95 ? 'bg-danger' : pct >= 75 ? 'bg-warning' : 'bg-success';
    const boton = elegida ? '<button class="btn btn-outline-danger btn-sm">Quitar</button>'
      : lleno ? '<button class="btn btn-secondary btn-sm" disabled>Lleno</button>'
      : !ok ? '<button class="btn btn-secondary btn-sm" disabled>Sin requisitos</button>'
      : '<button class="btn btn-primary btn-sm">Agregar</button>';
    const div = document.createElement('div');
    div.className = `card ${elegida ? 'border-success' : ''}`;
    div.innerHTML = `<div class="card-body">
      <div class="d-flex justify-content-between align-items-start">
        <div><h2 class="h5 mb-0">${m.nombre} <small class="text-muted">${m.clave}</small></h2>
          <div class="text-muted small">${m.profesor} · ${m.creditos} créditos</div>
          <div class="small mt-1">🕒 ${txtHorario(m)}</div>
          ${m.requisitos.length ? `<div class="small ${ok ? 'text-muted' : 'text-danger'}">Requisitos: ${m.requisitos.join(', ')}</div>` : ''}</div>
        ${boton}
      </div>
      <div class="progress mt-3" style="height:8px"><div class="progress-bar ${barra}" style="width:${pct}%"></div></div>
      <div class="small text-muted mt-1">${m.inscritos}/${m.cupo} lugares ocupados</div></div>`;
    div.querySelector('button:not([disabled])')?.addEventListener('click', () => alternar(m.id));
    return div;
  }

  function render() {
    const q = $buscador.value.trim().toLowerCase();
    $lista.replaceChildren(...materias
      .filter((m) => !q || [m.nombre, m.clave, m.profesor].some((t) => t.toLowerCase().includes(q)))
      .map(tarjeta));
    const elegidas = materias.filter((m) => seleccion.has(m.id));
    $sel.innerHTML = elegidas.length
      ? elegidas.map((m) => `<li class="list-group-item small">${m.nombre}<br><span class="text-muted">${txtHorario(m)}</span></li>`).join('')
      : '<li class="list-group-item text-muted small">Nada seleccionado aún.</li>';
    $total.textContent = elegidas.reduce((s, m) => s + m.creditos, 0);
    $confirmar.disabled = elegidas.length === 0;
  }

  $buscador.addEventListener('input', render);
  $confirmar.addEventListener('click', () => aviso('Selección lista. (Pendiente conectar con el backend para guardarla.)', 'success'));
  render();
})();
