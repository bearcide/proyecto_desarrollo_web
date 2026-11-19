<template>
  <div class="suscripciones-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Gestión de Suscripciones</h1>
        <p class="page-subtitle">Suscripciones, contratos, licencias y renovaciones de las instituciones</p>
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
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          Suscripciones Comerciales ({{ total }})
        </h2>
      </div>

      <div class="card-body">
        <div class="filter-bar">
          <div class="form-group" style="flex: 1 1 200px; margin-bottom: 0;">
            <label for="estado-suscripcion" class="form-label">Estado</label>
            <select id="estado-suscripcion" v-model="estadoFiltro" class="form-select" @change="cargarLista">
              <option v-for="opcion in opcionesEstado" :key="opcion.valor" :value="opcion.valor">{{ opcion.etiqueta }}</option>
            </select>
          </div>
          <div class="form-group" style="flex: 1 1 260px; margin-bottom: 0;">
            <label for="institucion-suscripcion" class="form-label">Institución</label>
            <input id="institucion-suscripcion" v-model="institucionFiltro" type="text" class="form-input" placeholder="ID o nombre de la institución" />
          </div>
          <button type="button" class="btn btn-outline btn-sm" @click="cargarLista">Filtrar</button>
          <button type="button" class="btn btn-secondary btn-sm" @click="limpiarFiltros">Limpiar</button>
        </div>

        <div v-if="cargando" class="empty-state">
          <div class="spinner spinner-primary" style="margin: 0 auto 0.5rem;"></div>
          <span class="text-muted">Cargando suscripciones comerciales…</span>
        </div>

        <div v-else-if="suscripciones.length === 0" class="empty-state">
          <div class="empty-state-icon">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          </div>
          <div class="empty-state-title">Sin suscripciones encontradas</div>
          <p class="empty-state-text">No hay suscripciones que coincidan con los filtros aplicados.</p>
        </div>

        <div v-else class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Institución</th>
                <th>Plan</th>
                <th>Estado</th>
                <th>Fecha Inicio</th>
                <th>Fecha Fin / Renovación</th>
                <th>Licencia</th>
                <th>Detalle</th>
                <th>Acción</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="suscripcion in suscripciones"
                :key="suscripcion.id"
                class="suscripcion-row"
                @click="abrirDetalle(suscripcion)"
              >
                <td class="font-mono text-sm">#{{ suscripcion.id }}</td>
                <td><strong>{{ suscripcion.institucion || '—' }}</strong></td>
                <td><span class="badge badge-indigo">{{ suscripcion.plan || 'Sin plan' }}</span></td>
                <td>
                  <span class="badge" :class="claseBadgeEstado(suscripcion.estado)">{{ etiqueta(suscripcion.estado) }}</span>
                </td>
                <td class="font-mono text-sm">{{ suscripcion.fechaInicio || '—' }}</td>
                <td class="font-mono text-sm">{{ suscripcion.fechaFin || '—' }}</td>
                <td>{{ suscripcion.licencia || '—' }}</td>
                <td>
                  <button type="button" class="btn btn-secondary btn-sm" @click.stop="abrirDetalle(suscripcion)">
                    Ver detalle
                  </button>
                </td>
                <td>
                  <button
                    v-if="puedeActuar(suscripcion)"
                    type="button"
                    class="btn btn-outline btn-sm"
                    :disabled="cancelando"
                    @click.stop="iniciarCancelacion(suscripcion)"
                  >
                    Cancelar suscripción
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Modal Detalle de Suscripción / Contrato -->
    <div v-if="suscripcionSeleccionada" class="modal-backdrop" @click="cerrarDetalle">
      <div class="modal-box" @click.stop>
        <div class="modal-header">
          <div>
            <h3 class="modal-title">Suscripción #{{ suscripcionSeleccionada.id }}</h3>
            <span class="font-mono text-xs text-muted">{{ suscripcionSeleccionada.institucion || 'Sin institución' }}</span>
          </div>
          <button type="button" class="modal-close-btn" aria-label="Cerrar" @click="cerrarDetalle">×</button>
        </div>

        <div class="modal-body">
          <div class="stats-mini-grid">
            <div class="stat-mini">
              <span class="stat-mini-label">Estado</span>
              <strong class="stat-mini-val">{{ etiqueta(suscripcionSeleccionada.estado) }}</strong>
            </div>
            <div class="stat-mini">
              <span class="stat-mini-label">Vigencia</span>
              <strong class="stat-mini-val">{{ esVigente(suscripcionSeleccionada.fechaFin) ? 'Vigente' : '—' }}</strong>
            </div>
            <div class="stat-mini">
              <span class="stat-mini-label">Licencia</span>
              <strong class="stat-mini-val">{{ suscripcionSeleccionada.licencia ? 'Asignada' : '—' }}</strong>
            </div>
            <div class="stat-mini">
              <span class="stat-mini-label">Importe</span>
              <strong class="stat-mini-val">{{ suscripcionSeleccionada.monto ?? '—' }}</strong>
            </div>
          </div>

          <div class="detail-section">
            <h5 class="detail-subtitle">Contrato Vigente</h5>
            <p v-if="suscripcionSeleccionada.fechaFin" class="text-sm text-muted">
              Periodo: {{ suscripcionSeleccionada.fechaInicio || '—' }} → {{ suscripcionSeleccionada.fechaFin || '—' }}
            </p>
            <p v-else class="text-sm text-muted">Sin datos de contrato disponibles.</p>
          </div>

          <div class="detail-section">
            <h5 class="detail-subtitle">Renovaciones y Cancelaciones</h5>
            <p v-if="suscripcionSeleccionada.cancelacionProgramada" class="text-sm text-muted">
              Cancelación programada al fin del periodo: el acceso se mantiene vigente hasta
              {{ suscripcionSeleccionada.fechaFin || 'la fecha de renovación registrada' }}.
            </p>
            <p v-else class="text-sm text-muted">
              Sin cancelaciones programadas para esta suscripción.
            </p>
          </div>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary btn-sm" @click="cerrarDetalle">Cerrar</button>
          <button
            v-if="puedeActuar(suscripcionSeleccionada)"
            type="button"
            class="btn btn-danger btn-sm"
            :disabled="cancelando"
            @click="iniciarCancelacion(suscripcionSeleccionada)"
          >
            Cancelar suscripción
          </button>
        </div>
      </div>
    </div>

    <!-- Modal Confirmación de Cancelación de Suscripción -->
    <div v-if="suscripcionCancelar" class="modal-backdrop" @click="cerrarCancelacion">
      <div class="modal-box" @click.stop role="dialog" aria-modal="true">
        <div class="modal-header">
          <div>
            <h3 class="modal-title">Cancelar Suscripción #{{ suscripcionCancelar.id }}</h3>
            <span class="font-mono text-xs text-muted">{{ suscripcionCancelar.institucion || 'Sin institución' }}</span>
          </div>
          <button type="button" class="modal-close-btn" aria-label="Cerrar" @click="cerrarCancelacion">×</button>
        </div>

        <div class="modal-body">
          <p class="text-sm" style="margin-bottom: 0.75rem;">
            La cancelación de la suscripción se programa al <strong>fin del periodo pagado</strong>
            ({{ suscripcionCancelar.fechaFin || 'la fecha de renovación registrada' }}).
            El acceso a las funcionalidades contratadas se mantiene vigente hasta esa fecha y la
            renovación automática no se ejecutará.
          </p>
          <div v-if="errorCancelar" class="alert alert-danger" role="alert">
            {{ errorCancelar }}
          </div>
          <p v-if="procesandoCancelacion" class="text-sm text-muted">Procesando la cancelación…</p>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary btn-sm" :disabled="procesandoCancelacion" @click="cerrarCancelacion">Volver</button>
          <button type="button" class="btn btn-danger btn-sm" :disabled="procesandoCancelacion" @click="confirmarCancelacion">Confirmar cancelación</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useSuscripcionesComerciales } from '../composables/useSuscripcionesComerciales';
