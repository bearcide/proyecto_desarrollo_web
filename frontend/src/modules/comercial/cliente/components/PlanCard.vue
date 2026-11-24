<template>
  <div
    class="card plan-card"
    :class="{
      'plan-card-featured': plan.codigo === 'pro',
      'plan-card-selected': seleccionado,
    }"
  >
    <div v-if="plan.codigo === 'pro'" class="featured-ribbon">
      <AppIcon name="award" size="14" />
      <span>Más Recomendado</span>
    </div>

    <div class="plan-header">
      <div class="plan-title-row">
        <h3 class="plan-name">{{ plan.nombre }}</h3>
        <span class="badge badge-indigo">Código: {{ plan.codigo }}</span>
      </div>
      <p class="plan-desc">{{ plan.descripcion }}</p>
    </div>

    <!-- Selector de Modalidad disponible para este plan -->
    <div class="modalidades-selector" role="tablist" aria-label="Modalidades de contratación">
      <button
        v-for="precio in preciosPlan"
        :key="precio.id"
        type="button"
        role="tab"
        class="modalidad-tab-btn"
        :class="{ active: precioActivo?.id === precio.id }"
        :aria-selected="precioActivo?.id === precio.id"
        @click="precioActivo = precio"
      >
        <ModalidadBadge :modalidad="precio.modalidad" size="sm" />
      </button>
    </div>

    <!-- Precio Dinámico Oficial (desde API) -->
    <div class="plan-pricing-box">
      <div v-if="precioActivo" class="pricing-display">
        <div class="price-row">
          <span class="price-amount">{{ formatearMoneda(precioActivo.importe, precioActivo.moneda) }}</span>
          <span class="price-cadence">/ {{ obtenerTextoPeriodo(precioActivo) }}</span>
        </div>
        <div v-if="parseFloat(precioActivo.por_alumno) > 0" class="student-rate">
          + {{ formatearMoneda(precioActivo.por_alumno, precioActivo.moneda) }} por alumno activo
        </div>
        <div v-else class="student-rate text-success">
          Alumnos incluidos sin cargo marginal
        </div>
      </div>
      <div v-else class="pricing-empty">
        <span class="text-muted text-sm">Modalidad bajo cotización personalizada</span>
      </div>
    </div>

    <!-- Límites Institucionales -->
    <div class="plan-limits-strip">
      <div class="limit-item">
        <AppIcon name="user" size="14" />
        <span>Hasta {{ plan.max_alumnos.toLocaleString() }} alumnos</span>
      </div>
      <div class="limit-item">
        <AppIcon name="building" size="14" />
        <span>{{ plan.max_planteles }} {{ plan.max_planteles === 1 ? 'plantel' : 'planteles' }}</span>
      </div>
    </div>

    <!-- Lista de Funcionalidades -->
    <div class="plan-features">
      <h4 class="features-title">Funcionalidades incluidas:</h4>
      <ul class="features-list">
        <li v-for="(func, idx) in listaFuncionalidades" :key="idx" class="feature-item">
          <AppIcon name="check-circle" size="16" class="feature-icon" />
          <span>{{ func }}</span>
        </li>
      </ul>
    </div>

    <!-- Acciones -->
    <div class="plan-footer">
      <button
        type="button"
        class="btn btn-primary btn-block cta-btn"
        :disabled="!precioActivo"
        @click="emitContratar"
      >
        <span>Contratar Ahora</span>
        <AppIcon name="arrow-right" size="16" />
      </button>

      <button
        type="button"
        class="btn btn-outline btn-block config-btn"
        @click="emitConfigurar"
      >
        <AppIcon name="sliders" size="15" />
        <span>Configurar Parámetros</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import AppIcon from '../../../../components/AppIcon.vue';
import ModalidadBadge from './ModalidadBadge.vue';
import { formatearMoneda, MODALIDADES } from '../domain/comercialCalculos';

