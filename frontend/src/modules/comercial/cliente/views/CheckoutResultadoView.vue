<template>
  <div class="resultado-page">
    <!-- Estado de Carga -->
    <div v-if="verificando" class="card result-card verificando-card">
      <div class="spinner spinner-primary spinner-lg" style="margin: 0 auto 1.5rem;"></div>
      <h2 class="result-title">Verificando Estado con el Servidor</h2>
      <p class="result-desc">
        Consultando la confirmación oficial en el backend Django REST…
        Por políticas de seguridad, el acceso sólo se otorga con confirmación verificada.
      </p>
    </div>

    <!-- Si no se especificó ID de orden -->
    <div v-else-if="!ordenId" class="card result-card warning-card">
      <div class="icon-circle icon-circle-warning">
        <AppIcon name="warning" size="32" class="text-warning" />
      </div>
      <h2 class="result-title">No se especificó una orden</h2>
      <p class="result-desc">
        No se recibió el identificador de orden en los parámetros de la URL.
        Puedes verificar el estado de tus compras en tu panel de suscripción.
      </p>
      <div class="result-actions">
        <router-link to="/admin/comercial/suscripcion" class="btn btn-primary">
          <span>Ir a Mi Suscripción</span>
          <AppIcon name="arrow-right" size="16" />
        </router-link>
      </div>
    </div>

    <!-- Estado 1: PAGO APROBADO (paid) -->
    <div v-else-if="orden?.estado === 'paid'" class="card result-card success-card">
      <div class="icon-circle icon-circle-success">
        <AppIcon name="check-circle" size="36" class="text-success" />
      </div>

      <span class="badge badge-success status-pill">Pago Confirmado por Django</span>
      <h1 class="result-title">¡Contratación Exitosa y Acreditada!</h1>
      <p v-if="orden.proveedor === 'DEMO'" class="result-desc">
        El propietario confirmó esta orden de demostración. No se efectuó un cargo bancario.
      </p>
      <p v-else class="result-desc">El servidor recibió la confirmación del pago de Stripe Sandbox.</p>

      <div class="order-receipt-box">
        <div class="receipt-header">
          <span class="receipt-title">Comprobante de Confirmación</span>
          <EstadoPagoBadge estado="paid" />
        </div>

        <div class="receipt-grid">
          <div class="receipt-item">
            <span class="label">Folio de Orden:</span>
            <code class="val">{{ orden.id }}</code>
          </div>
          <div class="receipt-item">
            <span class="label">Importe Acreditado:</span>
            <span class="val font-bold text-success">{{ formatearMoneda(orden.importe, orden.moneda) }}</span>
          </div>
          <div class="receipt-item">
            <span class="label">Alumnos en la cotización:</span>
            <span class="val">{{ orden.alumnos }} alumnos</span>
          </div>
          <div class="receipt-item">
            <span class="label">Proveedor de Cobro:</span>
            <span class="val uppercase">{{ orden.proveedor }}</span>
          </div>
        </div>
      </div>

      <div class="result-actions">
        <router-link to="/admin/comercial/suscripcion" class="btn btn-primary">
          <AppIcon name="credit-card" size="16" />
          <span>Ver Mi Suscripción & Licencias</span>
        </router-link>

        <button
          type="button"
          class="btn btn-secondary"
          @click="abrirModalFactura"
        >
          <AppIcon name="file-text" size="16" />
          <span>Registrar solicitud fiscal</span>
        </button>

        <router-link to="/admin/dashboard" class="btn btn-outline">
          <span>Ir al Dashboard Escolar</span>
        </router-link>
      </div>
    </div>

    <div v-else-if="errorConsulta" class="alert alert-danger" role="alert">
      <p>{{ errorConsulta }}</p>
      <button class="btn btn-secondary" :disabled="reconsultando" @click="verificarEstado">Reintentar consulta</button>
    </div>

    <!-- Estado 2: PENDIENTE DE CONFIRMACIÓN (pending) -->
    <div v-else-if="orden?.estado === 'pending'" class="card result-card pending-card">
      <div class="icon-circle icon-circle-warning">
        <AppIcon name="clock" size="36" class="text-warning" />
      </div>

      <span class="badge badge-warning status-pill">Pendiente de Confirmación</span>
      <h1 class="result-title">Transacción en Espera de Acreditación</h1>
      <p class="result-desc">
        <span v-if="route.query.retorno === 'cancelado'">Regresaste de Stripe sin completar el checkout. </span>
        La orden <strong>#{{ orden.id.substring(0, 8) }}…</strong> fue registrada en el backend.
        Estamos a la espera de la confirmación asíncrona del proveedor bancario (Stripe Webhook)
        o la aprobación del operador de la plataforma.
      </p>

      <div class="pending-notice-box">
        <AppIcon name="info" size="18" class="text-warning" />
        <span>
          <strong>Regla de seguridad:</strong> No declaramos un pago exitoso sin la confirmación sellada del servidor.
          Puedes reconsultar en cualquier momento.
        </span>
      </div>

      <div class="result-actions">
        <button
          type="button"
          class="btn btn-primary"
          :disabled="reconsultando"
          @click="verificarEstado"
        >
          <AppIcon name="refresh" size="16" :class="{ spinner: reconsultando }" />
          <span>{{ reconsultando ? 'Reconsultando…' : 'Volver a Consultar Estado' }}</span>
        </button>


        <router-link to="/admin/comercial/suscripcion" class="btn btn-outline">
          <span>Ir al Panel de Suscripciones</span>
        </router-link>
      </div>
    </div>

    <!-- Estado 3: RECHAZADO / FALLIDO (failed) -->
    <div v-else class="card result-card failed-card">
      <div class="icon-circle icon-circle-danger">
        <AppIcon name="x-circle" size="36" class="text-danger" />
      </div>

      <span class="badge badge-danger status-pill">Transacción No Completada</span>
      <h1 class="result-title">No se pudo procesar la contratación</h1>
      <p class="result-desc">
        El servidor registró el fallo de esta orden.
        No se realizó ningún cobro a tu cuenta institucional.
      </p>

      <div class="result-actions">
        <router-link to="/admin/comercial/checkout" class="btn btn-primary">
          <AppIcon name="refresh" size="16" />
          <span>Reintentar Proceso de Contratación</span>
        </router-link>

        <router-link to="/admin/comercial/planes" class="btn btn-secondary">
          <span>Volver al Catálogo de Planes</span>
        </router-link>
      </div>
    </div>

    <!-- Modal para solicitud de factura si la orden está pagada -->
    <FacturacionModal
      :abierto="modalFacturaAbierto"
      :orden-id="orden?.id"
      :importe="orden?.importe"
      :enviando="enviandoFactura"
      @cerrar="modalFacturaAbierto = false"
      @solicitar="onSolicitarFactura"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import AppIcon from '../../../../components/AppIcon.vue';
