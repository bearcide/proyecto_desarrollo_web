import { ref } from 'vue';
import { RUTAS_COMERCIALES } from '../services/apiComercial';
import { useListaComercial } from './useListaComercial';
import { normalizarPagoComercial, normalizarSolicitudFacturacion } from '../services/normalizarComercial';

/** Pagos y transacciones con filtros comerciales. */
export function useFacturacionComercial() {
  const pagos = useListaComercial({
    url: RUTAS_COMERCIALES.transacciones,
    mapearItem: normalizarPagoComercial,
  });

  const solicitudes = useListaComercial({
    url: RUTAS_COMERCIALES.facturas,
    mapearItem: normalizarSolicitudFacturacion,
  });

  const fechaInicio = ref('');
  const fechaFin = ref('');
  const institucionFiltro = ref('');
  const estadoPago = ref('');

  async function cargarPagos(pagina = 1) {
    const filtros = {};
    if (fechaInicio.value) filtros.fecha_inicio = fechaInicio.value;
    if (fechaFin.value) filtros.fecha_fin = fechaFin.value;
    if (institucionFiltro.value) filtros.escuela = institucionFiltro.value;
    if (estadoPago.value) filtros.estado = estadoPago.value;
    return pagos.cargar(pagina, filtros);
  }

  async function cargarSolicitudes(pagina = 1) {
    const filtros = {};
    if (estadoPago.value && estadoPago.value !== 'TODOS') filtros.estado = estadoPago.value;
    return solicitudes.cargar(pagina, filtros);
  }

  function establecerFechaInicio(valor) {
    fechaInicio.value = valor;
  }

  function establecerFechaFin(valor) {
    fechaFin.value = valor;
  }

  function establecerInstitucion(valor) {
    institucionFiltro.value = valor;
  }

  function establecerEstadoPago(valor) {
    estadoPago.value = valor;
  }

  function limpiarFiltros() {
    fechaInicio.value = '';
    fechaFin.value = '';
    institucionFiltro.value = '';
    estadoPago.value = '';
  }

  return {
    pagos: pagos.registros,
    pagosTotal: pagos.total,
    pagosCargando: pagos.cargando,
    pagosError: pagos.error,
    pagosPaginaActual: pagos.paginaActual,
    pagosUrlSiguiente: pagos.urlSiguiente,
    pagosUrlAnterior: pagos.urlAnterior,
    solicitudes: solicitudes.registros,
    solicitudesTotal: solicitudes.total,
    solicitudesCargando: solicitudes.cargando,
    solicitudesError: solicitudes.error,
    solicitudesPaginaActual: solicitudes.paginaActual,
    solicitudesUrlSiguiente: solicitudes.urlSiguiente,
    solicitudesUrlAnterior: solicitudes.urlAnterior,
    fechaInicio,
    fechaFin,
    institucionFiltro,
    estadoPago,
    cargarPagos,
    cargarSolicitudes,
    establecerFechaInicio,
    establecerFechaFin,
    establecerInstitucion,
    establecerEstadoPago,
    limpiarFiltros,
  };
}
