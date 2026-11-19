import { ref } from 'vue';
import { RUTAS_COMERCIALES, obtenerEscuelaComercial } from '../services/apiComercial';
import { useListaComercial } from './useListaComercial';
import { normalizarEscuelaComercial } from '../services/normalizarComercial';

/** Clientes comerciales: instituciones (escuelas) que contratan el SaaS. */
export function useClientesComerciales() {
  const escuelas = useListaComercial({
    url: RUTAS_COMERCIALES.instituciones,
    mapearItem: normalizarEscuelaComercial,
  });

  const busqueda = ref('');
  const estadoFiltro = ref('');
  const planFiltro = ref('');

  const clientes = escuelas.registros;

  async function cargarClientes(pagina = 1) {
    const filtros = {};
    const termino = busqueda.value.trim();
    if (termino) filtros.search = termino;
    if (estadoFiltro.value) filtros.estado = estadoFiltro.value;
    if (planFiltro.value) filtros.plan = planFiltro.value;
    return escuelas.cargar(pagina, filtros);
  }

  function establecerBusqueda(valor) {
    busqueda.value = valor;
  }

  function establecerEstado(valor) {
    estadoFiltro.value = valor;
  }

  function establecerPlan(valor) {
    planFiltro.value = valor;
  }

  function limpiarFiltros() {
    busqueda.value = '';
    estadoFiltro.value = '';
    planFiltro.value = '';
  }

  async function cargarCliente(id) {
    return await obtenerEscuelaComercial(id);
  }

  return {
    clientes,
    total: escuelas.total,
    cargando: escuelas.cargando,
    error: escuelas.error,
    paginaActual: escuelas.paginaActual,
    urlSiguiente: escuelas.urlSiguiente,
    urlAnterior: escuelas.urlAnterior,
    busqueda,
    estadoFiltro,
    planFiltro,
    cargarClientes,
    establecerBusqueda,
    establecerEstado,
    establecerPlan,
    limpiarFiltros,
    cargarCliente,
  };
}
