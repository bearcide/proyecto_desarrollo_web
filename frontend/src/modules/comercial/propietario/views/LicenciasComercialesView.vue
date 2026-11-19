<template>
  <div class="licencias-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Gestión de Licencias</h1>
        <p class="page-subtitle">Licencias vigentes, vencimientos y cupos de instituciones contratantes</p>
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
          Licencias Comerciales ({{ total }})
        </h2>
      </div>

      <div class="card-body">
        <div class="filter-bar">
          <div class="form-group" style="flex: 1 1 200px; margin-bottom: 0;">
            <label for="estado-licencia" class="form-label">Estado</label>
            <select id="estado-licencia" v-model="estadoFiltro" class="form-select" @change="cargarLista">
              <option v-for="opcion in opcionesEstado" :key="opcion.valor" :value="opcion.valor">{{ opcion.etiqueta }}</option>
            </select>
          </div>
          <div class="form-group" style="flex: 1 1 260px; margin-bottom: 0;">
            <label for="suscripcion-licencia" class="form-label">Suscripción</label>
            <input id="suscripcion-licencia" v-model="suscripcionFiltro" type="text" class="form-input" placeholder="ID de la suscripción" />
          </div>
          <button type="button" class="btn btn-outline btn-sm" @click="cargarLista">Filtrar</button>
          <button type="button" class="btn btn-secondary btn-sm" @click="limpiarFiltros">Limpiar</button>
        </div>

        <div v-if="cargando" class="empty-state">
          <div class="spinner spinner-primary" style="margin: 0 auto 0.5rem;"></div>
          <span class="text-muted">Cargando licencias comerciales…</span>
        </div>

        <div v-else-if="licencias.length === 0" class="empty-state">
          <div class="empty-state-icon">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          </div>
          <div class="empty-state-title">Sin licencias encontradas</div>
          <p class="empty-state-text">No hay licencias que coincidan con los filtros aplicados.</p>
        </div>

        <div v-else class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Suscripción</th>
                <th>Institución</th>
                <th>Plan</th>
                <th>Estado</th>
                <th>Fecha Vencimiento</th>
                <th>Detalle</th>
                <th>Acción</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="licencia in licencias"
                :key="licencia.id"
                class="licencia-row"
                @click="abrirDetalle(licencia)"
              >
                <td class="font-mono text-sm">#{{ licencia.id }}</td>
                <td class="font-mono text-sm">#{{ licencia.suscripcion || '—' }}</td>
                <td><strong>{{ licencia.institucion || '—' }}</strong></td>
                <td><span class="badge badge-indigo">{{ licencia.plan || 'Sin plan' }}</span></td>
                <td>
                  <span class="badge" :class="claseBadgeEstado(licencia.estado)">{{ etiqueta(licencia.estado) }}</span>
                </td>
                <td class="font-mono text-sm">{{ licencia.fechaVencimiento || '—' }}</td>
                <td>
                  <button type="button" class="btn btn-secondary btn-sm" @click.stop="abrirDetalle(licencia)">
                    Ver detalle
                  </button>
                </td>
                <td>
                  <button
                    v-if="puedeRevocar(licencia)"
                    type="button"
                    class="btn btn-outline btn-sm"
                    :disabled="revocando"
                    @click.stop="iniciarRevocacion(licencia)"
                  >
                    Revocar licencia
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Modal Detalle de Licencia -->
    <div v-if="licenciaSeleccionada" class="modal-backdrop" @click="cerrarDetalle">
      <div class="modal-box" @click.stop>
        <div class="modal-header">
          <div>
            <h3 class="modal-title">Licencia #{{ licenciaSeleccionada.id }}</h3>
            <span class="font-mono text-xs text-muted">Suscripción #{{ licenciaSeleccionada.suscripcion || '—' }}</span>
          </div>
          <button type="button" class="modal-close-btn" aria-label="Cerrar" @click="cerrarDetalle">×</button>
        </div>

        <div class="modal-body">
          <div class="stats-mini-grid">
            <div class="stat-mini">
              <span class="stat-mini-label">Estado</span>
              <strong class="stat-mini-val">{{ etiqueta(licenciaSeleccionada.estado) }}</strong>
            </div>
            <div class="stat-mini">
              <span class="stat-mini-label">Vigente</span>
              <strong class="stat-mini-val">{{ licenciaSeleccionada.activo ? 'Sí' : 'No' }}</strong>
            </div>
            <div class="stat-mini">
              <span class="stat-mini-label">Límite</span>
              <strong class="stat-mini-val">{{ licenciaSeleccionada.limite ?? 'Ilimitado' }}</strong>
            </div>
            <div class="stat-mini">
              <span class="stat-mini-label">Usados</span>
              <strong class="stat-mini-val">{{ licenciaSeleccionada.usados ?? '—' }}</strong>
            </div>
          </div>

          <div class="detail-section">
            <h5 class="detail-subtitle">Fecha de Vencimiento</h5>
            <p class="text-sm text-muted">{{ licenciaSeleccionada.fechaVencimiento || 'Sin fecha de vencimiento registrada' }}</p>
          </div>

          <div class="detail-section">
            <h5 class="detail-subtitle">Revocación</h5>
            <p v-if="licenciaSeleccionada.revocada" class="text-sm text-muted">
              Licencia revocada: el acceso quedó suspendido de forma permanente.
            </p>
            <p v-else class="text-sm text-muted">Sin revocaciones registradas para esta licencia.</p>
          </div>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary btn-sm" @click="cerrarDetalle">Cerrar</button>
          <button
            v-if="puedeRevocar(licenciaSeleccionada)"
            type="button"
            class="btn btn-danger btn-sm"
            :disabled="revocando"
            @click="iniciarRevocacion(licenciaSeleccionada)"
          >
            Revocar licencia
          </button>
        </div>
      </div>
    </div>

    <!-- Modal Confirmación de Revocación de Licencia -->
    <div v-if="licenciaRevocar" class="modal-backdrop" @click="cerrarRevocacion">
      <div class="modal-box" @click.stop role="dialog" aria-modal="true">
        <div class="modal-header">
          <div>
            <h3 class="modal-title">Revocar Licencia #{{ licenciaRevocar.id }}</h3>
            <span class="font-mono text-xs text-muted">Suscripción #{{ licenciaRevocar.suscripcion || '—' }}</span>
          </div>
          <button type="button" class="modal-close-btn" aria-label="Cerrar" @click="cerrarRevocacion">×</button>
        </div>

        <div class="modal-body">
          <p class="text-sm" style="margin-bottom: 0.75rem;">
            La revocación de la licencia es <strong>permanente e irreversible</strong>. La institución perderá
            el acceso inmediatamente a las funcionalidades contratadas y el evento quedará registrado en el
            historial auditable del backend.
          </p>
          <div v-if="errorRevocar" class="alert alert-danger" role="alert">
            {{ errorRevocar }}
          </div>
          <p v-if="procesandoRevocacion" class="text-sm text-muted">Procesando la revocación…</p>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary btn-sm" :disabled="procesandoRevocacion" @click="cerrarRevocacion">Volver</button>
          <button type="button" class="btn btn-danger btn-sm" :disabled="procesandoRevocacion" @click="confirmarRevocacion">Confirmar revocación</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useLicenciasComerciales } from '../composables/useLicenciasComerciales';
