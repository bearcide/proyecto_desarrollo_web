<template>
  <div class="suscripcion-page">
    <div class="page-header">
      <div>
        <div class="header-pretitle">
          <AppIcon name="credit-card" size="16" class="text-primary" />
          <span>Gestión de Contratación y Facturación Escolar</span>
        </div>
        <h1 class="page-title">Mi Suscripción y Licencias</h1>
        <p class="page-subtitle">
          Supervisa el estado de vigencia, límites de consumo de alumnos, comprobantes de pago y facturación fiscal.
        </p>
      </div>

      <div class="header-actions">
        <router-link to="/admin/comercial/planes" class="btn btn-primary btn-sm">
          <AppIcon name="award" size="15" />
          <span>Explorar / Mejorar Plan</span>
        </router-link>
        <button
          type="button"
          class="btn btn-secondary btn-sm"
          :disabled="cargando"
          @click="cargarDatos"
        >
          <AppIcon name="refresh" size="14" :class="{ spinner: cargando }" />
          <span>Actualizar</span>
        </button>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="error" class="alert alert-danger" role="alert">
      <AppIcon name="alert" size="18" />
      <span>{{ error }}</span>
    </div>

    <!-- Estado de Carga Inicial -->
    <div v-if="cargando && !suscripcionPrincipal" class="empty-state">
      <div class="spinner spinner-primary" style="margin: 0 auto 0.75rem;"></div>
      <span class="text-muted">Consultando estado comercial de la institución…</span>
    </div>

    <div v-else class="suscripcion-content-grid">
      <!-- 1. Tarjeta de Estado del Plan Actual -->
      <section v-if="suscripcionPrincipal" class="card main-plan-card">
        <div class="main-plan-header">
          <div>
            <span class="plan-type-label">Plan Institucional Contratado</span>
            <h2 class="main-plan-name">{{ suscripcionPrincipal.plan_nombre || 'Suscripción institucional' }}</h2>
          </div>
          <div class="plan-badges-group">
            <ModalidadBadge :modalidad="suscripcionPrincipal.modalidad" />
            <EstadoPagoBadge :estado="suscripcionPrincipal.estado" />
          </div>
        </div>

        <div class="plan-details-strip">
          <div class="detail-cell">
            <span class="detail-label">Fin de Periodo / Renovación</span>
            <span class="detail-val font-bold">
              {{ formatearFecha(suscripcionPrincipal?.fin_periodo) }}
            </span>
          </div>

          <div class="detail-cell">
            <span class="detail-label">Renovación Automática</span>
            <span class="detail-val" :class="suscripcionPrincipal?.cancel_at_period_end ? 'text-warning font-bold' : 'text-success'">
              {{ suscripcionPrincipal.cancel_at_period_end ? 'Cancela al fin de periodo' : suscripcionPrincipal.estado === 'active' ? 'Programada' : 'Sin renovación activa' }}
            </span>
          </div>

          <div class="detail-cell">
            <span class="detail-label">Importe Periodo</span>
            <span class="detail-val font-bold">
              {{ formatearMoneda(suscripcionPrincipal.importe, suscripcionPrincipal.moneda) }} {{ suscripcionPrincipal.moneda }}
            </span>
          </div>
        </div>

        <!-- Alerta si la cancelación fue programada -->
        <div v-if="suscripcionPrincipal?.cancel_at_period_end" class="cancel-scheduled-alert">
          <AppIcon name="info" size="18" />
          <span>
            Se ha programado la no renovación del servicio. Tu institución mantendrá acceso completo hasta el
            <strong>{{ formatearFecha(suscripcionPrincipal?.fin_periodo) }}</strong> sin cargos futuros.
          </span>
        </div>

        <!-- Acciones del Plan -->
        <div class="main-plan-actions">
          <router-link to="/admin/comercial/configurador" class="btn btn-secondary btn-sm">
            <AppIcon name="sliders" size="14" />
            <span>Consultar opciones de contratación</span>
          </router-link>

          <button
            v-if="suscripcionPrincipal.estado === 'active' && !suscripcionPrincipal.cancel_at_period_end"
            type="button"
            class="btn btn-outline btn-sm text-danger-btn"
            @click="abrirConfirmacionCancelar"
          >
            <span>Cancelar Renovación Programada</span>
          </button>
        </div>
      </section>

      <section v-else class="card main-plan-card">
        <p>{{ error ? 'No se pudo consultar la suscripción.' : 'Sin suscripción registrada.' }}</p>
      </section>

      <!-- 2. Límites y Consumo de Acceso Efectivo -->
      <section class="card limits-card">
        <h3 class="section-title-sm">
          <AppIcon name="shield" size="18" class="text-primary" />
          <span>Acceso Efectivo y Límites de la Institución</span>
        </h3>

        <div class="limits-metrics-grid">
          <div class="metric-box">
            <div class="metric-top">
              <span class="metric-name">Alumnos Concurrentes</span>
              <AppIcon name="user" size="18" class="text-primary" />
            </div>
            <div class="metric-val">
              <span class="num">{{ acceso?.max_alumnos?.toLocaleString() ?? '—' }}</span>
              <span class="unit">máximo autorizado</span>
            </div>
          </div>

          <div class="metric-box">
            <div class="metric-top">
              <span class="metric-name">Planteles Habilitados</span>
              <AppIcon name="building" size="18" class="text-blue" />
            </div>
            <div class="metric-val">
              <span class="num">{{ acceso?.max_planteles ?? '—' }}</span>
              <span class="unit">campus central y sedes</span>
            </div>
          </div>
        </div>

        <div class="features-enabled-box">
          <span class="features-box-title">Funcionalidades del Sistema Activas:</span>
          <div class="features-tags">
            <span
              v-for="(f, i) in listaFuncionalidades"
              :key="i"
              class="feature-pill"
            >
              <AppIcon name="check" size="14" class="text-success" />
              <span>{{ f }}</span>
            </span>
          </div>
        </div>
      </section>

      <!-- 3. Navegación por pestañas: Transacciones, Comprobantes, Facturas CFDI -->
      <section class="card tabs-section-card">
        <div class="tabs-header" role="tablist">
          <button
            type="button"
            role="tab"
            class="tab-btn"
            :class="{ active: tabActiva === 'transacciones' }"
            @click="tabActiva = 'transacciones'"
          >
            <AppIcon name="credit-card" size="16" />
            <span>Historial de Pagos ({{ transacciones.length }})</span>
          </button>

          <button
            type="button"
            role="tab"
            class="tab-btn"
            :class="{ active: tabActiva === 'comprobantes' }"
            @click="tabActiva = 'comprobantes'"
          >
            <AppIcon name="download" size="16" />
            <span>Comprobantes PDF ({{ comprobantes.length }})</span>
          </button>

          <button
            type="button"
            role="tab"
            class="tab-btn"
            :class="{ active: tabActiva === 'facturas' }"
            @click="tabActiva = 'facturas'"
          >
            <AppIcon name="file-text" size="16" />
            <span>Facturación CFDI ({{ facturas.length }})</span>
          </button>
        </div>

        <!-- Pestaña 1: Transacciones -->
        <div v-if="tabActiva === 'transacciones'" class="tab-pane">
          <div v-if="!transacciones.length" class="empty-state">
            <AppIcon name="credit-card" size="32" class="text-muted" />
            <p class="text-muted text-sm" style="margin-top: 0.5rem;">
              No se han registrado transacciones bancarias recientes.
            </p>
          </div>

          <div v-else class="table-responsive">
            <table class="table">
              <thead>
                <tr>
                  <th>Referencia de Pago</th>
                  <th>Fecha</th>
                  <th>Importe</th>
                  <th>Estado</th>
                  <th class="text-right">Acción</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="tx in transacciones" :key="tx.id">
                  <td>
                    <code class="text-xs font-bold">{{ tx.referencia || tx.id.substring(0, 12) }}</code>
                  </td>
                  <td>{{ formatearFecha(tx.fecha) }}</td>
                  <td class="font-bold">{{ formatearMoneda(tx.importe, tx.moneda) }}</td>
                  <td>
                    <EstadoPagoBadge :estado="tx.estado" />
                  </td>
                  <td class="text-right">
                    <button
                      type="button"
                      class="btn btn-secondary btn-sm"
                      @click="abrirFacturaParaOrden(tx.orden, tx.importe)"
                    >
                      <AppIcon name="file-text" size="13" />
                      <span>Pedir Factura</span>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Pestaña 2: Comprobantes PDF -->
        <div v-if="tabActiva === 'comprobantes'" class="tab-pane">
          <div v-if="!comprobantes.length" class="empty-state">
            <AppIcon name="download" size="32" class="text-muted" />
            <p class="text-muted text-sm" style="margin-top: 0.5rem;">
              No hay comprobantes de pago emitidos todavía.
            </p>
          </div>

          <div v-else class="comprobantes-grid">
            <div v-for="comp in comprobantes" :key="comp.id" class="comprobante-card">
              <div class="comprobante-icon-box">
                <AppIcon name="file-text" size="24" class="text-primary" />
              </div>
              <div class="comprobante-info">
                <span class="comprobante-folio">Folio: {{ comp.folio }}</span>
                <span class="comprobante-date">{{ formatearFecha(comp.fecha) }}</span>
                <span class="comprobante-amount font-bold">{{ formatearMoneda(comp.importe, comp.moneda) }}</span>
              </div>
              <button
                type="button"
                class="btn btn-outline btn-sm download-btn"
                @click="descargarComprobante(comp.id, comp.folio)"
              >
                <AppIcon name="download" size="14" />
                <span>Descargar PDF</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Pestaña 3: Facturas CFDI -->
        <div v-if="tabActiva === 'facturas'" class="tab-pane">
          <div class="facturas-topbar">
            <div>
              <h4 class="facturas-heading">Comprobantes Fiscales Digitales por Internet (SAT México)</h4>
              <p class="facturas-subheading">
                Las solicitudes son validadas con el catálogo de órdenes pagadas.
              </p>
            </div>
            <button
              type="button"
              class="btn btn-primary btn-sm"
              @click="abrirFacturaParaOrden(transacciones[0]?.orden, transacciones[0]?.importe)"
            >
              <AppIcon name="file-text" size="14" />
              <span>Nueva Solicitud Fiscal</span>
            </button>
          </div>

          <div v-if="!facturas.length" class="empty-state">
            <AppIcon name="file-text" size="32" class="text-muted" />
            <p class="text-muted text-sm" style="margin-top: 0.5rem;">
              No tienes solicitudes de facturación activas para este ciclo.
            </p>
          </div>

          <div v-else class="table-responsive">
            <table class="table">
              <thead>
                <tr>
                  <th>RFC Receptor</th>
                  <th>Razón Social</th>
                  <th>Uso CFDI</th>
                  <th>Régimen</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="fact in facturas" :key="fact.id">
                  <td><code class="font-bold">{{ fact.rfc }}</code></td>
                  <td>{{ fact.razon_social }}</td>
                  <td>{{ fact.uso_cfdi }}</td>
                  <td>Régimen {{ fact.regimen }}</td>
                  <td>
                    <EstadoPagoBadge :estado="fact.estado" />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>

    <!-- ConfirmSheet para cancelar renovación -->
    <ConfirmSheet
      :abierto="sheetCancelarAbierto"
      titulo="¿Deseas cancelar la renovación programada?"
      descripcion="Esta acción evitará cobros automáticos posteriores. Tu institución conservará todas las funciones y cupos activos hasta el término del periodo ya pagado."
      texto-confirmar="Confirmar Cancelación de Renovación"
      texto-cancelar="Conservar Renovación Activa"
      @confirmar="ejecutarCancelar"
      @cancelar="sheetCancelarAbierto = false"
    />

    <!-- Modal de Facturación -->
    <FacturacionModal
      :abierto="modalFacturaAbierto"
      :orden-id="ordenFacturaId"
      :importe="ordenFacturaImporte"
      :enviando="enviandoFactura"
      @cerrar="modalFacturaAbierto = false"
      @solicitar="onSolicitarFactura"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import AppIcon from '../../../../components/AppIcon.vue';
