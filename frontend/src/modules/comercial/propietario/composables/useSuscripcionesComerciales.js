import { ref } from 'vue';
import { RUTAS_COMERCIALES, obtenerSuscripcionesComerciales, cancelarSuscripcionComercial } from '../services/apiComercial';
import { useListaComercial } from './useListaComercial';
import { normalizarSuscripcionComercial, normalizarEstado } from '../services/normalizarComercial';
import { usePermisosComerciales } from './usePermisosComerciales';
import { obtenerMensajeError } from '../../../../api';

/**
 * Suscripciones comerciales con contrato vigente asociado.
 *
 * Expone la cancelación programada (`cancel_at_period_end`) del contrato
 * publicado en `docs/CONTRATO_COMERCIAL_API.md` solo para el propietario SaaS.
 */
export function useSuscripcionesComerciales() {
  const suscripciones = useListaComercial({
    url: RUTAS_COMERCIALES.suscripciones,
    mapearItem: normalizarSuscripcionComercial,
  });

  const { esPropietario } = usePermisosComerciales();

  const estadoFiltro = ref('');
  const institucionFiltro = ref('');

  const cancelando = ref(false);
  const errorCancelar = ref(null);
  const cancelacion = ref(null);

  async function cargarSuscripciones(pagina = 1) {
    const filtros = {};
    if (estadoFiltro.value) filtros.estado = estadoFiltro.value;
    if (institucionFiltro.value) filtros.institucion = institucionFiltro.value;
    return suscripciones.cargar(pagina, filtros);
  }

  function establecerEstado(valor) {
    estadoFiltro.value = valor;
  }

  function establecerInstitucion(valor) {
    institucionFiltro.value = valor;
  }

  function limpiarFiltros() {
    estadoFiltro.value = '';
    institucionFiltro.value = '';
  }

  /**
   * Cancela la suscripción al final del periodo pagado.
   * Delega en el backend (`POST /comercial/suscripciones/{id}/cancelar/`).
   * Devuelve `{ ok, ...respuesta }` para que la UI distinga error y éxito.
   */
  async function cancelar(id) {
    if (!esPropietario.value) {
      const mensaje = 'Solo el propietario SaaS puede cancelar suscripciones comerciales.';
      errorCancelar.value = mensaje;
      return { ok: false, cancelada: false, error: mensaje };
    }

    cancelando.value = true;
    errorCancelar.value = null;
    try {
      const resultado = await cancelarSuscripcionComercial(id);
      cancelacion.value = resultado ?? null;
      await cargarSuscripciones(suscripciones.paginaActual.value);
      return { ok: true, ...(resultado ?? {}) };
    } catch (err) {
      errorCancelar.value = obtenerMensajeError(err);
      return { ok: false, cancelada: false, error: errorCancelar.value };
    } finally {
      cancelando.value = false;
    }
  }

  /**
   * Indica si el usuario con sesión actual puede cancelar la suscripción
   * mostrada (propietario SaaS y sin cancelación previa programada/confirmada).
   */
  function puedeActuar(suscripcion) {
    const estado = normalizarEstado(suscripcion?.estado);
    const cancelada = suscripcion?.cancelacionProgramada === true
      || suscripcion?.cancelada === true
      || estado === 'CANCELED';
    return esPropietario.value && !cancelada;
  }

  return {
    suscripciones: suscripciones.registros,
    total: suscripciones.total,
    cargando: suscripciones.cargando,
    error: suscripciones.error,
    paginaActual: suscripciones.paginaActual,
    urlSiguiente: suscripciones.urlSiguiente,
    urlAnterior: suscripciones.urlAnterior,
    estadoFiltro,
    institucionFiltro,
    cancelando,
    errorCancelar,
    cancelacion,
    cargarSuscripciones,
    establecerEstado,
    establecerInstitucion,
    limpiarFiltros,
    cancelar,
    puedeActuar,
  };
}
