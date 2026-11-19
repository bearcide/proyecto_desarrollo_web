import { ref } from 'vue';
import api, { obtenerMensajeError } from '../../../../api';
import { extraerContador, extraerRegistros } from '../services/normalizarComercial';

/**
 * Gestor genérico de listas del panel comercial.
 *
 * Responsabilidades:
 * - Llamar al endpoint del dominio indicado.
 * - Normalizar respuestas paginadas (DRF) o listas planas.
 * - Exponer estado de carga, error, registros, total, página y links DRF.
 *
 * No decide filtros: recibe un objeto plano de query params.
 */
export function useListaComercial({ url, mapearItem }) {
  const cargando = ref(false);
  const error = ref(null);
  const registros = ref([]);
  const total = ref(0);
  const paginaActual = ref(1);
  const urlSiguiente = ref(null);
  const urlAnterior = ref(null);

  async function cargar(pagina = 1, filtros = {}) {
    cargando.value = true;
    error.value = null;

    const params = { page: pagina };
    Object.entries(filtros || {}).forEach(([clave, valor]) => {
      const limpio = typeof valor === 'string' ? valor.trim() : valor;
      if (limpio !== '' && limpio !== null && limpio !== undefined) {
        params[clave] = limpio;
      }
    });

    try {
      const { data } = await api.get(url, { params });
      const resultados = extraerRegistros(data);
      registros.value = mapearItem ? resultados.map(mapearItem) : resultados;
      total.value = extraerContador(data, resultados.length);
      paginaActual.value = Number(pagina) || 1;
      urlSiguiente.value = data?.next ?? null;
      urlAnterior.value = data?.previous ?? null;
      return { registros: registros.value, total: total.value };
    } catch (err) {
      error.value = err?.message || obtenerMensajeError(err);
      registros.value = [];
      return { registros: [], total: 0 };
    } finally {
      cargando.value = false;
    }
  }

  return {
    registros,
    total,
    cargando,
    error,
    paginaActual,
    urlSiguiente,
    urlAnterior,
    cargar,
  };
}
