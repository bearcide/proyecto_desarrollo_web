<template>
  <div class="checkout-page">
    <div class="page-header">
      <div>
        <div class="header-pretitle">
          <AppIcon name="lock" size="16" class="text-success" />
          <span>Pasarela de Pago Segura e Idempotente</span>
        </div>
        <h1 class="page-title">Confirmación y Checkout Comercial</h1>
        <p class="page-subtitle">
          Revisa el resumen oficial antes de iniciar la transacción. Las credenciales bancarias se procesan
          exclusivamente mediante pasarela segura externa o autorización institucional DEMO.
        </p>
      </div>

      <div class="header-actions">
        <router-link to="/admin/comercial/configurador" class="btn btn-secondary btn-sm">
          <AppIcon name="arrow-left" size="14" />
          <span>Modificar Parámetros</span>
        </router-link>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="error" class="alert alert-danger" role="alert">
      <AppIcon name="alert" size="18" />
      <span>{{ error }}</span>
    </div>

    <div v-if="cargando && !cotizacion" class="empty-state">
      <div class="spinner spinner-primary" style="margin: 0 auto 0.75rem;"></div>
      <span class="text-muted">Cargando condiciones oficiales de la orden…</span>
    </div>

    <div v-else-if="plan && precio && cotizacion" class="checkout-layout">
      <!-- Columna Izquierda: Información de la Institución y Declaraciones -->
      <div class="checkout-details-column">
        <!-- Tarjeta de Institución Contratante -->
        <div class="card checkout-card">
          <div class="card-section-title">
            <AppIcon name="building" size="18" class="text-primary" />
            <h3>Institución Compradora</h3>
          </div>

          <div class="institution-info-box">
            <div class="info-row">
              <span class="label">Escuela:</span>
              <span class="val font-bold">{{ authStore.nombreEscuela }}</span>
            </div>
            <div class="info-row">
              <span class="label">Tenant Escolar (Aislamiento):</span>
              <code class="val-code">{{ authStore.tenantId || 'tenant-general' }}</code>
            </div>
            <div class="info-row">
              <span class="label">Administrador Responsable:</span>
              <span class="val">{{ authStore.matriculaOId }}</span>
            </div>
          </div>
        </div>

        <!-- Términos y Garantías de Seguridad -->
        <div class="card checkout-card">
          <div class="card-section-title">
            <AppIcon name="shield" size="18" class="text-success" />
            <h3>Garantías de Seguridad y Cumplimiento</h3>
          </div>

          <ul class="security-rules-list">
            <li class="security-rule-item">
              <AppIcon name="check-circle" size="18" class="text-success" />
              <div>
                <strong>Cero almacenamiento bancario local:</strong>
                <p>InscripcionMadeEasy jamás solicita ni almacena números de tarjeta ni CVV en servidores propios.</p>
              </div>
            </li>
            <li class="security-rule-item">
              <AppIcon name="check-circle" size="18" class="text-success" />
              <div>
                <strong>Idempotencia en cada intento:</strong>
                <p>Los reintentos de la misma compra conservan su clave.</p>
              </div>
            </li>
            <li class="security-rule-item">
              <AppIcon name="check-circle" size="18" class="text-success" />
              <div>
                <strong>Confirmación asíncrona verificada por Django:</strong>
                <p>El acceso institucional se activa únicamente cuando el backend valida la firma del webhook o la aprobación oficial.</p>
              </div>
            </li>
          </ul>

          <div class="terms-checkbox-wrapper">
            <label class="terms-label">
              <input
                type="checkbox"
                v-model="aceptaTerminos"
                class="terms-checkbox"
              />
              <span>
                He leído y acepto los términos de servicio, las políticas de retención de datos y las condiciones comerciales para la modalidad <strong>{{ precio.modalidad }}</strong>.
              </span>
            </label>
          </div>
        </div>
      </div>

      <!-- Columna Derecha: Snapshot de Compra y Botón de Pago -->
      <aside class="checkout-summary-column">
        <div class="card summary-box">
          <div class="summary-box-header">
            <h3>Resumen de la Transacción</h3>
            <span class="badge badge-indigo">Orden de Compra</span>
          </div>

          <div class="summary-plan-heading">
            <div class="plan-heading-text">
              <span class="plan-name">{{ plan.nombre }}</span>
              <span class="plan-code">Ref: {{ plan.codigo }}</span>
            </div>
            <ModalidadBadge :modalidad="precio.modalidad" />
          </div>

          <div class="summary-items-list">
            <div class="summary-item">
              <span class="item-name">Tarifa base institucional</span>
              <span class="item-val">{{ formatearMoneda(cotizacion.base, cotizacion.moneda) }}</span>
            </div>

            <div v-if="cotizacion.cuota_alumnos > 0" class="summary-item">
              <span class="item-name">
                Volumen contratado ({{ alumnos }} alumnos):
              </span>
              <span class="item-val">+ {{ formatearMoneda(cotizacion.cuota_alumnos, cotizacion.moneda) }}</span>
            </div>

          </div>

          <div class="summary-total-strip">
            <div>
              <span class="total-label">Total a Autorizar</span>
              <span class="iva-note">Precios en moneda nacional</span>
            </div>
            <div class="total-price-large">
              {{ formatearMoneda(cotizacion.total, cotizacion.moneda) }}
            </div>
          </div>

          <button
            type="button"
            class="btn btn-primary btn-block btn-lg checkout-btn"
            :disabled="!aceptaTerminos || procesando"
            @click="procesarCheckout"
          >
            <span v-if="procesando" class="spinner spinner-white"></span>
            <AppIcon v-else name="lock" size="18" />
            <span>{{ procesando ? 'Contactando Pasarela…' : 'Proceder al Pago Seguro' }}</span>
          </button>

          <p class="summary-footer-note">
            Al pulsar el botón serás transferido a Stripe Checkout HTTPS o a la sala de autorización DEMO de la plataforma.
          </p>
        </div>
      </aside>
    </div>

    <!-- Modal Informativo DEMO -->
    <DemoConfirmModal
      :abierto="modalDemoAbierto"
      :orden-id="ordenGeneradaId"
      @cerrar="modalDemoAbierto = false"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import AppIcon from '../../../../components/AppIcon.vue';
