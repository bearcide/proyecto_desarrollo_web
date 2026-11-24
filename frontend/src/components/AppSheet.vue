<template>
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="abierto" class="sheet-overlay" @click.self="cerrar">
        <div
          ref="panelRef"
          class="sheet-panel"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="idTitulo"
          tabindex="-1"
          @keydown.esc.prevent="cerrar"
          @keydown.tab="atraparFoco"
        >
          <header class="sheet-header">
            <div class="sheet-header-text">
              <h2 :id="idTitulo" class="sheet-title">{{ titulo }}</h2>
              <p v-if="subtitulo" class="sheet-subtitle">{{ subtitulo }}</p>
            </div>
            <button ref="cerrarRef" type="button" class="sheet-close" aria-label="Cerrar" @click="cerrar">
              <AppIcon name="x" :size="18" />
            </button>
          </header>

          <div class="sheet-body">
            <slot />
          </div>

          <footer v-if="$slots.footer" class="sheet-footer">
            <slot name="footer" />
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
/** Hoja informativa (HIG sheet): se cierra con Escape, clic fuera o el botón ×, y mantiene el foco dentro. */
import { ref, watch, nextTick } from 'vue';
import AppIcon from './AppIcon.vue';

const props = defineProps({
  abierto: { type: Boolean, default: false },
  titulo: { type: String, required: true },
  subtitulo: { type: String, default: '' },
});
const emit = defineEmits(['cerrar']);

const idTitulo = `sheet-info-${Math.random().toString(36).slice(2, 8)}`;
const panelRef = ref(null);
const cerrarRef = ref(null);
let focoPrevio = null;

watch(
  () => props.abierto,
  async (abierto) => {
    if (abierto) {
      focoPrevio = document.activeElement;
      await nextTick();
      cerrarRef.value?.focus();
    } else if (focoPrevio?.focus) {
      focoPrevio.focus();
      focoPrevio = null;
    }
  },
);

function cerrar() {
  emit('cerrar');
}

function atraparFoco(e) {
  const focusables = panelRef.value?.querySelectorAll('button:not([disabled]), [href], input, [tabindex]:not([tabindex="-1"])');
  if (!focusables?.length) return;
  const primero = focusables[0];
  const ultimo = focusables[focusables.length - 1];
  if (e.shiftKey && document.activeElement === primero) {
    e.preventDefault();
    ultimo.focus();
  } else if (!e.shiftKey && document.activeElement === ultimo) {
    e.preventDefault();
    primero.focus();
  }
}
</script>

<style scoped>
.sheet-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  background-color: rgba(0, 0, 0, 0.35);
}

.sheet-panel {
  width: 100%;
  max-width: 540px;
  max-height: calc(100vh - 3rem);
  display: flex;
  flex-direction: column;
  outline: none;
  background-color: var(--glass-bg);
  -webkit-backdrop-filter: blur(30px) saturate(180%);
  backdrop-filter: blur(30px) saturate(180%);
  border: 1px solid var(--glass-border);
  border-radius: 20px;
  box-shadow: inset 0 1px 0 var(--glass-highlight), 0 30px 70px -10px rgba(0, 0, 0, 0.35);
}

@media (prefers-reduced-transparency: reduce), (prefers-contrast: more) {
  .sheet-panel {
    background-color: var(--bg-card);
    -webkit-backdrop-filter: none;
    backdrop-filter: none;
  }
}

.sheet-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.25rem 1.25rem 0.75rem 1.5rem;
}

.sheet-title {
  font-size: 1.375rem; /* 22px · Title 2 */
  font-weight: 700;
  color: var(--text-main);
}

.sheet-subtitle {
  margin-top: 0.2rem;
  font-size: 0.9375rem;
  color: var(--text-muted);
}

.sheet-close {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 50%;
  background-color: var(--bg-surface);
  color: var(--text-muted);
  cursor: pointer;
}

.sheet-close:hover {
  color: var(--text-main);
}

.sheet-body {
  padding: 0.5rem 1.5rem 1.25rem;
  overflow-y: auto;
}

.sheet-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 0 1.5rem 1.5rem;
}

.sheet-enter-active,
.sheet-leave-active {
  transition: opacity 0.22s ease;
}

.sheet-enter-active .sheet-panel,
.sheet-leave-active .sheet-panel {
  transition: transform 0.28s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.sheet-enter-from,
.sheet-leave-to {
  opacity: 0;
}

.sheet-enter-from .sheet-panel,
.sheet-leave-to .sheet-panel {
  transform: translateY(24px) scale(0.98);
}
</style>
