/**
 * Tema claro/oscuro compartido por toda la app.
 *
 * - Por defecto sigue la configuración del sistema (prefers-color-scheme) y
 *   reacciona en vivo si el usuario la cambia.
 * - El botón de alternar guarda una preferencia explícita. Si esa preferencia
 *   coincide con la del sistema, se descarta y se vuelve a seguir al sistema.
 * - El tema efectivo se escribe en <html data-theme="light|dark">; los estilos
 *   leen ese atributo. index.html lo aplica antes del primer pintado.
 */
import { ref, computed, watchEffect } from 'vue';

const STORAGE_KEY = 'ime-theme';

function leerPreferencia() {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    return v === 'light' || v === 'dark' ? v : null;
  } catch {
    return null;
  }
}

function guardarPreferencia(v) {
  try {
    if (v) localStorage.setItem(STORAGE_KEY, v);
    else localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* almacenamiento no disponible: el tema solo dura la sesión */
  }
}

const media = typeof window !== 'undefined' && window.matchMedia
  ? window.matchMedia('(prefers-color-scheme: dark)')
  : null;

const preferencia = ref(leerPreferencia());
const sistemaOscuro = ref(media ? media.matches : false);
media?.addEventListener?.('change', (e) => {
  sistemaOscuro.value = e.matches;
});

const tema = computed(() => preferencia.value ?? (sistemaOscuro.value ? 'dark' : 'light'));
const esOscuro = computed(() => tema.value === 'dark');

if (typeof document !== 'undefined') {
  watchEffect(() => {
    document.documentElement.dataset.theme = tema.value;
  });
}

function alternarTema() {
  const nuevo = esOscuro.value ? 'light' : 'dark';
  const delSistema = sistemaOscuro.value ? 'dark' : 'light';
  preferencia.value = nuevo === delSistema ? null : nuevo;
  guardarPreferencia(preferencia.value);

  // Transición suave de colores solo durante el cambio
  const root = document.documentElement;
  root.classList.add('theme-transition');
  window.setTimeout(() => root.classList.remove('theme-transition'), 350);
}

export function useTheme() {
  return { tema, esOscuro, alternarTema };
}