import ModalidadBadge from '../components/ModalidadBadge.vue';
import DemoConfirmModal from '../components/DemoConfirmModal.vue';
import { useAuthStore } from '../../../../stores/auth';
import { comercialService } from '../api/comercialService';
import { useComercial } from '../composables/useComercial';
import {
  formatearMoneda,
  generarIdempotencyKey,
} from '../domain/comercialCalculos';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const { cargando, error, planes, precios, cargarCatalogo, iniciarCheckout } = useComercial();

const plan = ref(null);
const precio = ref(null);
const alumnos = ref(1);
const cotizacion = ref(null);
const aceptaTerminos = ref(false);
const procesando = ref(false);

const modalDemoAbierto = ref(false);
const ordenGeneradaId = ref('');

let idempotencyKey;

onMounted(async () => {
  try {
    const intento = typeof route.query.intento === 'string' && /^[A-Za-z0-9_-]{8,100}$/.test(route.query.intento)
      ? route.query.intento
      : generarIdempotencyKey();
    idempotencyKey = intento;
    if (route.query.intento !== intento) {
      await router.replace({ query: { ...route.query, intento } });
    }
    await cargarCatalogo();

    precio.value = precios.value.find((item) => item.id === route.query.precio_id && item.activo);
    plan.value = planes.value.find((item) => item.id === precio.value?.plan && item.activo);
    if (!precio.value || !plan.value) {
      error.value = 'Selecciona un plan y una modalidad vigentes en el configurador.';
      return;
    }
    const cantidad = Number(route.query.alumnos);
    alumnos.value = Number.isInteger(cantidad) && cantidad >= 1
      ? Math.min(cantidad, plan.value.max_alumnos)
      : 1;
    cotizacion.value = await comercialService.cotizar({
      precioId: precio.value.id,
      alumnos: alumnos.value,
      contratoId: route.query.contrato_id,
    });
  } catch (err) {
    error.value = err.message;
  }
});

