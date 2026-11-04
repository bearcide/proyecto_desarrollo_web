<template>
  <div class="alumno-inscripcion-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Simulador y Pre-inscripción de Materias</h1>
        <p class="page-subtitle">
          Explora la oferta académica, verifica prerrequisitos y detecta cruces de horario en tiempo real
        </p>
      </div>
      <div class="header-actions">
        <button
          type="button"
          class="btn btn-secondary btn-sm"
          :disabled="cargando"
          @click="cargarCatalogo"
        >
          <svg :class="{ spinner: cargando }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
          Actualizar catálogo
        </button>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="errorMsg" class="alert alert-danger" role="alert">
      {{ errorMsg }}
    </div>

    <!-- Alerta de Conflictos Detectados en Vivo -->
    <div v-if="conflictos.length > 0" class="alert alert-danger" role="alert">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      <div>
        <strong>Conflicto de Horario Detectado</strong>
        <p class="text-sm">
          Las siguientes materias se empalman en el mismo día y franja horaria:
          <span v-for="(conf, cIdx) in conflictos" :key="cIdx" class="conf-pill">
            {{ conf[0].nombre }} ⚔ {{ conf[1].nombre }}
          </span>
        </p>
      </div>
    </div>

    <div v-if="cargando && !materias.length" class="empty-state">
      <div class="spinner spinner-primary" style="margin: 0 auto 0.5rem;"></div>
      <span class="text-muted">Cargando catálogo curricular…</span>
    </div>

    <div v-else class="simulador-layout">
      <!-- Columna Principal: Catálogo Curricular -->
      <div class="catalogo-col">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/></svg>
              Oferta Curricular ({{ materiasFiltradas.length }})
            </h2>
            <div class="filter-controls">
              <input
                v-model="busqueda"
                type="text"
                class="form-input form-input-sm"
                placeholder="Buscar materia o clave…"
              />
            </div>
          </div>

          <div class="card-body">
            <div class="materias-cards-list">
              <div
                v-for="m in materiasFiltradas"
                :key="m.id"
                class="materia-card-row"
                :class="{
                  'materia-selected': seleccion.has(m.id),
                  'materia-disabled': !puedeInscribir(m) && !seleccion.has(m.id),
                }"
              >
                <div class="mat-details">
                  <div class="mat-title-wrap">
                    <strong class="mat-name">{{ m.nombre }}</strong>
                    <span class="font-mono text-xs badge badge-neutral">{{ m.clave }}</span>
                    <span class="badge badge-indigo text-xs">{{ m.creditos }} créditos</span>
                    <span class="badge badge-neutral text-xs">Sem {{ m.semestre }}</span>
                  </div>

                  <!-- Prerrequisitos -->
                  <div v-if="m.requisitos && m.requisitos.length" class="mat-meta text-xs">
                    <span>Requiere: </span>
                    <span
                      v-for="(req, rIdx) in m.requisitos"
                      :key="rIdx"
                      :class="esRequisitoFaltante(m, rIdx) ? 'text-danger font-bold' : 'text-success font-medium'"
                    >
                      {{ req }}{{ rIdx < m.requisitos.length - 1 ? ', ' : '' }}
                    </span>
                  </div>

                  <!-- Horarios -->
                  <div v-if="m.horarios && m.horarios.length" class="mat-horarios font-mono text-xs text-muted">
                    🕒 {{ horariosTexto(m) }}
                  </div>
                </div>

                <div class="mat-action">
                  <button
                    type="button"
                    class="btn btn-sm"
                    :class="seleccion.has(m.id) ? 'btn-danger' : 'btn-outline'"
                    :disabled="!puedeInscribir(m) && !seleccion.has(m.id)"
                    @click="toggle(m)"
                  >
                    {{ seleccion.has(m.id) ? 'Quitar' : 'Seleccionar' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Columna Lateral: Resumen de Selección y Créditos -->
      <div class="resumen-col">
        <div class="card sticky-panel">
          <div class="card-header">
            <h3 class="card-title">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
              Tu Pre-selección ({{ seleccion.size }})
            </h3>
          </div>

          <div class="card-body">
            <div v-if="seleccion.size === 0" class="empty-state" style="padding: 1.5rem 1rem;">
              <p class="text-sm text-muted">Aún no has agregado materias a tu selección.</p>
            </div>

            <div v-else class="selected-items-list">
              <div
                v-for="id in [...seleccion]"
                :key="id"
                class="selected-item-row"
              >
                <div>
                  <strong class="text-sm">{{ materiaNombre(id) }}</strong>
                  <div class="text-xs text-muted font-mono">{{ materiaCreditos(id) }} créditos</div>
                </div>
                <button
                  type="button"
                  class="btn-remove-sm"
                  title="Quitar materia"
                  @click="quitarMateria(id)"
                >
                  ✕
                </button>
              </div>
            </div>

            <div class="selection-totals">
              <div class="total-row">
                <span class="text-sm text-muted">Materias elegidas:</span>
                <strong class="font-mono">{{ seleccion.size }}</strong>
              </div>
              <div class="total-row">
                <span class="text-sm text-muted">Total de créditos:</span>
                <strong class="font-mono text-primary text-base">{{ totalCreditos }} cred.</strong>
              </div>
            </div>

            <button
              type="button"
              class="btn btn-primary btn-lg w-full submit-selection-btn"
              :disabled="!puedeConfirmar"
              @click="confirmarSimulacion"
            >
              Simular Inscripción Válida
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import api, { obtenerMensajeError } from '../../../api';
import { useAuthStore } from '../../../stores/auth';
import { useNotificationStore } from '../../../stores/notification';
import {
  cumpleRequisitos,
  hayCupoDisponible,
  hayConflictoHorario,
  evaluarSolicitudInscripcion,
} from '../../../domain/ValidadorInscripcion';

const authStore = useAuthStore();
const notifStore = useNotificationStore();

const materias = ref([]);
const cargando = ref(false);
const errorMsg = ref(null);
const busqueda = ref('');
const seleccion = ref(new Set());

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

function hayCupo(m) {
  return m.cupo == null || (m.inscritos ?? 0) < m.cupo;
}

function choca(a, b) {
  return (a.horarios || []).some((x) =>
    (b.horarios || []).some((y) => x.dia === y.dia && x.inicio < y.fin && y.inicio < x.fin),
  );
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

const totalCreditos = computed(() =>
  seleccionMaterias.value.reduce((s, m) => s + (m.creditos || 0), 0),
);

function horariosTexto(m) {
  return (m.horarios || []).map((h) => `${h.dia} ${h.inicio}:00-${h.fin}:00`).join(', ');
}

function materiaNombre(id) {
  return materias.value.find((m) => m.id === id)?.nombre || `Materia #${id}`;
}

function materiaCreditos(id) {
  return materias.value.find((m) => m.id === id)?.creditos || 0;
}

function puedeInscribir(m) {
  return faltantes(m).length === 0 && hayCupo(m);
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
  notifStore.success(`¡Simulación válida! ${seleccion.value.size} materias sin conflictos horarios.`);
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
.page-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--text-main);
}

.page-subtitle {
  font-size: 0.875rem;
  color: var(--text-muted);
}

.conf-pill {
  display: inline-block;
  background: rgba(0, 0, 0, 0.08);
  padding: 0.15rem 0.4rem;
  border-radius: var(--radius-sm);
  margin-left: 0.35rem;
  font-weight: 700;
}

.simulador-layout {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 1.5rem;
  align-items: start;
}

.form-input-sm {
  padding: 0.45rem 0.75rem;
  font-size: 0.8125rem;
  width: 220px;
}

.materias-cards-list {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.materia-card-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.9rem 1.15rem;
  background-color: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  transition: all 0.15s ease;
}

.materia-card-row:hover {
  border-color: var(--primary-border);
}

.materia-selected {
  background-color: var(--primary-light);
  border-color: var(--primary);
  border-left: 4px solid var(--primary);
}

.materia-disabled {
  opacity: 0.65;
  background-color: var(--bg-surface);
}

.mat-details {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  flex: 1;
}

.mat-title-wrap {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.mat-name {
  font-size: 0.95rem;
  color: var(--text-main);
}

.sticky-panel {
  position: sticky;
  top: 80px;
}

.selected-items-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
}

.selected-item-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.btn-remove-sm {
  background: none;
  border: none;
  color: var(--danger);
  cursor: pointer;
  font-size: 1rem;
  padding: 0 0.25rem;
  line-height: 1;
}

.selection-totals {
  border-top: 1px solid var(--border);
  padding-top: 0.85rem;
  margin-bottom: 1.15rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.w-full {
  width: 100%;
}

.font-mono {
  font-family: 'JetBrains Mono', monospace;
}

.font-bold {
  font-weight: 700;
}

.font-medium {
  font-weight: 600;
}

.text-xs {
  font-size: 0.75rem;
}

.text-sm {
  font-size: 0.875rem;
}

.text-base {
  font-size: 1rem;
}

.text-primary {
  color: var(--primary);
}

.text-danger {
  color: var(--danger);
}

.text-success {
  color: var(--success);
}

.text-muted {
  color: var(--text-muted);
}

@media (max-width: 900px) {
  .simulador-layout {
    grid-template-columns: 1fr;
  }
}
</style>
