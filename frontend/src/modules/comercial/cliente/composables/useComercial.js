import { ref } from 'vue';
import { comercialService } from '../api/comercialService';
import { useNotificationStore } from '../../../../stores/notification';

export function useComercial() {
  const notifStore = useNotificationStore();

  const cargando = ref(false);
  const error = ref(null);

  const planes = ref([]);
  const precios = ref([]);
  const acceso = ref(null);
  const suscripciones = ref([]);
  const licencias = ref([]);
  const transacciones = ref([]);
  const comprobantes = ref([]);
  const facturas = ref([]);
  const contratos = ref([]);

  async function cargarCatalogo() {
    cargando.value = true;
    error.value = null;
    try {
      const [listaPlanes, listaPrecios] = await Promise.all([
        comercialService.getPlanes(),
        comercialService.getPrecios(),
      ]);
      planes.value = listaPlanes;
      precios.value = listaPrecios;
      return { planes: listaPlanes, precios: listaPrecios };
    } catch (err) {
      error.value = err.message || 'Error al cargar catálogo comercial.';
      notifStore.error(error.value);
      throw err;
    } finally {
      cargando.value = false;
    }
  }

  async function cargarEstadoInstitucion() {
    cargando.value = true;
    error.value = null;
    try {
      const [
        datosAcceso,
        listaSuscripciones,
        listaLicencias,
        listaTransacciones,
        listaComprobantes,
        listaFacturas,
        listaContratos,
      ] = await Promise.allSettled([
        comercialService.getAcceso(),
        comercialService.getSuscripciones(),
        comercialService.getLicencias(),
        comercialService.getTransacciones(),
        comercialService.getComprobantes(),
        comercialService.getFacturas(),
        comercialService.getContratos(),
      ]);

      if (datosAcceso.status === 'fulfilled') acceso.value = datosAcceso.value;
      if (listaSuscripciones.status === 'fulfilled') suscripciones.value = listaSuscripciones.value;
      if (listaLicencias.status === 'fulfilled') licencias.value = listaLicencias.value;
      if (listaTransacciones.status === 'fulfilled') transacciones.value = listaTransacciones.value;
      if (listaComprobantes.status === 'fulfilled') comprobantes.value = listaComprobantes.value;
      if (listaFacturas.status === 'fulfilled') facturas.value = listaFacturas.value;
      if (listaContratos.status === 'fulfilled') contratos.value = listaContratos.value;
    } catch (err) {
      error.value = err.message || 'Error al consultar estado comercial de la institución.';
      notifStore.error(error.value);
    } finally {
      cargando.value = false;
    }
  }

  function obtenerPreciosDePlan(planId) {
    if (!planId) return [];
    return precios.value.filter((p) => p.plan === planId && p.activo);
  }

  function obtenerPrecio(planId, modalidad) {
    return precios.value.find((p) => p.plan === planId && p.modalidad === modalidad && p.activo);
  }

  async function iniciarCheckout({ precioId, alumnos = 1, contratoId = null }) {
    cargando.value = true;
    error.value = null;
    try {
      const sesion = await comercialService.crearCheckout({
        precioId,
        alumnos,
        contratoId,
      });
      return sesion;
    } catch (err) {
      error.value = err.message || 'Error al iniciar checkout.';
      notifStore.error(error.value);
      throw err;
    } finally {
      cargando.value = false;
    }
  }

  async function consultarOrden(id) {
    cargando.value = true;
    error.value = null;
    try {
      const orden = await comercialService.getOrden(id);
      return orden;
    } catch (err) {
      error.value = err.message || 'Error al consultar orden.';
      throw err;
    } finally {
      cargando.value = false;
    }
  }

  async function cancelarRenovacion(suscripcionId) {
    cargando.value = true;
    try {
      const res = await comercialService.cancelarSuscripcion(suscripcionId);
      notifStore.info('Cancelación de renovación programada exitosamente.');
      await cargarEstadoInstitucion();
      return res;
    } catch (err) {
      notifStore.error(err.message || 'No se pudo programar la cancelación.');
      throw err;
    } finally {
      cargando.value = false;
    }
  }

  async function descargarComprobante(id, folio) {
    try {
      notifStore.info('Preparando descarga del comprobante PDF…');
      await comercialService.descargarComprobantePdf(id, folio);
      notifStore.success('Comprobante descargado correctamente.');
    } catch (err) {
      notifStore.error(err.message || 'Error al descargar PDF del comprobante.');
    }
  }

  async function enviarSolicitudFactura(datos) {
    cargando.value = true;
    try {
      const resp = await comercialService.solicitarFactura(datos);
      notifStore.success('Solicitud de factura enviada exitosamente.');
      const list = await comercialService.getFacturas();
      facturas.value = list;
      return resp;
    } catch (err) {
      notifStore.error(err.message || 'Error al registrar solicitud fiscal.');
      throw err;
    } finally {
      cargando.value = false;
    }
  }

  return {
    cargando,
    error,
    planes,
    precios,
    acceso,
    suscripciones,
    licencias,
    transacciones,
    comprobantes,
    facturas,
    contratos,
    cargarCatalogo,
    cargarEstadoInstitucion,
    obtenerPreciosDePlan,
    obtenerPrecio,
    iniciarCheckout,
    consultarOrden,
    cancelarRenovacion,
    descargarComprobante,
    enviarSolicitudFactura,
  };
}
