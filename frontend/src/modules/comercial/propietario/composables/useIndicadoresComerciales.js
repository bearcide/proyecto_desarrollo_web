import { ref } from 'vue';
import { obtenerIndicadoresComerciales } from '../services/apiComercial';
import { normalizarIndicadores } from '../services/normalizarComercial';

/** Indicadores comerciales del dashboard del propietario SaaS. */
export function useIndicadoresComerciales() {
  const indicadores = ref(normalizarIndicadores(null));
  const cargando = ref(false);
  const error = ref(null);

  async function cargarIndicadores() {
    cargando.value = true;
    error.value = null;

    try {
      indicadores.value = normalizarIndicadores(await obtenerIndicadoresComerciales());
    } catch (err) {
      error.value = err?.response?.status ? `Error ${err.response.status} al cargar los indicadores comerciales.` : 'No pudimos cargar los indicadores comerciales.';
    } finally {
      cargando.value = false;
    }

    return indicadores.value;
  }

  return { indicadores, cargando, error, cargarIndicadores };
}
