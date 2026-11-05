<template>
  <div class="alumno-inscripcion-page">
    <header class="ui-page-header">
      <div>
        <h1 class="ui-large-title">Simulador y pre-inscripción de materias</h1>
        <p class="ui-page-subtitle">
          Explora la oferta académica, verifica prerrequisitos y detecta cruces de horario en tiempo real
        </p>
      </div>
      <div class="ui-page-actions">
        <button
          type="button"
          class="btn btn-secondary btn-sm"
          :disabled="cargando"
          @click="cargarCatalogo"
        >
          <AppIcon name="refresh" :size="14" :class="{ girando: cargando }" />
          Actualizar catálogo
        </button>
      </div>
    </header>

    <ErrorBanner
      v-if="errorMsg"
      titulo="No pudimos cargar el catálogo"
      :mensaje="errorMsg"
      :cargando="cargando"
      @reintentar="cargarCatalogo"
    />

    <!-- Conflictos de horario (D5): icono + lista de choques -->
    <div v-if="conflictos.length > 0" class="alert alert-danger conflict-alert" role="status" aria-live="polite">
      <AppIcon name="warning" :size="20" class="conflict-icon" />
      <div>
        <strong>Conflicto de horario</strong>
        <p>Estas materias se imparten a la misma hora. Quita una de cada par para continuar.</p>
        <ul class="conflict-list">
          <li v-for="(conf, cIdx) in conflictos" :key="cIdx">
            <strong>{{ conf[0].nombre }}</strong> y <strong>{{ conf[1].nombre }}</strong>
            <span class="conflict-when">· {{ detalleChoque(conf[0], conf[1]) }}</span>
          </li>
        </ul>
      </div>
    </div>

    <!-- Carga: esqueleto (A9) -->
    <div v-if="cargando && !materias.length" class="simulador-layout" aria-busy="true" aria-label="Cargando catálogo">
      <div class="ui-grouped">
        <div v-for="n in 5" :key="n" class="ui-row">
          <div class="skeleton skel-circle"></div>
          <div class="ui-row-main">
            <div class="skeleton ui-skel-line" style="width: 40%"></div>
            <div class="skeleton ui-skel-line" style="width: 65%"></div>
          </div>
        </div>
      </div>
      <div class="card"><div class="card-body"><div class="skeleton" style="height: 180px"></div></div></div>
    </div>

    <div v-else class="simulador-layout">
      <!-- Columna principal: catálogo -->
      <section class="catalogo-col">
        <div class="catalogo-toolbar">
          <h2 class="ui-section-title catalogo-title">
            <span>
              Oferta curricular
              <span class="ui-section-count">{{ materiasFiltradas.length }}</span>
            </span>
          </h2>
          <!-- Búsqueda (D4) -->
          <div class="ui-search catalogo-search" role="search">
            <AppIcon name="search" :size="16" class="ui-search-icon" />
            <input
              v-model="busqueda"
              type="search"
              placeholder="Buscar materia o clave"
              aria-label="Buscar materia o clave"
            />
            <button
              v-if="busqueda"
              type="button"
              class="ui-search-clear"
              aria-label="Borrar búsqueda"
              @click="busqueda = ''"
            >
              <AppIcon name="x-circle" :size="16" />
            </button>
          </div>
        </div>

        <div class="ui-grouped">
          <!-- Sin resultados -->
          <div v-if="materiasFiltradas.length === 0" class="ui-empty">
            <div class="ui-empty-icon"><AppIcon name="search" :size="24" /></div>
            <template v-if="busqueda">
              <h3 class="ui-empty-title">Sin resultados</h3>
              <p class="ui-empty-text">No encontramos materias para “{{ busqueda }}”.</p>
              <button type="button" class="btn btn-secondary btn-sm" @click="busqueda = ''">Limpiar búsqueda</button>
            </template>
            <p v-else class="ui-empty-text">No hay materias disponibles en tu plan por ahora.</p>
          </div>

          <!-- Filas seleccionables completas (D1 / D2) -->
          <div
            v-for="m in materiasFiltradas"
            :key="m.id"
            class="ui-row materia-row"
            :class="{
              'is-selected': seleccion.has(m.id),
              'is-blocked': bloqueada(m),
              'is-conflict': idsEnConflicto.has(m.id),
            }"
            role="checkbox"
            tabindex="0"
            :aria-checked="seleccion.has(m.id) ? 'true' : 'false'"
            :aria-disabled="bloqueada(m) ? 'true' : undefined"
            @click="toggle(m)"
            @keydown.space.prevent="toggle(m)"
            @keydown.enter.prevent="toggle(m)"
          >
            <span class="select-circle" aria-hidden="true">
              <AppIcon v-if="bloqueada(m)" name="lock" :size="13" />
              <AppIcon v-else-if="seleccion.has(m.id)" name="check" :size="14" :stroke-width="3" />
            </span>

            <div class="ui-row-main">
              <div class="ui-row-title">{{ m.nombre }}</div>
              <div class="ui-row-subtitle">
                <span class="ui-code">{{ m.clave }}</span> · {{ m.creditos }} créditos · Semestre {{ m.semestre }}
              </div>

              <!-- Prerrequisitos: icono + texto, no solo color (D3) -->
              <div v-if="faltantesNombres(m).length" class="mat-note note-blocked">
                <AppIcon name="lock" :size="13" />
                Primero acredita {{ listaHumana(faltantesNombres(m)) }}
              </div>
              <div v-else-if="m.requisitos && m.requisitos.length" class="mat-note note-ok">
                <AppIcon name="check-circle" :size="13" />
                Requisitos cumplidos: {{ listaHumana(m.requisitos) }}
              </div>
              <div v-if="!hayCupo(m)" class="mat-note note-blocked">
                <AppIcon name="alert" :size="13" />
                Sin cupo disponible
              </div>

              <div v-if="m.horarios && m.horarios.length" class="mat-note">
                <AppIcon name="clock" :size="13" />
                <span class="ui-num">{{ horariosTexto(m) }}</span>
              </div>

              <div v-if="idsEnConflicto.has(m.id)" class="mat-note note-conflict">
                <AppIcon name="warning" :size="13" />
                Se cruza con {{ listaHumana(idsEnConflicto.get(m.id)) }}
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Columna lateral: resumen -->
      <aside class="resumen-col">
        <div class="card sticky-panel">
          <div class="card-header">
            <h3 class="card-title">
              <AppIcon name="select-list" />
              Tu pre-selección ({{ seleccion.size }})
            </h3>
          </div>

          <div class="card-body">
            <!-- Estado vacío (D7) -->
            <div v-if="seleccion.size === 0" class="ui-empty resumen-empty">
              <div class="ui-empty-icon"><AppIcon name="layers" :size="22" /></div>
              <p class="ui-empty-title">Aún no eliges materias</p>
              <p class="ui-empty-text">Toca una materia de la lista para agregarla aquí.</p>
            </div>

            <div v-else class="ui-grouped selected-list">
              <div v-for="m in seleccionMaterias" :key="m.id" class="ui-row">
                <div class="ui-row-main">
                  <div class="ui-row-title">{{ m.nombre }}</div>
                  <div class="ui-row-subtitle">{{ m.creditos }} créditos</div>
                </div>
                <button
                  type="button"
                  class="btn-remove"
                  :aria-label="`Quitar ${m.nombre}`"
                  @click="quitarMateria(m.id)"
                >
                  <AppIcon name="x" :size="16" />
                </button>
              </div>
            </div>

            <div class="selection-totals">
              <div class="total-row">
                <span>Materias elegidas</span>
                <strong class="ui-num">{{ seleccion.size }}</strong>
              </div>
              <div class="total-row">
                <span>Total de créditos</span>
                <strong class="ui-num total-creditos">{{ totalCreditos }} créditos</strong>
              </div>
            </div>

            <button
              type="button"
              class="btn btn-primary btn-lg submit-selection-btn"
              :disabled="!puedeConfirmar"
              @click="sheetAbierta = true"
            >
              Simular inscripción válida
            </button>
            <p v-if="conflictos.length > 0" class="submit-hint">Resuelve los cruces de horario para continuar.</p>
          </div>
        </div>
      </aside>
    </div>

    <!-- Hoja de confirmación (D6) -->
    <ConfirmSheet
      :abierto="sheetAbierta"
      titulo="Confirmar simulación"
      descripcion="Revisa tu selección antes de simular la inscripción."
      texto-confirmar="Confirmar"
      @cancelar="sheetAbierta = false"
      @confirmar="confirmarSimulacion"
    >
      <div class="ui-grouped sheet-list">
        <div v-for="m in seleccionMaterias" :key="m.id" class="ui-row">
          <div class="ui-row-main">
            <div class="ui-row-title">{{ m.nombre }}</div>
            <div class="ui-row-subtitle"><span class="ui-code">{{ m.clave }}</span> · Semestre {{ m.semestre }}</div>
          </div>
          <span class="ui-row-value">{{ m.creditos }} créditos</span>
        </div>
        <div class="ui-row sheet-total">
          <span class="ui-row-label">Total</span>
          <span class="ui-row-value">{{ seleccion.size }} materias · {{ totalCreditos }} créditos</span>
        </div>
      </div>
      <p class="sheet-note">
        <AppIcon name="check-circle" :size="14" />
        Sin cruces de horario ni prerrequisitos pendientes.
      </p>
    </ConfirmSheet>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import api, { obtenerMensajeError } from '../../../api';
