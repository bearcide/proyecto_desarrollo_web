<template>
  <div class="card summary-card">
    <div class="summary-header">
      <AppIcon name="file-text" size="20" class="summary-icon" />
      <h3 class="summary-title">Resumen de Contratación</h3>
    </div>

    <div v-if="plan && precio" class="summary-body">
      <div class="summary-plan-badge">
        <span class="plan-tag">{{ plan.nombre }}</span>
        <ModalidadBadge :modalidad="precio.modalidad" />
      </div>

      <div class="summary-breakdown">
        <div class="breakdown-row">
          <span class="concept-label">Tarifa base ({{ precio.modalidad }}):</span>
          <span class="concept-val">{{ formatearMoneda(desglose.base, desglose.moneda) }}</span>
        </div>

        <div v-if="desglose.cuotaAlumnos > 0" class="breakdown-row">
          <span class="concept-label">
            Cuota por matrícula ({{ alumnos }} alumnos × {{ formatearMoneda(precio.por_alumno, desglose.moneda) }}):
          </span>
          <span class="concept-val">+ {{ formatearMoneda(desglose.cuotaAlumnos, desglose.moneda) }}</span>
        </div>

        <div v-if="desglose.cuotaPlanteles > 0" class="breakdown-row">
          <span class="concept-label">
            Planteles adicionales ({{ planteles - 1 }} extra):
          </span>
          <span class="concept-val">+ {{ formatearMoneda(desglose.cuotaPlanteles, desglose.moneda) }}</span>
        </div>

        <div v-if="desglose.costoAddOns > 0" class="breakdown-row">
          <span class="concept-label">Módulos & soporte adicional:</span>
          <span class="concept-val">+ {{ formatearMoneda(desglose.costoAddOns, desglose.moneda) }}</span>
        </div>
      </div>

      <div class="summary-total-box">
        <div class="total-row">
          <span class="total-label">Total Estimado</span>
          <div class="total-amount-wrapper">
            <span class="total-amount">{{ formatearMoneda(desglose.total, desglose.moneda) }}</span>
            <span class="total-currency">{{ desglose.moneda }}</span>
          </div>
        </div>
        <p class="backend-seal-notice">
          <AppIcon name="shield" size="14" />
          <span>El cálculo definitivo es validado y sellado inmutablemente por el backend (Django REST).</span>
        </p>
      </div>

      <button
        type="button"
        class="btn btn-primary btn-block checkout-action-btn"
        :disabled="cargando"
        @click="$emit('procederCheckout')"
      >
        <span v-if="cargando" class="spinner spinner-white"></span>
        <span v-else>Continuar al Checkout Seguro</span>
        <AppIcon v-if="!cargando" name="arrow-right" size="16" />
      </button>

      <div class="guarantee-box">
        <div class="guarantee-item">
          <AppIcon name="lock" size="14" />
          <span>Sin captura de tarjetas en el navegador</span>
        </div>
        <div class="guarantee-item">
          <AppIcon name="check-circle" size="14" />
          <span>Facturación CFDI e IVA desglosado</span>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <AppIcon name="sliders" size="24" class="text-muted" />
      <p class="text-muted text-sm" style="margin-top: 0.5rem;">
        Selecciona un plan y modalidad para proyectar la cotización.
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import AppIcon from '../../../../components/AppIcon.vue';
import ModalidadBadge from './ModalidadBadge.vue';
import { formatearMoneda, calcularTotalEstimado } from '../domain/comercialCalculos';

const props = defineProps({
  plan: {
    type: Object,
    default: null,
  },
  precio: {
    type: Object,
    default: null,
  },
  alumnos: {
    type: Number,
    default: 1,
  },
  planteles: {
    type: Number,
    default: 1,
  },
  addOns: {
    type: Array,
    default: () => [],
  },
  cargando: {
    type: Boolean,
    default: false,
  },
});

defineEmits(['procederCheckout']);

const desglose = computed(() => {
  return calcularTotalEstimado({
    precio: props.precio,
    alumnos: props.alumnos,
    planteles: props.planteles,
    addOns: props.addOns,
  });
});
</script>

<style scoped>
.summary-card {
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  background: var(--bg-card);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  position: sticky;
  top: 1rem;
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--border-subtle);
}

.summary-icon {
  color: var(--primary);
}

.summary-title {
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--text-main);
  margin: 0;
}

.summary-plan-badge {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
  padding: 0.5rem 0.75rem;
  background: var(--bg-surface);
  border-radius: var(--radius-sm);
}

.plan-tag {
  font-weight: 700;
  font-size: 0.88rem;
  color: var(--text-main);
}

.summary-breakdown {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  margin-bottom: 1.25rem;
  font-size: 0.84rem;
}

.breakdown-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.5rem;
}

.concept-label {
  color: var(--text-muted);
}

.concept-val {
  font-weight: 600;
  color: var(--text-main);
  text-align: right;
  white-space: nowrap;
}

.summary-total-box {
  background: var(--primary-light);
  border: 1px solid var(--primary-border);
  border-radius: var(--radius-md);
  padding: 1rem;
  margin-bottom: 1.25rem;
}

.total-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.total-label {
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--primary-dark);
  letter-spacing: 0.04em;
}

.total-amount-wrapper {
  display: flex;
  align-items: baseline;
  gap: 0.35rem;
}

.total-amount {
  font-size: 1.6rem;
  font-weight: 900;
  color: var(--text-main);
  letter-spacing: -0.02em;
}

.total-currency {
  font-size: 0.75rem;
  font-weight: 800;
  color: var(--primary);
}

.backend-seal-notice {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.72rem;
  color: var(--text-muted);
  margin: 0.65rem 0 0;
  line-height: 1.35;
}

.checkout-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-weight: 700;
  padding: 0.85rem 1rem;
  margin-bottom: 1rem;
}

.guarantee-box {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.guarantee-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
</style>