import ModalidadBadge from '../components/ModalidadBadge.vue';
import EstadoPagoBadge from '../components/EstadoPagoBadge.vue';
import ConfirmSheet from '../../../../components/ConfirmSheet.vue';
import FacturacionModal from '../components/FacturacionModal.vue';
import { useComercial } from '../composables/useComercial';
import { formatearMoneda } from '../domain/comercialCalculos';

const {
  cargando,
  error,
  acceso,
  suscripciones,
  transacciones,
  comprobantes,
  facturas,
  cargarEstadoInstitucion,
  cancelarRenovacion,
  descargarComprobante,
  enviarSolicitudFactura,
} = useComercial();

const tabActiva = ref('transacciones');
const sheetCancelarAbierto = ref(false);

const modalFacturaAbierto = ref(false);
const ordenFacturaId = ref('');
const ordenFacturaImporte = ref('0.00');
const enviandoFactura = ref(false);

onMounted(async () => {
  await cargarDatos();
});

async function cargarDatos() {
  await cargarEstadoInstitucion();
}

const suscripcionPrincipal = computed(() => {
  if (suscripciones.value && suscripciones.value.length > 0) {
    return suscripciones.value[0];
  }
  return null;
});

const listaFuncionalidades = computed(() =>
  Object.entries(acceso.value?.funcionalidades ?? {})
    .filter(([, habilitada]) => habilitada)
    .map(([funcionalidad]) => funcionalidad.replaceAll('_', ' ')),
);