import { useAuthStore } from '../../../stores/auth';
import { useNotificationStore } from '../../../stores/notification';
import AppIcon from '../../../components/AppIcon.vue';
import ErrorBanner from '../../../components/ErrorBanner.vue';
import ConfirmSheet from '../../../components/ConfirmSheet.vue';

const authStore = useAuthStore();
const notifStore = useNotificationStore();

const materias = ref([]);
const cargando = ref(false);
const errorMsg = ref(null);
const busqueda = ref('');
const seleccion = ref(new Set());
const sheetAbierta = ref(false);

const alumno = computed(() => authStore.alumno);
const aprobadasIds = computed(() => alumno.value?.materias_aprobadas_ids || []);

const materiasFiltradas = computed(() => {
  const q = busqueda.value.trim().toLowerCase();
  if (!q) return materias.value;
  return materias.value.filter(
    (m) => m.nombre.toLowerCase().includes(q) || m.clave.toLowerCase().includes(q),
  );
});

function faltantes(m) {
  if (!aprobadasIds.value) return [];
  return (m.requisitosIds || []).filter((id) => !aprobadasIds.value.includes(id));
}

function esRequisitoFaltante(m, reqIdx) {
  const reqId = m.requisitosIds?.[reqIdx];
  return reqId && !aprobadasIds.value.includes(reqId);
}

