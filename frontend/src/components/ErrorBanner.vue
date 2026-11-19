<template>
  <div class="alert alert-danger error-banner" role="alert">
    <AppIcon name="alert" :size="20" class="error-banner-icon" />
    <div class="error-banner-text">
      <strong>{{ titulo }}</strong>
      <span>{{ mensaje }}</span>
    </div>
    <button
      v-if="reintentable"
      type="button"
      class="btn btn-secondary btn-sm"
      :disabled="cargando"
      @click="$emit('reintentar')"
    >
      <AppIcon name="refresh" :size="14" />
      Reintentar
    </button>
  </div>
</template>

<script setup>
import AppIcon from './AppIcon.vue';

defineProps({
  mensaje: { type: String, required: true },
  titulo: { type: String, default: 'Algo salió mal' },
  reintentable: { type: Boolean, default: true },
  cargando: { type: Boolean, default: false },
});
defineEmits(['reintentar']);
</script>

<style scoped>
.error-banner {
  align-items: center;
}

.error-banner-icon {
  flex-shrink: 0;
}

.error-banner-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}
</style>
