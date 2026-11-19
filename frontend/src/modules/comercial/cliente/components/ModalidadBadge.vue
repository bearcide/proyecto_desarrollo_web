<template>
  <span class="badge modalidad-badge" :class="claseEstilo" :title="infoModalidad.descripcion">
    <AppIcon :name="infoModalidad.icono" :size="iconSize" />
    <span>{{ infoModalidad.etiquetaCorta }}</span>
  </span>
</template>

<script setup>
import { computed } from 'vue';
import AppIcon from '../../../../components/AppIcon.vue';
import { MODALIDADES } from '../domain/comercialCalculos';

const props = defineProps({
  modalidad: {
    type: String,
    required: true,
  },
  size: {
    type: String,
    default: 'normal', // 'sm' | 'normal'
  },
});

const infoModalidad = computed(() => {
  return (
    MODALIDADES[props.modalidad] || {
      etiquetaCorta: props.modalidad,
      descripcion: 'Modalidad comercial',
      icono: 'award',
    }
  );
});

const iconSize = computed(() => (props.size === 'sm' ? 12 : 14));

const claseEstilo = computed(() => {
  switch (props.modalidad) {
    case 'annual':
      return 'badge-annual';
    case 'monthly':
      return 'badge-monthly';
    case 'process':
      return 'badge-process';
    case 'institutional':
    case 'perpetual':
      return 'badge-institutional';
    case 'enterprise':
      return 'badge-enterprise';
    default:
      return 'badge-neutral';
  }
});
</script>

<style scoped>
.modalidad-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  padding: 0.25rem 0.6rem;
  border-radius: var(--radius-full);
  font-size: 0.72rem;
}

.badge-annual {
  background: rgba(16, 185, 129, 0.12);
  color: var(--success);
  border: 1px solid var(--success-border);
}

.badge-monthly {
  background: var(--blue-light);
  color: var(--blue);
  border: 1px solid var(--blue-border);
}

.badge-process {
  background: var(--warning-bg);
  color: var(--warning-text);
  border: 1px solid var(--warning-border);
}

.badge-institutional {
  background: var(--primary-light);
  color: var(--primary);
  border: 1px solid var(--primary-border);
}

.badge-enterprise {
  background: var(--violet-light);
  color: var(--violet);
  border: 1px solid var(--violet-border);
}
</style>