import { etiquetaEstado, normalizarEstado } from '../services/normalizarComercial';

const {
  licencias,
  total,
  cargando,
  error,
  estadoFiltro,
  suscripcionFiltro,
  revocando,
  errorRevocar,
  cargarLicencias,
  establecerEstado,
  establecerSuscripcion,
  limpiarFiltros,
  revocar,
  puedeRevocar,
} = useLicenciasComerciales();

const opcionesEstado = [
  { valor: '', etiqueta: 'Todos los estados' },
  { valor: 'ACTIVE', etiqueta: 'Activa' },
  { valor: 'REVOKED', etiqueta: 'Revocada' },
];

const licenciaSeleccionada = ref(null);
const licenciaRevocar = ref(null);
const procesandoRevocacion = ref(false);

function etiqueta(estado) {
  return etiquetaEstado(estado) || 'Sin datos';
}

function claseBadgeEstado(estado) {
  const valor = normalizarEstado(estado);
  if (valor === 'ACTIVE') return 'badge-success';
  if (valor === 'REVOKED') return 'badge-danger';
  if (valor === 'PENDING') return 'badge-warning';
  return 'badge-neutral';
}

async function cargarLista() {
  await cargarLicencias(1);
}

function limpiarFiltrosComerciales() {
  limpiarFiltros();
  establecerEstado('');
  establecerSuscripcion('');
}

function iniciarRevocacion(licencia) {
  licenciaRevocar.value = licencia;
}

function cerrarRevocacion() {
  licenciaRevocar.value = null;
}

async function confirmarRevocacion() {
  if (!licenciaRevocar.value) return;
  procesandoRevocacion.value = true;
  const resultado = await revocar(licenciaRevocar.value.id);
  procesandoRevocacion.value = false;
  if (resultado?.ok) {
    licenciaRevocar.value = null;
    licenciaSeleccionada.value = null;
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