const props = defineProps({
  plan: {
    type: Object,
    required: true,
  },
  precios: {
    type: Array,
    default: () => [],
  },
  seleccionado: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['contratar', 'configurar']);

const preciosPlan = computed(() => {
  return props.precios.filter((p) => p.plan === props.plan.id && p.activo);
});

// Preseleccionar anual o mensual por defecto
const precioActivo = ref(null);

watch(
  preciosPlan,
  (nuevos) => {
    if (nuevos && nuevos.length > 0) {
      const preferido =
        nuevos.find((p) => p.modalidad === 'annual') ||
        nuevos.find((p) => p.modalidad === 'monthly') ||
        nuevos[0];
      precioActivo.value = preferido;
    } else {
      precioActivo.value = null;
    }
  },
  { immediate: true },
);

const listaFuncionalidades = computed(() => {
  if (Array.isArray(props.plan.funcionalidades)) {
    return props.plan.funcionalidades;
  }
  if (props.plan.funcionalidades && typeof props.plan.funcionalidades === 'object') {
    return Object.keys(props.plan.funcionalidades).filter((k) => props.plan.funcionalidades[k]);
  }
  return [];
});

function obtenerTextoPeriodo(precio) {
  if (!precio) return 'periodo';
  switch (precio.modalidad) {
    case 'monthly':
      return 'mes';
    case 'annual':
      return 'año';
    case 'process':
      return 'proceso de inscripción';
    case 'perpetual':
      return 'pago único vitalicio';
    case 'institutional':
      return 'año institucional';
    default:
      return precio.dias ? `${precio.dias} días` : 'periodo';
  }
}

function emitContratar() {
  if (precioActivo.value) {
    emit('contratar', {
      plan: props.plan,
      precio: precioActivo.value,
    });
  }
}

function emitConfigurar() {
  emit('configurar', {
    plan: props.plan,
    precio: precioActivo.value,
  });
}
</script>

<style scoped>
.plan-card {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  border-radius: var(--radius-lg);
  padding: 1.75rem 1.5rem;
  background: var(--bg-card);
  border: 1px solid var(--border);
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.plan-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
  border-color: var(--primary-border);
}

.plan-card-featured {
  border-color: var(--primary);
  box-shadow: var(--shadow-md), 0 0 0 1px var(--primary);
}

.plan-card-selected {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}

.featured-ribbon {
  position: absolute;
  top: -12px;
  right: 20px;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: var(--accent);
  color: #ffffff;
  padding: 0.25rem 0.75rem;
  font-size: 0.72rem;
  font-weight: 800;
  border-radius: var(--radius-full);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  box-shadow: var(--shadow-sm);
}

.plan-header {
  margin-bottom: 1.25rem;
}

.plan-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.4rem;
}

.plan-name {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--text-main);
  margin: 0;
}

.plan-desc {
  font-size: 0.875rem;
  color: var(--text-muted);
  line-height: 1.45;
  margin: 0;
  min-height: 40px;
}

.modalidades-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  padding: 0.5rem;
  background: var(--bg-surface);
  border-radius: var(--radius-md);
  margin-bottom: 1.25rem;
}

.modalidad-tab-btn {
  background: transparent;
  border: none;
  padding: 0;
  cursor: pointer;
  border-radius: var(--radius-full);
  transition: opacity 0.15s ease, transform 0.15s ease;
  opacity: 0.65;
}

.modalidad-tab-btn:hover {
  opacity: 0.95;
}

.modalidad-tab-btn.active {
  opacity: 1;
  transform: scale(1.03);
}

.plan-pricing-box {
  margin-bottom: 1.25rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid var(--border-subtle);
}

.price-row {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}

.price-amount {
  font-size: 1.85rem;
  font-weight: 900;
  color: var(--text-main);
  letter-spacing: -0.02em;
}

.price-cadence {
  font-size: 0.85rem;
  color: var(--text-muted);
  font-weight: 600;
}

.student-rate {
  font-size: 0.8rem;
  margin-top: 0.25rem;
  color: var(--text-muted);
  font-weight: 500;
}

.plan-limits-strip {
  display: flex;
  gap: 1rem;
  padding: 0.65rem 0.85rem;
  background: var(--bg-surface);
  border-radius: var(--radius-sm);
  margin-bottom: 1.25rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-muted);
}

.limit-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.plan-features {
  flex: 1;
  margin-bottom: 1.5rem;
}

.features-title {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-light);
  font-weight: 700;
  margin-bottom: 0.75rem;
}

.features-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  font-size: 0.85rem;
  color: var(--text-main);
  line-height: 1.4;
}

.feature-icon {
  color: var(--success);
  flex-shrink: 0;
  margin-top: 0.15rem;
}

.plan-footer {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin-top: auto;
}

.cta-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-weight: 700;
  padding: 0.75rem 1rem;
}

.config-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-size: 0.82rem;
  padding: 0.55rem 0.85rem;
}
</style>