async function procesarCheckout() {
  if (!precio.value || !aceptaTerminos.value || procesando.value) return;

  procesando.value = true;
  try {
    const sesion = await iniciarCheckout({
      precioId: precio.value.id,
      alumnos: alumnos.value,
      contratoId: route.query.contrato_id || null,
      cotizacion: cotizacion.value,
      idempotencyKey,
    });

    ordenGeneradaId.value = sesion.orden;

    if (sesion.estado === 'paid') {
      await router.push({ name: 'admin-comercial-checkout-resultado', query: { orden_id: sesion.orden } });
    } else if (sesion.proveedor === 'stripe' && sesion.url) {
      // Redirección HTTPS oficial a Stripe Checkout
      window.location.href = sesion.url;
    } else if (sesion.proveedor === 'DEMO') {
      // Proveedor DEMO oficial (url: null según docs/CONTRATO_COMERCIAL_API.md)
      modalDemoAbierto.value = true;
    } else {
      error.value = 'La pasarela no proporcionó una sesión de checkout.';
    }
  } catch (err) {
    error.value = err.message;
  } finally {
    procesando.value = false;
  }
}
</script>

<style scoped>
.checkout-page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 1100px;
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
  color: var(--success);
  margin-bottom: 0.35rem;
}

.checkout-layout {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 1.75rem;
  align-items: flex-start;
}

@media (max-width: 900px) {
  .checkout-layout {
    grid-template-columns: 1fr;
  }
}

.checkout-details-column {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.checkout-card {
  padding: 1.5rem;
  border-radius: var(--radius-lg);
  background: var(--bg-card);
  border: 1px solid var(--border);
}

.card-section-title {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 1.25rem;
  padding-bottom: 0.65rem;
  border-bottom: 1px solid var(--border-subtle);
}

.card-section-title h3 {
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--text-main);
  margin: 0;
}

.institution-info-box {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  background: var(--bg-surface);
  border-radius: var(--radius-md);
  padding: 1rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
}

.info-row .label {
  color: var(--text-muted);
}

.val-code {
  font-size: 0.8rem;
  background: var(--bg-card);
  padding: 0.2rem 0.5rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  color: var(--primary);
}

.security-rules-list {
  list-style: none;
  padding: 0;
  margin: 0 0 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.security-rule-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  font-size: 0.85rem;
  line-height: 1.45;
}

.security-rule-item strong {
  display: block;
  color: var(--text-main);
  margin-bottom: 0.15rem;
}

.security-rule-item p {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.8rem;
}

.terms-checkbox-wrapper {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 1rem;
}

.terms-label {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  font-size: 0.82rem;
  color: var(--text-main);
  cursor: pointer;
  line-height: 1.45;
}

.terms-checkbox {
  margin-top: 0.2rem;
  accent-color: var(--primary);
  width: 18px;
  height: 18px;
}

/* Columna Resumen */
.summary-box {
  padding: 1.75rem;
  border-radius: var(--radius-lg);
  background: var(--bg-card);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-md);
  position: sticky;
  top: 1rem;
}

.summary-box-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.25rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--border-subtle);
}

.summary-box-header h3 {
  font-size: 1.15rem;
  font-weight: 800;
  margin: 0;
  color: var(--text-main);
}

.summary-plan-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.25rem;
  padding: 0.85rem;
  background: var(--bg-surface);
  border-radius: var(--radius-md);
}

.plan-name {
  display: block;
  font-weight: 800;
  font-size: 1rem;
  color: var(--text-main);
}

.plan-code {
  font-size: 0.75rem;
  color: var(--text-light);
  text-transform: uppercase;
}

.summary-items-list {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
  margin-bottom: 1.5rem;
  font-size: 0.84rem;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.summary-item.border-top {
  border-top: 1px dashed var(--border);
  padding-top: 0.75rem;
  margin-top: 0.25rem;
}

.item-name {
  color: var(--text-muted);
}

.item-val {
  color: var(--text-main);
  font-weight: 600;
}

.summary-total-strip {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  background: var(--primary-light);
  border: 1px solid var(--primary-border);
  border-radius: var(--radius-md);
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.total-label {
  display: block;
  font-weight: 800;
  font-size: 0.85rem;
  text-transform: uppercase;
  color: var(--primary-dark);
}

.iva-note {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.total-price-large {
  font-size: 1.65rem;
  font-weight: 900;
  color: var(--text-main);
}

.checkout-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.9rem;
  font-size: 0.95rem;
  font-weight: 800;
}

.summary-footer-note {
  font-size: 0.72rem;
  color: var(--text-muted);
  text-align: center;
  margin: 0.85rem 0 0;
  line-height: 1.35;
}
</style>
