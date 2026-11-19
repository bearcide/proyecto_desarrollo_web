<template>
  <span class="badge estado-badge" :class="info.badge" :title="info.descripcion">
    <span class="punto-estado" :class="`punto-${info.tipo}`"></span>
    <span>{{ info.etiqueta }}</span>
  </span>
</template>

<script setup>
import { computed } from 'vue';
import { clasificarEstado } from '../domain/comercialCalculos';

const props = defineProps({
  estado: {
    type: String,
    required: true,
  },
});

const info = computed(() => clasificarEstado(props.estado));
</script>

<style scoped>
.estado-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-weight: 700;
  font-size: 0.75rem;
  padding: 0.25rem 0.65rem;
  border-radius: var(--radius-full);
}

.punto-estado {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.punto-success {
  background: var(--success);
}

.punto-warning {
  background: var(--warning);
}

.punto-danger {
  background: var(--danger);
}

.punto-neutral {
  background: var(--text-light);
}
</style>
