<template>
  <div class="planes-comerciales-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Gestión de Planes Comerciales</h1>
        <p class="page-subtitle">Catálogo de precios, periodicidad, límites, módulos y disponibilidad</p>
      </div>
      <div class="header-actions">
        <button type="button" class="btn btn-secondary btn-sm" :disabled="cargando" @click="cargarLista">
          <svg :class="{ spinner: cargando }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
          Actualizar
        </button>
      </div>
    </div>

    <div v-if="error" class="alert alert-danger" role="alert">
      {{ error }}
    </div>

    <div class="card">
      <div class="card-header">
        <h2 class="card-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
          Catálogo de Planes ({{ total }})
        </h2>
      </div>

      <div class="card-body">
        <div class="filter-bar">
          <div class="search-input-wrapper">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input
              v-model="busqueda"
              type="text"
              class="form-input"
              placeholder="Buscar por nombre de plan…"
              @input="onBusquedaInput"
            />
          </div>

          <select v-model="estadoFiltro" class="form-select filtro-select" aria-label="Filtrar por disponibilidad">
            <option v-for="opcion in opcionesEstado" :key="opcion.valor" :value="opcion.valor">{{ opcion.etiqueta }}</option>
          </select>

          <button
            v-if="tieneFiltros"
            type="button"
            class="btn btn-outline btn-sm"
            @click="limpiarFiltros"
          >
            Limpiar filtros
          </button>
        </div>

        <div v-if="cargando" class="empty-state">
          <div class="spinner spinner-primary" style="margin: 0 auto 0.5rem;"></div>
          <span class="text-muted">Cargando catálogo de planes comerciales…</span>
        </div>

        <div v-else-if="planes.length === 0" class="empty-state">
          <div class="empty-state-icon">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
          </div>
          <div class="empty-state-title">Sin planes comerciales</div>
          <p class="empty-state-text">No hay planes que coincidan con la búsqueda o los filtros aplicados.</p>
        </div>

        <div v-else class="planes-grid">
          <div
            v-for="plan in planes"
            :key="plan.id"
            class="card plan-card"
            @click="abrirDetalle(plan)"
          >
            <div class="plan-card-top">
              <div>
                <h3 class="plan-name">{{ plan.nombre }}</h3>
                <span class="badge badge-indigo">Plan ID #{{ plan.id }}</span>
              </div>
              <span class="badge" :class="plan.disponible ? 'badge-success' : 'badge-neutral'">
                {{ plan.disponible ? 'Disponible' : 'No disponible' }}
              </span>
            </div>

            <p class="plan-precio">
              <template v-if="plan.precio !== null && plan.precio !== undefined">
                {{ formatearMoneda(plan.precio) }}
              </template>
              <template v-else-if="plan.precios && plan.precios.length > 0">
                {{ formatearMoneda(plan.precios[0].importe) }}
              </template>
              <template v-else>Sin precio</template>
              <span class="plan-periodicidad" v-if="plan.periodicidad">/ {{ plan.periodicidad }}</span>
            </p>

            <div class="plan-meta">
              <div>
                <span class="text-xs text-muted">Límite de alumnos</span>
                <strong>{{ plan.limiteAlumnos ?? 'Ilimitado' }}</strong>
              </div>
              <div>
                <span class="text-xs text-muted">Planteles permitidos</span>
                <strong>{{ plan.plantelesPermitidos ?? 'Ilimitado' }}</strong>
              </div>
              <div>
                <span class="text-xs text-muted">Módulos</span>
                <strong>{{ plan.modulos?.length || 0 }}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Detalle del Plan Comercial -->
    <div v-if="planSeleccionado" class="modal-backdrop" @click="planSeleccionado = null">
      <div class="modal-box" @click.stop>
        <div class="modal-header">
          <div>
            <h3 class="modal-title">{{ planSeleccionado.nombre }}</h3>
            <span class="font-mono text-xs text-muted">Plan ID #{{ planSeleccionado.id }}</span>
          </div>
          <button type="button" class="modal-close-btn" aria-label="Cerrar" @click="planSeleccionado = null">×</button>
        </div>

        <div class="modal-body">
          <div class="stats-mini-grid">
            <div class="stat-mini">
              <span class="stat-mini-label">Precio</span>
              <strong class="stat-mini-val">{{ formatearMoneda(planSeleccionado.precio ?? planSeleccionado.precios?.[0]?.importe) }}</strong>
            </div>
            <div class="stat-mini">
              <span class="stat-mini-label">Periodicidad</span>
              <strong class="stat-mini-val">{{ planSeleccionado.periodicidad || '—' }}</strong>
            </div>
            <div class="stat-mini">
              <span class="stat-mini-label">Límite alumnos</span>
              <strong class="stat-mini-val">{{ planSeleccionado.limiteAlumnos ?? 'Ilimitado' }}</strong>
            </div>
            <div class="stat-mini">
              <span class="stat-mini-label">Planteles</span>
              <strong class="stat-mini-val">{{ planSeleccionado.plantelesPermitidos ?? 'Ilimitado' }}</strong>
            </div>
          </div>

          <div class="detail-section">
            <h5 class="detail-subtitle">Módulos Disponibles</h5>
            <div v-if="planSeleccionado.modulos?.length" class="ids-wrap">
              <span v-for="modulo in planSeleccionado.modulos" :key="modulo" class="badge badge-indigo">
                {{ modulo }}
              </span>
            </div>
            <p v-else class="text-sm text-muted">Sin módulos adicionales registrados.</p>
          </div>

          <div class="detail-section">
            <h5 class="detail-subtitle">Estado de Disponibilidad</h5>
            <span class="badge" :class="planSeleccionado.disponible ? 'badge-success' : 'badge-warning'">
              {{ planSeleccionado.disponible ? 'Disponible' : 'No disponible' }}
            </span>
          </div>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary btn-sm" @click="planSeleccionado = null">Cerrar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { usePlanesComerciales } from '../composables/usePlanesComerciales';