import { esVigente, etiquetaEstado, normalizarEstado } from '../services/normalizarComercial';

const {
  suscripciones,
  total,
  cargando,
  error,
  paginaActual,
  urlSiguiente,
  urlAnterior,
  estadoFiltro,
  institucionFiltro,
  cancelando,
  errorCancelar,
  cargarSuscripciones,
  establecerEstado,
  establecerInstitucion,
  limpiarFiltros,
  cancelar,
  puedeActuar,
} = useSuscripcionesComerciales();

const opcionesEstado = [
  { valor: '', etiqueta: 'Todos los estados' },
  { valor: 'ACTIVE', etiqueta: 'Activa' },
  { valor: 'PAST_DUE', etiqueta: 'De pago' },
  { valor: 'CANCELED', etiqueta: 'Cancelada' },
];

const suscripcionSeleccionada = ref(null);
const suscripcionCancelar = ref(null);
const procesandoCancelacion = ref(false);

const tieneFiltros = computed(() => Boolean(institucionFiltro.value || estadoFiltro.value));

function etiqueta(estado) {
  return etiquetaEstado(estado) || 'Sin datos';
}

function claseBadgeEstado(estado) {
  const valor = normalizarEstado(estado);
  if (valor === 'ACTIVE') return 'badge-success';
  if (valor === 'PAST_DUE') return 'badge-warning';
  if (valor === 'CANCELED') return 'badge-neutral';
  if (valor === 'PENDING') return 'badge-warning';
  return 'badge-neutral';
}

async function cargarLista() {
  await cargarSuscripciones(paginaActual.value);
}

function limpiarFiltrosComerciales() {
  limpiarFiltros();
  establecerEstado('');
  establecerInstitucion('');
}

function iniciarCancelacion(suscripcion) {
  suscripcionCancelar.value = suscripcion;
}

function cerrarCancelacion() {
  suscripcionCancelar.value = null;
}

async function confirmarCancelacion() {
  if (!suscripcionCancelar.value) return;
  procesandoCancelacion.value = true;
  const resultado = await cancelar(suscripcionCancelar.value.id);
  procesandoCancelacion.value = false;
  if (resultado?.ok) {
    suscripcionCancelar.value = null;
    suscripcionSeleccionada.value = null;
    await cargarLista();
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
