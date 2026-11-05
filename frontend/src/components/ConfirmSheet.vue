<template>
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="abierto" class="sheet-overlay" @click.self="cancelar">
        <div
          ref="panelRef"
          class="sheet-panel"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="idTitulo"
          @keydown.esc.prevent="cancelar"
          @keydown.tab="atraparFoco"
        >
          <header class="sheet-header">
            <h2 :id="idTitulo" class="sheet-title">{{ titulo }}</h2>
            <p v-if="descripcion" class="sheet-desc">{{ descripcion }}</p>
          </header>

          <div class="sheet-body">
            <slot />
          </div>

          <footer class="sheet-actions">
            <button ref="cancelarRef" type="button" class="btn btn-secondary btn-lg" @click="cancelar">
              {{ textoCancelar }}
            </button>
            <button type="button" class="btn btn-primary btn-lg" @click="$emit('confirmar')">
              {{ textoConfirmar }}
            </button>
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';

const props = defineProps({
  abierto: { type: Boolean, default: false },
  titulo: { type: String, required: true },
  descripcion: { type: String, default: '' },
  textoConfirmar: { type: String, default: 'Confirmar' },
  textoCancelar: { type: String, default: 'Cancelar' },
});
const emit = defineEmits(['confirmar', 'cancelar']);

const idTitulo = `sheet-titulo-${Math.random().toString(36).slice(2, 8)}`;
const panelRef = ref(null);
const cancelarRef = ref(null);
let focoPrevio = null;

watch(
  () => props.abierto,
  async (abierto) => {
    if (abierto) {
      focoPrevio = document.activeElement;
      await nextTick();
      // Foco en la acción segura (Cancelar), como recomienda la HIG
      cancelarRef.value?.focus();
    } else if (focoPrevio?.focus) {
      focoPrevio.focus();
      focoPrevio = null;
    }
  },
);

function cancelar() {
  emit('cancelar');
}

// Mantiene el foco del teclado dentro del diálogo
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
  max-width: 480px;
  max-height: calc(100vh - 3rem);
  display: flex;
  flex-direction: column;
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
  padding: 1.5rem 1.5rem 0.75rem;
  text-align: center;
}

.sheet-title {
  font-size: 1.375rem; /* 22px · Title 2 */
  font-weight: 700;
  color: var(--text-main);
}

.sheet-desc {
  margin-top: 0.35rem;
  font-size: 0.9375rem;
  color: var(--text-muted);
}

.sheet-body {
  padding: 0.5rem 1.5rem;
  overflow-y: auto;
}

.sheet-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  padding: 1rem 1.5rem 1.5rem;
}

.sheet-actions .btn {
  min-height: 48px;
  border-radius: 12px;
}

/* Aparición: el panel sube y se desvanece el fondo */
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