function faltantesNombres(m) {
  return (m.requisitos || []).filter((_, idx) => esRequisitoFaltante(m, idx));
}

function hayCupo(m) {
  return m.cupo == null || (m.inscritos ?? 0) < m.cupo;
}

// Franjas que se empalman entre dos materias
function choques(a, b) {
  const res = [];
  (a.horarios || []).forEach((x) => {
    (b.horarios || []).forEach((y) => {
      if (x.dia === y.dia && x.inicio < y.fin && y.inicio < x.fin) res.push({ x, y });
    });
  });
  return res;
}

function choca(a, b) {
  return choques(a, b).length > 0;
}

function detalleChoque(a, b) {
  const [primero] = choques(a, b);
  if (!primero) return '';
  const inicio = Math.max(primero.x.inicio, primero.y.inicio);
  return `${primero.x.dia} a las ${inicio}:00`;
}

const seleccionMaterias = computed(() =>
  materias.value.filter((m) => seleccion.value.has(m.id)),
);

const conflictos = computed(() => {
  const sel = seleccionMaterias.value.filter((m) => (m.horarios || []).length > 0);
  const res = [];
  for (let i = 0; i < sel.length; i++) {
    for (let j = i + 1; j < sel.length; j++) {
      if (choca(sel[i], sel[j])) {
        res.push([sel[i], sel[j]]);
      }
    }
  }
  return res;
});

// id de materia → nombres de las materias con las que se cruza
const idsEnConflicto = computed(() => {
  const mapa = new Map();
  conflictos.value.forEach(([a, b]) => {
    mapa.set(a.id, [...(mapa.get(a.id) || []), b.nombre]);
    mapa.set(b.id, [...(mapa.get(b.id) || []), a.nombre]);
  });
  return mapa;
});

const totalCreditos = computed(() =>
  seleccionMaterias.value.reduce((s, m) => s + (m.creditos || 0), 0),
);

function horariosTexto(m) {
  return (m.horarios || []).map((h) => `${h.dia} ${h.inicio}:00–${h.fin}:00`).join(' · ');
}

function listaHumana(nombres = []) {
  if (nombres.length <= 1) return nombres.join('');
  return `${nombres.slice(0, -1).join(', ')} y ${nombres[nombres.length - 1]}`;
}

function puedeInscribir(m) {
  return faltantes(m).length === 0 && hayCupo(m);
}

function bloqueada(m) {
  return !puedeInscribir(m) && !seleccion.value.has(m.id);
}

const puedeConfirmar = computed(() => {
  return seleccion.value.size > 0 && conflictos.value.length === 0 && totalCreditos.value > 0;
});

function toggle(m) {
  if (seleccion.value.has(m.id)) {
    seleccion.value.delete(m.id);
    return;
  }
  if (!puedeInscribir(m)) return;
  seleccion.value.add(m.id);
}

function quitarMateria(id) {
  seleccion.value.delete(id);
}

function confirmarSimulacion() {
  if (!puedeConfirmar.value) return;
  sheetAbierta.value = false;
  notifStore.success(`Simulación válida: ${seleccion.value.size} materias sin cruces de horario.`);
}