function formatearFecha(isoString) {
  if (!isoString) return '—';
  try {
    const d = new Date(isoString);
    return new Intl.DateTimeFormat('es-MX', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    }).format(d);
  } catch {
    return isoString;
  }
}

function abrirConfirmacionCancelar() {
  sheetCancelarAbierto.value = true;
}

async function ejecutarCancelar() {
  sheetCancelarAbierto.value = false;
  if (suscripcionPrincipal.value?.id) {
    await cancelarRenovacion(suscripcionPrincipal.value.id);
  }
}

function abrirFacturaParaOrden(ordenId, importe) {
  ordenFacturaId.value = ordenId || 'ord-general';
  ordenFacturaImporte.value = importe || '0.00';
  modalFacturaAbierto.value = true;
}

async function onSolicitarFactura(datos) {
  enviandoFactura.value = true;
  try {
    await enviarSolicitudFactura(datos);
    modalFacturaAbierto.value = false;
    tabActiva.value = 'facturas';
  } catch (err) {
    console.error(err);
  } finally {
    enviandoFactura.value = false;
  }
}
</script>

<style scoped>
.suscripcion-page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem 1rem 3rem;
}

.header-pretitle {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--primary);
  margin-bottom: 0.35rem;
}

.suscripcion-content-grid {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* 1. Main Plan Card */
.main-plan-card {
  padding: 1.75rem;
  border-radius: var(--radius-lg);
  background: var(--bg-card);
  border: 1px solid var(--border);
}

.main-plan-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 1.5rem;
}

