<template>
  <div class="clientes-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Administración de Clientes</h1>
        <p class="page-subtitle">Escuelas contratantes del SaaS y su contexto comercial</p>
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
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
          Instituciones Contratantes ({{ total }})
        </h2>
      </div>

      <div class="card-body">
        <!-- Filtros: búsqueda + estado + plan -->
        <div class="filter-bar">
          <div class="search-input-wrapper">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input
              v-model="busqueda"
              type="text"
              class="form-input"
              placeholder="Buscar por nombre de institución…"
              @input="onBusquedaInput"
            />
          </div>

          <select v-model="estadoFiltro" class="form-select filtro-select" aria-label="Filtrar por estado">
            <option v-for="opcion in opcionesEstado" :key="opcion.valor" :value="opcion.valor">{{ opcion.etiqueta }}</option>
          </select>

          <select v-model="planFiltro" class="form-select filtro-select" aria-label="Filtrar por plan contratante">
            <option value="">Todos los planes</option>
            <option v-for="plan in planes" :key="plan.id" :value="plan.nombre">{{ plan.nombre }}</option>
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
          <span class="text-muted">Cargando instituciones contratantes…</span>
        </div>

        <div v-else-if="clientes.length === 0" class="empty-state">
          <div class="empty-state-icon">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
          </div>
          <div class="empty-state-title">Sin instituciones encontradas</div>
          <p class="empty-state-text">No hay escuelas que coincidan con la búsqueda o los filtros aplicados.</p>
        </div>

        <div v-else class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Institución</th>
                <th>Plan Contratante</th>
                <th>Estado</th>
                <th>Detalle</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="cliente in clientes"
                :key="cliente.id"
                class="cliente-row"
                @click="abrirDetalle(cliente)"
              >
                <td>
                  <strong>{{ cliente.nombre }}</strong>
                  <div class="text-xs text-muted font-mono">{{ cliente.id }}</div>
                </td>
                <td>
                  <span class="badge badge-indigo" v-if="cliente.plan">{{ cliente.plan }}</span>
                  <span class="badge badge-neutral" v-else>Sin plan</span>
                </td>
                <td>
                  <span class="badge" :class="cliente.estado === 'ACTIVO' ? 'badge-success' : 'badge-warning'">
                    {{ etiqueta(cliente.estado) }}
                  </span>
                </td>
                <td>
                  <button type="button" class="btn btn-secondary btn-sm" @click.stop="abrirDetalle(cliente)">
                    Ver detalle
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Paginación DRF -->
        <div v-if="!cargando" class="pagination-footer">
          <div class="text-sm text-muted">
            Mostrando página {{ paginaActual }} · Total: {{ total }} instituciones
          </div>
          <div class="pagination-buttons">
            <button type="button" class="btn btn-secondary btn-sm" :disabled="!urlAnterior" @click="cambiarPagina(paginaActual - 1)">
              ← Anterior
            </button>
            <button type="button" class="btn btn-secondary btn-sm" :disabled="!urlSiguiente" @click="cambiarPagina(paginaActual + 1)">
              Siguiente →
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Detalle del Cliente Comercial -->
    <div v-if="clienteSeleccionado" class="modal-backdrop" @click="cerrarDetalle">
      <div class="modal-box" @click.stop>
        <div class="modal-header">
          <div>
            <h3 class="modal-title">Detalle de la Institución</h3>
            <span class="font-mono text-xs text-muted">{{ clienteSeleccionado.id }}</span>
          </div>
          <button type="button" class="modal-close-btn" aria-label="Cerrar" @click="cerrarDetalle">×</button>
        </div>

        <div class="modal-body">
          <div class="student-profile-summary">
            <div class="student-avatar-lg">
              {{ inicialesCliente }}
            </div>
            <div>
              <h4 class="student-fullname">{{ clienteSeleccionado.nombre }}</h4>
              <p class="text-sm text-muted">
                Plan: <strong>{{ clienteSeleccionado.plan || 'Sin plan contratante' }}</strong>
              </p>
            </div>
          </div>

          <div class="stats-mini-grid">
            <div class="stat-mini">
              <span class="stat-mini-label">Estado</span>
              <strong class="stat-mini-val">{{ etiqueta(clienteSeleccionado.estado) }}</strong>
            </div>
            <div class="stat-mini">
              <span class="stat-mini-label">Contrato</span>
              <strong class="stat-mini-val">{{ clienteDetalle?.contratoVigente ? 'Vigente' : 'Sin datos' }}</strong>
            </div>
            <div class="stat-mini">
              <span class="stat-mini-label">Licencias</span>
              <strong class="stat-mini-val">{{ clienteDetalle?.licencias?.length || 0 }}</strong>
            </div>
            <div class="stat-mini">
              <span class="stat-mini-label">Historial</span>
              <strong class="stat-mini-val">{{ clienteDetalle?.historial?.length || 0 }}</strong>
            </div>
          </div>

          <div class="detail-section">
            <h5 class="detail-subtitle">Plan Comercial</h5>
            <p class="text-sm text-muted">
              {{ clienteDetalle?.plan?.nombre || clienteSeleccionado.plan || 'Sin plan comercial asignado' }}
            </p>
          </div>

          <div class="detail-section">
            <h5 class="detail-subtitle">Contrato Vigente</h5>
            <p v-if="clienteDetalle?.contratoVigente" class="text-sm text-muted">
              Vigencia: {{ clienteDetalle.contratoVigente.fechaInicio || '—' }} → {{ clienteDetalle.contratoVigente.fechaFin || '—' }}
            </p>
            <p v-else class="text-sm text-muted">Sin contrato vigente registrado para esta institución.</p>
          </div>

          <div class="detail-section">
            <h5 class="detail-subtitle">Licencias</h5>
            <div v-if="clienteDetalle?.licencias?.length" class="ids-wrap">
              <span v-for="licencia in clienteDetalle.licencias" :key="licencia.id" class="badge badge-indigo">
                {{ licencia.plan || 'Licencia' }} · {{ licencia.estado || '' }}
              </span>
            </div>
            <p v-else class="text-sm text-muted">Sin licencias registradas para esta institución.</p>
          </div>

          <div class="detail-section">
            <h5 class="detail-subtitle">Historial de Contratación</h5>
            <div v-if="clienteDetalle?.historial?.length" class="ids-wrap">
              <span v-for="(evento, i) in clienteDetalle.historial" :key="i" class="badge badge-neutral">
                {{ evento }}
              </span>
            </div>
            <p v-else class="text-sm text-muted">Sin eventos de contratación registrados.</p>
          </div>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary btn-sm" @click="cerrarDetalle">Cerrar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useClientesComerciales } from '../composables/useClientesComerciales';