const {
  planes,
  total,
  cargando,
  error,
  paginaActual,
  cargarPlanes: cargarPlanesListado,
} = usePlanesComerciales();

const busqueda = ref('');
const estadoFiltro = ref('');

const planSeleccionado = ref(null);

const opcionesEstado = [
  { valor: '', etiqueta: 'Todos los estados' },
  { valor: 'ACTIVO', etiqueta: 'Disponible' },
  { valor: 'INACTIVO', etiqueta: 'No disponible' },
];

const tieneFiltros = computed(() => Boolean(busqueda.value.trim() || estadoFiltro.value));

let debounceTimeout = null;

function onBusquedaInput() {
  clearTimeout(debounceTimeout);
  debounceTimeout = setTimeout(() => {
    cargarLista();
  }, 350);
}

async function cargarLista() {
  await cargarPlanesListado(paginaActual.value, {
    ...(busqueda.value.trim() ? { search: busqueda.value.trim() } : {}),
    ...(estadoFiltro.value ? { estado: estadoFiltro.value } : {}),
  });
}

function limpiarFiltros() {
  busqueda.value = '';
  estadoFiltro.value = '';
  cargarLista();
}

function formatearMoneda(monto) {
  try {
    return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(monto) || 0);
  } catch (_) {
    return `${Number(monto || 0).toFixed(2)} MXN`;
  }
}

onMounted(() => {
  cargarLista();
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

.header-actions {
  display: flex;
  gap: 0.65rem;
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.85rem;
  margin-bottom: 1.25rem;
}

.filtro-select {
  width: auto;
  min-width: 150px;
}

.planes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.25rem;
}

.plan-card {
  padding: 1.25rem;
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.plan-card:hover {
  border-color: var(--primary-border);
  transform: translateY(-2px);
}

.plan-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.plan-name {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 0.25rem;
}

.plan-precio {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--text-main);
  margin-bottom: 0.75rem;
}

.plan-periodicidad {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-muted);
}

.plan-meta {
  display: flex;
  gap: 1.5rem;
  border-top: 1px solid var(--border-subtle);
  padding-top: 0.75rem;
}

.plan-meta > div {
  display: flex;
  flex-direction: column;
}

/* Modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(15, 23, 42, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-box {
  background: var(--bg-card);
  border-radius: var(--radius-md);
  width: 100%;
  max-width: 520px;
  box-shadow: var(--shadow-xl);
  overflow: hidden;
  animation: modalEnter 0.2s ease-out;
}

@keyframes modalEnter {
  from { opacity: 0; transform: scale(0.96); }
  to { opacity: 1; transform: scale(1); }
}

.modal-header {
  padding: 1.15rem 1.5rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-main);
}

.modal-close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--text-light);
  cursor: pointer;
}

.modal-close-btn:hover {
  color: var(--text-main);
}

.modal-body {
  padding: 1.5rem;
}

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border);
  background-color: var(--bg-main);
  display: flex;
  justify-content: flex-end;
}

.stats-mini-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
  margin-bottom: 1.25rem;
}

.stat-mini {
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.5rem;
  text-align: center;
}

.stat-mini-label {
  display: block;
  font-size: 0.65rem;
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: 600;
}

.stat-mini-val {
  font-size: 1.1rem;
  font-family: 'JetBrains Mono', monospace;
  color: var(--primary);
}

.detail-section {
  margin-top: 1rem;
  border-top: 1px solid var(--border-subtle);
  padding-top: 0.75rem;
}

.detail-subtitle {
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 0.4rem;
}

.ids-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.font-mono {
  font-family: 'JetBrains Mono', monospace;
}

.font-bold {
  font-weight: 700;
}

.text-center {
  text-align: center;
}

.text-muted {
  color: var(--text-muted);
}

.text-xs {
  font-size: 0.75rem;
}

.text-sm {
  font-size: 0.875rem;
}

@media (max-width: 640px) {
  .stats-mini-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