.plan-type-label {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-light);
  display: block;
  margin-bottom: 0.2rem;
}

.main-plan-name {
  font-size: 1.5rem;
  font-weight: 900;
  color: var(--text-main);
  margin: 0;
}

.plan-badges-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.plan-details-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 1rem 1.25rem;
  margin-bottom: 1.5rem;
}

.detail-cell {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-label {
  font-size: 0.75rem;
  color: var(--text-light);
  text-transform: uppercase;
  font-weight: 700;
}

.detail-val {
  font-size: 0.95rem;
  color: var(--text-main);
}

.cancel-scheduled-alert {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  background: var(--warning-bg);
  border: 1px solid var(--warning-border);
  color: var(--warning-text);
  border-radius: var(--radius-md);
  padding: 0.85rem 1rem;
  font-size: 0.84rem;
  line-height: 1.4;
  margin-bottom: 1.5rem;
}

.main-plan-actions {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  flex-wrap: wrap;
}

.text-danger-btn {
  color: var(--danger);
  border-color: var(--danger-border);
}

.text-danger-btn:hover {
  background: var(--danger-bg);
}

/* 2. Limits Card */
.limits-card {
  padding: 1.5rem;
  border-radius: var(--radius-lg);
  background: var(--bg-card);
  border: 1px solid var(--border);
}

.section-title-sm {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--text-main);
  margin: 0 0 1.25rem;
}

.limits-metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.metric-box {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1.15rem;
}

.metric-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.metric-name {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-muted);
}

.metric-val {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}

.metric-val .num {
  font-size: 1.75rem;
  font-weight: 900;
  color: var(--text-main);
}

.metric-val .unit {
  font-size: 0.78rem;
  color: var(--text-light);
}

.features-enabled-box {
  background: var(--bg-surface);
  border-radius: var(--radius-md);
  padding: 1rem;
}

.features-box-title {
  display: block;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-light);
  margin-bottom: 0.65rem;
}

.features-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.feature-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-full);
  padding: 0.3rem 0.75rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-main);
}

/* 3. Tabs Section */
.tabs-section-card {
  padding: 1.5rem;
  border-radius: var(--radius-lg);
  background: var(--bg-card);
  border: 1px solid var(--border);
}

.tabs-header {
  display: flex;
  gap: 0.5rem;
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: 0.75rem;
  margin-bottom: 1.25rem;
  overflow-x: auto;
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  background: transparent;
  border: none;
  padding: 0.5rem 0.85rem;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-muted);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.tab-btn:hover {
  color: var(--text-main);
  background: var(--bg-surface);
}

.tab-btn.active {
  color: var(--primary);
  background: var(--primary-light);
}

.tab-pane {
  min-height: 200px;
}

.comprobantes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.comprobante-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
}

.comprobante-icon-box {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-sm);
  background: var(--primary-light);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.comprobante-info {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  flex: 1;
}

.comprobante-folio {
  font-weight: 800;
  font-size: 0.85rem;
  color: var(--text-main);
}

.comprobante-date {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.comprobante-amount {
  font-size: 0.88rem;
  color: var(--text-main);
}

.download-btn {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.facturas-topbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1.25rem;
  flex-wrap: wrap;
}

.facturas-heading {
  font-size: 0.95rem;
  font-weight: 800;
  color: var(--text-main);
  margin: 0;
}

.facturas-subheading {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin: 0.15rem 0 0;
}
</style>