import { usePlanesComerciales } from '../composables/usePlanesComerciales';
import { etiquetaEstado } from '../services/normalizarComercial';

const {
  clientes,
  total,
  cargando,
  error,
  paginaActual,
  urlSiguiente,
  urlAnterior,
  busqueda,
  estadoFiltro,
  planFiltro,
  cargarClientes,
  establecerBusqueda,
  establecerEstado,
  establecerPlan,
  limpiarFiltros,
  cargarCliente,
} = useClientesComerciales();

const { planes, cargarPlanes } = usePlanesComerciales();

const opcionesEstado = [
  { valor: '', etiqueta: 'Todos los estados' },
  { valor: 'ACTIVO', etiqueta: 'Activo' },
  { valor: 'SUSPENDIDO', etiqueta: 'Suspendido' },
  { valor: 'CANCELADO', etiqueta: 'Cancelado' },
];

const clienteSeleccionado = ref(null);
const clienteDetalle = ref(null);
const cargandoDetalle = ref(false);
const errorDetalle = ref(null);

const tieneFiltros = computed(() => Boolean(busqueda.value.trim() || estadoFiltro.value || planFiltro.value));

const inicialesCliente = computed(() => {
  const nombre = clienteSeleccionado.value?.nombre || '';
  const partes = nombre.trim().split(/\s+/).filter(Boolean);
  const iniciales = partes.slice(0, 2).map((p) => p.charAt(0).toUpperCase()).join('');
  return iniciales || 'IC';
});

function etiqueta(estado) {
  return etiquetaEstado(estado) || 'Sin datos';
}

let debounceTimeout = null;

function onBusquedaInput() {
  clearTimeout(debounceTimeout);
  debounceTimeout = setTimeout(() => {
    establecerBusqueda(busqueda.value);
    cargarLista();
  }, 350);
}

function limpiarBusqueda() {
  establecerBusqueda('');
  cargarLista();
}

async function cargarLista() {
  await cargarClientes(paginaActual.value);
}

async function cambiarPagina(nuevaPagina) {
  if (nuevaPagina < 1) return;
  await cargarClientes(nuevaPagina);
}

function cerrarDetalle() {
  clienteSeleccionado.value = null;
  clienteDetalle.value = null;
}

async function abrirDetalle(cliente) {
  clienteSeleccionado.value = cliente;
  errorDetalle.value = null;
  cargandoDetalle.value = true;

  try {
    clienteDetalle.value = await cargarCliente(cliente.id);
  } catch (err) {
    errorDetalle.value = 'No se pudo cargar el detalle comercial de la institución.';
  } finally {
    cargandoDetalle.value = false;
  }
}

onMounted(() => {
  cargarPlanes();
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

.cliente-row {
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.cliente-row:hover {
  background-color: var(--primary-light) !important;
}

.pagination-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 1rem;
  margin-top: 1rem;
  border-top: 1px solid var(--border);
}

.pagination-buttons {
  display: flex;
  gap: 0.5rem;
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

.student-profile-summary {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.student-avatar-lg {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--accent);
  color: #ffffff;
  font-weight: 800;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.student-fullname {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 0.15rem;
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
