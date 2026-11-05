<template>
  <button
    type="button"
    class="theme-toggle"
    :aria-label="esOscuro ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'"
    :title="esOscuro ? 'Modo claro' : 'Modo oscuro'"
    @click="alternarTema"
  >
    <Transition name="icono" mode="out-in">
      <!-- En modo oscuro se ofrece el sol (pasar a claro) -->
      <svg v-if="esOscuro" key="sol" aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="4"/>
        <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>
      </svg>
      <!-- En modo claro se ofrece la luna (pasar a oscuro) -->
      <svg v-else key="luna" aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>
      </svg>
    </Transition>
  </button>
</template>

<script setup>
import { useTheme } from '../composables/useTheme';

const { esOscuro, alternarTema } = useTheme();
</script>

<style scoped>
.theme-toggle {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border-radius: 50%;
  border: 1px solid var(--glass-border);
  background-color: var(--glass-bg);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  backdrop-filter: blur(20px) saturate(180%);
  box-shadow: var(--shadow-xs);
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.15s ease, background-color 0.15s ease, transform 0.15s ease;
}

.theme-toggle:hover {
  color: var(--accent-text);
}

.theme-toggle:active {
  transform: scale(0.94);
}

@media (prefers-reduced-transparency: reduce), (prefers-contrast: more) {
  .theme-toggle {
    background-color: var(--bg-card);
    -webkit-backdrop-filter: none;
    backdrop-filter: none;
  }
}

/* Cambio de icono: gira y aparece */
.icono-enter-active,
.icono-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.icono-enter-from {
  opacity: 0;
  transform: rotate(-90deg) scale(0.6);
}

.icono-leave-to {
  opacity: 0;
  transform: rotate(90deg) scale(0.6);
}
</style>
