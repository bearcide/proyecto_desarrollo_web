import { ref } from 'vue';
import { RUTAS_COMERCIALES, obtenerPlanesComerciales } from '../services/apiComercial';
import { useListaComercial } from './useListaComercial';
import { normalizarPlanComercial } from '../services/normalizarComercial';

/** Catálogo comercial de planes: precios, periodicidad, límites, módulos y disponibilidad. */
export function usePlanesComerciales() {
  const planes = useListaComercial({
    url: RUTAS_COMERCIALES.planes,
    mapearItem: normalizarPlanComercial,
  });

  async function cargarPlanes(pagina = 1, filtros = {}) {
    return planes.cargar(pagina, filtros);
  }

  return {
    planes: planes.registros,
    total: planes.total,
    cargando: planes.cargando,
    error: planes.error,
    paginaActual: planes.paginaActual,
    urlSiguiente: planes.urlSiguiente,
    urlAnterior: planes.urlAnterior,
    cargarPlanes,
  };
}