import EstadoPagoBadge from '../components/EstadoPagoBadge.vue';
import FacturacionModal from '../components/FacturacionModal.vue';
import { useComercial } from '../composables/useComercial';
import { formatearMoneda } from '../domain/comercialCalculos';

const route = useRoute();
const { consultarOrden, enviarSolicitudFactura } = useComercial();

const ordenId = ref('');
const orden = ref(null);
const errorConsulta = ref('');
const verificando = ref(true);
const reconsultando = ref(false);

const modalFacturaAbierto = ref(false);
const enviandoFactura = ref(false);

watch(() => route.query.orden_id, async (valor) => {
  ordenId.value = typeof valor === 'string' ? valor : '';
  orden.value = null;
  errorConsulta.value = '';
  reconsultando.value = false;
  verificando.value = Boolean(ordenId.value);
  if (ordenId.value) {
    await verificarEstado();
  }
}, { immediate: true });

async function verificarEstado() {
  const id = ordenId.value;
  if (!id) return;
  reconsultando.value = true;
  errorConsulta.value = '';
  try {
    const data = await consultarOrden(id);
    if (ordenId.value === id) orden.value = data;
  } catch (err) {
    if (ordenId.value === id) {
      orden.value = null;
      errorConsulta.value = err.message;
    }
  } finally {
    if (ordenId.value === id) {
      verificando.value = false;
      reconsultando.value = false;
    }
  }
}

function abrirModalFactura() {
  modalFacturaAbierto.value = true;
}

async function onSolicitarFactura(datos) {
  enviandoFactura.value = true;
  try {
    await enviarSolicitudFactura(datos);
    modalFacturaAbierto.value = false;
  } catch (err) {
    // Manejado en composable
  } finally {
    enviandoFactura.value = false;
  }
}
</script>

<style scoped>
.resultado-page {
  max-width: 780px;
  margin: 2rem auto 4rem;
  padding: 0 1rem;
}

.result-card {
  padding: 2.5rem 2rem;
  border-radius: var(--radius-lg);
  background: var(--bg-card);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-lg);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.verificando-card {
  padding: 4rem 2rem;
}

.icon-circle {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.25rem;
}

.icon-circle-success {
  background: var(--success-bg);
  border: 2px solid var(--success-border);
}

.icon-circle-warning {
  background: var(--warning-bg);
  border: 2px solid var(--warning-border);
}

.icon-circle-danger {
  background: var(--danger-bg);
  border: 2px solid var(--danger-border);
}

.status-pill {
  font-size: 0.75rem;
  font-weight: 800;
  margin-bottom: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.result-title {
  font-size: 1.5rem;
  font-weight: 900;
  color: var(--text-main);
  margin: 0 0 0.5rem;
  letter-spacing: -0.02em;
}

.result-desc {
  font-size: 0.92rem;
  color: var(--text-muted);
  line-height: 1.5;
  margin: 0 0 1.75rem;
  max-width: 580px;
}

.order-receipt-box {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1.25rem;
  width: 100%;
  max-width: 620px;
  margin-bottom: 2rem;
  text-align: left;
}

.receipt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.65rem;
  border-bottom: 1px solid var(--border-subtle);
}

.receipt-title {
  font-size: 0.85rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-muted);
}

.receipt-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.85rem;
  font-size: 0.84rem;
}

@media (max-width: 580px) {
  .receipt-grid {
    grid-template-columns: 1fr;
  }
}

.receipt-item {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.receipt-item .label {
  font-size: 0.72rem;
  color: var(--text-light);
  text-transform: uppercase;
  font-weight: 700;
}

.receipt-item .val {
  color: var(--text-main);
  word-break: break-all;
}

.pending-notice-box {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  background: var(--warning-bg);
  border: 1px solid var(--warning-border);
  border-radius: var(--radius-md);
  padding: 0.85rem 1.25rem;
  text-align: left;
  font-size: 0.82rem;
  color: var(--warning-text);
  line-height: 1.45;
  max-width: 620px;
  margin-bottom: 2rem;
}

.result-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.75rem;
}
</style>
