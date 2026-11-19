<template>
  <div class="facturacion-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Transacciones y Facturación</h1>
        <p class="page-subtitle">Historial de pagos, comprobantes y solicitudes de facturación</p>
      </div>
      <div class="header-actions">
        <button type="button" class="btn btn-secondary btn-sm" :disabled="pagosCargando" @click="cargarPagos">
          <svg :class="{ spinner: pagosCargando }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
          Actualizar
        </button>
      </div>
    </div>

    <!-- Filtros -->
    <div class="card" style="margin-bottom: 1.5rem;">
      <div class="card-header">
        <h2 class="card-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 3H2l8 9.46a2 2 0 0 0 1.99 1.78h8.73a2 2 0 0 0 1.99-1.78L22 3z"/><polyline points="11 22 11 12 13 12 13 22"/></svg>
          Filtros de Transacción
        </h2>
      </div>
      <div class="card-body">
        <div class="filter-bar" style="margin-bottom: 0;">
          <div class="form-group" style="flex: 1 1 200px; margin-bottom: 0;">
            <label for="fecha-inicio" class="form-label">Fecha desde</label>
            <input id="fecha-inicio" v-model="fechaInicio" type="date" class="form-input" />
          </div>
          <div class="form-group" style="flex: 1 1 200px; margin-bottom: 0;">
            <label for="fecha-fin" class="form-label">Fecha hasta</label>
            <input id="fecha-fin" v-model="fechaFin" type="date" class="form-input" />
          </div>
          <div class="form-group" style="flex: 1 1 220px; margin-bottom: 0;">
            <label for="institucion-pago" class="form-label">Institución</label>
            <input id="institucion-pago" v-model="institucionFiltro" type="text" class="form-input" placeholder="ID o nombre de la institución" />
          </div>
          <div class="form-group" style="flex: 1 1 180px; margin-bottom: 0;">
            <label for="estado-pago" class="form-label">Estado de pago</label>
            <select id="estado-pago" v-model="estadoPago" class="form-select">
              <option value="">Todos los estados</option>
              <option value="PAID">Pagado</option>
              <option value="PENDING">Pendiente</option>
              <option value="FAILED">Fallido</option>
            </select>
          </div>
          <div class="header-actions" style="align-self: flex-end; gap: 0.5rem;">
            <button type="button" class="btn btn-secondary btn-sm" @click="aplicarFiltros">Aplicar filtros</button>
            <button type="button" class="btn btn-outline btn-sm" @click="limpiarFiltros">Limpiar</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="pagosError" class="alert alert-danger" role="alert">
      {{ pagosError }}
    </div>

    <div class="card" style="margin-bottom: 1.5rem;">
      <div class="card-header">
        <h2 class="card-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>
          Historial de Pagos ({{ pagosTotal }})
        </h2>
      </div>

      <div class="card-body">
        <div v-if="pagosCargando" class="empty-state">
          <div class="spinner spinner-primary" style="margin: 0 auto 0.5rem;"></div>
          <span class="text-muted">Cargando historial de pagos…</span>
        </div>

        <div v-else-if="pagos.length === 0" class="empty-state">
          <div class="empty-state-icon">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>
          </div>
          <div class="empty-state-title">Sin pagos registrados</div>
          <p class="empty-state-text">No hay transacciones que coincidan con los filtros aplicados.</p>
        </div>

        <div v-else class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Institución</th>
                <th>Importe</th>
                <th>Estado</th>
                <th>Referencia Proveedor</th>
                <th>Comprobante</th>
                <th>Factura</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="pago in pagos" :key="pago.id">
                <td class="font-mono text-sm">{{ formatearFecha(pago.fecha) || '—' }}</td>
                <td>{{ pago.institucion || '—' }}</td>
                <td class="font-mono font-bold">{{ formatearMoneda(pago.importe) }}</td>
                <td>
                  <span class="badge" :class="claseBadgePago(pago.estado)">{{ etiquetaPago(pago.estado) }}</span>
                </td>
                <td class="font-mono text-xs">{{ pago.referenciaProveedor || '—' }}</td>
                <td>
                  <button
                    type="button"
                    class="btn btn-secondary btn-sm"
                    :disabled="descargando || !pago.comprobante"
                    @click="descargarComprobante(pago)"
                  >
                    {{ descargando ? 'Descargando…' : (pago.comprobante ? 'Descargar' : 'No disponible') }}
                  </button>
                </td>
                <td>{{ pago.factura || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Solicitudes de facturación -->
    <div class="card">
      <div class="card-header">
        <h2 class="card-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          Solicitudes de Facturación ({{ solicitudesTotal }})
        </h2>
      </div>
      <div class="card-body">
        <div v-if="solicitudesError" class="alert alert-danger" role="alert">
          {{ solicitudesError }}
        </div>

        <div v-if="solicitudesCargando" class="empty-state">
          <div class="spinner spinner-primary" style="margin: 0 auto 0.5rem;"></div>
          <span class="text-muted">Cargando solicitudes de facturación…</span>
        </div>

        <div v-else-if="solicitudes.length === 0" class="empty-state">
          <div class="empty-state-icon">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          </div>
          <div class="empty-state-title">Sin solicitudes de facturación</div>
          <p class="empty-state-text">No hay solicitudes registradas por las instituciones.</p>
        </div>

        <div v-else class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Solicitud</th>
                <th>Institución</th>
                <th>Fecha</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="solicitud in solicitudes" :key="solicitud.id">
                <td class="font-mono text-sm">#{{ solicitud.id }}</td>
                <td>{{ solicitud.institucion || '—' }}</td>
                <td class="font-mono text-sm">{{ formatearFecha(solicitud.fechaSolicitud) || '—' }}</td>
                <td>
                  <span class="badge" :class="claseBadgeSolicitud(solicitud.estado)">{{ etiquetaSolicitud(solicitud.estado) }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useFacturacionComercial } from '../composables/useFacturacionComercial';
import { descargarComprobanteComercial } from '../services/apiComercial';
import { etiquetaEstado, formatearFecha, formatearMoneda, normalizarEstado } from '../services/normalizarComercial';
import { useNotificationStore } from '../../../../stores/notification';

const notifStore = useNotificationStore();

const {
  pagos,
  pagosTotal,
  pagosCargando,
  pagosError,
  fechaInicio,
  fechaFin,
  institucionFiltro,
  estadoPago,
  cargarPagos,
  cargarSolicitudes,
  solicitudes,
  solicitudesTotal,
  solicitudesCargando,
  solicitudesError,
  establecerFechaInicio,
  establecerFechaFin,
  establecerInstitucion,
  establecerEstadoPago,
  limpiarFiltros,
} = useFacturacionComercial();

const descargando = ref(false);

function claseBadgePago(estado) {
  const valor = normalizarEstado(estado);
  if (valor === 'PAID') return 'badge-success';
  if (valor === 'PENDING') return 'badge-warning';
  if (valor === 'FAILED') return 'badge-danger';
  return 'badge-neutral';
}

function etiquetaPago(estado) {
  return etiquetaEstado(estado) || 'Sin datos';
}

function claseBadgeSolicitud(estado) {
  const valor = normalizarEstado(estado);
  if (valor === 'PROCESSING') return 'badge-warning';
  if (valor === 'REJECTED') return 'badge-danger';
  if (valor === 'REQUESTED') return 'badge-neutral';
  if (valor === 'CONFIRMADA' || valor === 'APROBADA' || valor === 'EMITIDA') return 'badge-success';
  return 'badge-neutral';
}

function etiquetaSolicitud(estado) {
  return etiquetaEstado(estado) || 'Sin datos';
}

async function aplicarFiltros() {
  await cargarPagos(1);
}

async function descargarComprobante(pago) {
  descargando.value = true;
  try {
    const { url, nombre } = await descargarComprobanteComercial(pago.id);
    const enlace = document.createElement('a');
    enlace.href = url;
    enlace.download = nombre;
    document.body.appendChild(enlace);
    enlace.click();
    enlace.remove();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
    notifStore.success(`Comprobante "${nombre}" descargado correctamente.`);
  } catch (_) {
    // No se genera comprobantes: si el backend no tiene uno emitido, se informa sin simular.
    notifStore.warning('No hay comprobante disponible para este pago.');
  } finally {
    descargando.value = false;
  }
}

onMounted(() => {
  cargarPagos(1);
  cargarSolicitudes(1);
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
