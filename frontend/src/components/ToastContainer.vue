<template>
  <div class="toast-container" aria-live="polite">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      :class="['toast', `toast-${toast.type}`]"
      role="status"
    >
      <div class="toast-content">
        <span class="toast-icon">
          <svg v-if="toast.type === 'success'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          <svg v-else-if="toast.type === 'danger'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          <svg v-else-if="toast.type === 'warning'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
        </span>
        <span class="toast-message">{{ toast.message }}</span>
      </div>
      <button
        type="button"
        class="toast-close"
        aria-label="Cerrar notificación"
        @click="notifStore.remove(toast.id)"
      >
        ×
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useNotificationStore } from '../stores/notification';

const notifStore = useNotificationStore();
const toasts = computed(() => notifStore.toasts);
</script>

<style scoped>
.toast-content {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}
.toast-icon {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}
.toast-success .toast-icon { color: var(--success); }
.toast-danger .toast-icon { color: var(--danger); }
.toast-warning .toast-icon { color: var(--warning); }
.toast-message {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-main);
}
.toast-close {
  background: none;
  border: none;
  font-size: 1.25rem;
  color: var(--text-light);
  cursor: pointer;
  padding: 0 0.25rem;
  line-height: 1;
}
.toast-close:hover {
  color: var(--text-main);
}
</style>
