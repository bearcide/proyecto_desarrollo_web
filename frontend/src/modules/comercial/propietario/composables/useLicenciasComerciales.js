import { ref } from 'vue';
import { RUTAS_COMERCIALES, obtenerLicenciasComerciales, revocarLicenciaComercial } from '../services/apiComercial';
import { useListaComercial } from './useListaComercial';
import { normalizarLicenciaComercial, normalizarEstado } from '../services/normalizarComercial';
import { usePermisosComerciales } from './usePermisosComerciales';
import { obtenerMensajeError } from '../../../../api';

/**
 * Licencias institucionales emitidas sobre suscripciones vigentes.
 *
 * Expone la revocación permanente (`estado=revoked` + evento interno
 * auditable) solo para el propietario SaaS.
 */
export function useLicenciasComerciales() {
  const licencias = useListaComercial({
    url: RUTAS_COMERCIALES.licencias,
    mapearItem: normalizarLicenciaComercial,
  });

  const { esPropietario } = usePermisosComerciales();

  const estadoFiltro = ref('');
  const suscripcionFiltro = ref('');

  const revocando = ref(false);
  const errorRevocar = ref(null);
  const revocacion = ref(null);

  async function cargarLicencias(pagina = 1) {
    const filtros = {};
    if (estadoFiltro.value) filtros.estado = estadoFiltro.value;
    if (suscripcionFiltro.value) filtros.suscripcion = suscripcionFiltro.value;
    return licencias.cargar(pagina, filtros);
  }

  function establecerEstado(valor) {
    estadoFiltro.value = valor;
  }

  function establecerSuscripcion(valor) {
    suscripcionFiltro.value = valor;
  }

  function limpiarFiltros() {
    estadoFiltro.value = '';
    suscripcionFiltro.value = '';
  }

  /**
   * Revoca permanentemente la licencia de la institución contratante.
   * Delega en el backend (`POST /comercial/licencias/{id}/revocar/`).
   * Devuelve `{ ok, ...respuesta }` para que la UI distinga error y éxito.
   */
  async function revocar(id) {
    if (!esPropietario.value) {
      const mensaje = 'Solo el propietario SaaS puede revocar licencias comerciales.';
      errorRevocar.value = mensaje;
      return { ok: false, revocada: false, error: mensaje };
    }

    revocando.value = true;
    errorRevocar.value = null;
    try {
      const resultado = await revocarLicenciaComercial(id);
      revocacion.value = resultado ?? null;
      await cargarLicencias(licencias.paginaActual.value);
      return { ok: true, ...(resultado ?? {}) };
    } catch (err) {
      errorRevocar.value = obtenerMensajeError(err);
      return { ok: false, revocada: false, error: errorRevocar.value };
    } finally {
      revocando.value = false;
    }
  }

  /**
   * Indica si el usuario con sesión actual puede revocar la licencia
   * mostrada (propietario SaaS y licencia aún activa).
   */
  function puedeRevocar(licencia) {
    const estado = normalizarEstado(licencia?.estado);
    const revocada = licencia?.revocada === true || estado === 'REVOKED';
    return esPropietario.value && !revocada;
  }

  return {
    licencias: licencias.registros,
    total: licencias.total,
    cargando: licencias.cargando,
    error: licencias.error,
    paginaActual: licencias.paginaActual,
    urlSiguiente: licencias.urlSiguiente,
    urlAnterior: licencias.urlAnterior,
    estadoFiltro,
    suscripcionFiltro,
    revocando,
    errorRevocar,
    revocacion,
    cargarLicencias,
    establecerEstado,
    establecerSuscripcion,
    limpiarFiltros,
    revocar,
    puedeRevocar,
  };
}