async function cargarCatalogo() {
  cargando.value = true;
  errorMsg.value = null;

  try {
    const planId = alumno.value?.plan_estudios;
    const [rNodos, rStats] = await Promise.all([
      api.get('/nodos/', { params: planId ? { plan_estudios: planId } : {} }),
      api.get('/estadisticas-nodos/'),
    ]);

    const nodos = Array.isArray(rNodos.data) ? rNodos.data : (rNodos.data?.results ?? []);
    const stats = Array.isArray(rStats.data) ? rStats.data : (rStats.data?.results ?? []);
    const statsPorNodo = new Map(stats.map((e) => [e.nodo, e]));

    materias.value = nodos.map((n) => ({
      id: n.id,
      clave: n.clave,
      nombre: n.nombre,
      creditos: n.creditos,
      semestre: n.semestre,
      requisitosIds: n.prerrequisitos || [],
      requisitos: (n.prerrequisitos || []).map((id) => nodos.find((x) => x.id === id)?.nombre || `#${id}`),
      inscritos: statsPorNodo.get(n.id)?.alumnos_inscritos ?? null,
      cupo: n.cupo ?? null,
      profesor: n.profesor ?? null,
      horarios: n.horarios ?? [],
    }));
  } catch (e) {
    errorMsg.value = obtenerMensajeError(e);
  } finally {
    cargando.value = false;
  }
}

onMounted(() => {
  cargarCatalogo();
});
</script>

<style scoped>
.simulador-layout {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 1.5rem;
  align-items: start;
}

/* Conflictos */
.conflict-alert {
  align-items: flex-start;
}

.conflict-icon {
  flex-shrink: 0;
  margin-top: 1px;
}

.conflict-alert p {
  margin-top: 0.15rem;
}

.conflict-list {
  margin: 0.5rem 0 0;
  padding-left: 1.1rem;
}

.conflict-when {
  opacity: 0.85;
}

/* Barra del catálogo */
.catalogo-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.6rem;
}

.catalogo-title {
  margin: 0;
}

.catalogo-search {
  flex: 0 1 280px;
}

/* Fila de materia seleccionable */
.materia-row {
  --ui-separator-inset: 3.35rem;
  align-items: flex-start;
  padding-block: 0.9rem;
  cursor: pointer;
  outline: none;
  transition: background-color 0.15s ease;
}

.materia-row:hover {
  background-color: var(--row-hover);
}

.materia-row:focus-visible {
  box-shadow: inset 0 0 0 2px var(--focus-ring);
}

.materia-row.is-selected {
  background-color: var(--primary-light);
}

.materia-row.is-blocked {
  cursor: not-allowed;
}

.materia-row.is-blocked .ui-row-title,
.materia-row.is-blocked .ui-row-subtitle {
  opacity: 0.6;
}

.materia-row.is-conflict {
  background-color: var(--danger-bg);
}

/* Casilla circular (estilo Recordatorios) */
.select-circle {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  margin-top: 1px;
  border-radius: 50%;
  border: 2px solid var(--border-strong);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--on-accent);
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.materia-row:hover:not(.is-blocked) .select-circle {
  border-color: var(--accent-text);
}

.is-selected .select-circle {
  background-color: var(--accent);
  border-color: var(--accent);
}

.is-blocked .select-circle {
  border-style: dashed;
  color: var(--text-light);
}

.mat-note {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin-top: 0.35rem;
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.note-ok { color: var(--success-text); }
.note-blocked { color: var(--danger-text); font-weight: 600; }
.note-conflict { color: var(--danger-text); font-weight: 600; }

.skel-circle {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* Panel lateral */
.sticky-panel {
  position: sticky;
  top: calc(64px + 1.5rem);
}

.resumen-empty {
  padding: 1rem 0.5rem 1.25rem;
}

.selected-list {
  background-color: var(--bg-surface);
  border-color: transparent;
}

.btn-remove {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--text-light);
  cursor: pointer;
}

.btn-remove:hover {
  color: var(--danger);
  background-color: var(--danger-bg);
}

.selection-totals {
  margin: 1.1rem 0;
  padding-top: 1rem;
  border-top: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.total-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.9375rem;
  color: var(--text-muted);
}

.total-row strong {
  color: var(--text-main);
}

.total-creditos {
  color: var(--accent-text) !important;
}

.submit-selection-btn {
  width: 100%;
  min-height: 50px;
  border-radius: 12px;
}

.submit-hint {
  margin-top: 0.6rem;
  font-size: 0.8125rem;
  text-align: center;
  color: var(--danger-text);
}

/* Hoja de confirmación */
.sheet-list {
  background-color: var(--bg-surface);
  border-color: transparent;
}

.sheet-total .ui-row-label {
  font-weight: 700;
}

.sheet-total .ui-row-value {
  color: var(--text-main);
}

.sheet-note {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  margin-top: 0.85rem;
  font-size: 0.8125rem;
  color: var(--success-text);
}

.girando {
  animation: spin 0.8s linear infinite;
}

@media (max-width: 1024px) {
  .simulador-layout {
    grid-template-columns: 1fr;
  }
  .sticky-panel {
    position: static;
  }
}
</style>
