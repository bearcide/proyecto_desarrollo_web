/**
 * Servicio del panel comercial del propietario SaaS (InscripcionMadeEasy).
 *
 * Este módulo es independiente del panel administrativo escolar y de la
 * experiencia comercial de cliente (`modules/comercial/cliente`): expone la
 * superficie de administración del propietario sobre las mismas colecciones
 * comerciales definidas por el contrato publicado `docs/CONTRATO_COMERCIAL_API.md`.
 *
 * Contrato: API comercial B2B v1 — Base `/api/v1/comercial/`.
 * Referencias: ordenes, suscripciones, licencias, transacciones, comprobantes,
 * facturas, contratos, precios, planes, ingresos y eventos.
 */
import api from '../../../../api';
import { comercialService } from '../../cliente/api/comercialService';
import { extraerRegistros, normalizarIndicadores, normalizarEstado, normalizarPlanComercial, normalizarLicenciaComercial, esVigente } from './normalizarComercial';

/** Rutas del contrato comercial publicadas (base /api/v1/comercial/). */
export const RUTAS_COMERCIALES = Object.freeze({
  ingresos: '/comercial/ingresos/',
  ordenesDemo: '/comercial/demo/pendientes/',
  confirmarDemo: '/comercial/demo/confirmar/',
  instituciones: '/comercial/instituciones/',
  institucionesDetalle: (id) => `/comercial/instituciones/${id}/`,
  contratos: '/comercial/contratos/',
  contratosDetalle: (id) => `/comercial/contratos/${id}/`,
  planes: '/comercial/planes/',
  precios: '/comercial/precios/',
  suscripciones: '/comercial/suscripciones/',
  licencias: '/comercial/licencias/',
  transacciones: '/comercial/transacciones/',
  comprobantes: (id) => `/comercial/comprobantes/${id}/pdf/`,
  facturas: '/comercial/facturas/',
  eventos: '/comercial/eventos/',
});

async function obtenerLista(url, params = {}) {
  const { data } = await api.get(url, { params });
  return data;
}

/** Indicadores comerciales agregados para el dashboard del propietario. */
export async function obtenerIndicadoresComerciales() {
  const resultados = await Promise.all([
    obtenerLista(RUTAS_COMERCIALES.instituciones),
    obtenerLista(RUTAS_COMERCIALES.suscripciones),
    obtenerLista(RUTAS_COMERCIALES.licencias),
    obtenerLista(RUTAS_COMERCIALES.transacciones),
    obtenerLista(RUTAS_COMERCIALES.contratos),
    obtenerLista(RUTAS_COMERCIALES.ingresos),
  ]);

  const instituciones = extraerRegistros(resultados[0]);
  const suscripciones = extraerRegistros(resultados[1]);
  const licencias = extraerRegistros(resultados[2]);
  const transacciones = extraerRegistros(resultados[3]);
  const contratos = extraerRegistros(resultados[4]);
  const ingresos = extraerRegistros(resultados[5]);

  const suscripcionesActivas = suscripciones.filter((s) => normalizarEstado(s.estado) === 'ACTIVE');
  const licenciasActivas = licencias.filter((l) => normalizarEstado(l.estado) === 'ACTIVE');
  const transaccionesPendientes = transacciones.filter((t) => normalizarEstado(t.estado) === 'PENDING');

  const hoy = new Date();
  const contratosVencidos = contratos.filter((c) => {
    const estado = normalizarEstado(c.estado);
    const fin = c.fin ? new Date(c.fin) : null;
    return estado === 'ACTIVE' && fin !== null && fin.getTime() < hoy.getTime();
  }).length;

  const renovacionesProximas = suscripcionesActivas.filter((s) => {
    const fin = s.fin_periodo ? new Date(s.fin_periodo) : null;
    if (!fin) return false;
    const limite = new Date(hoy.getTime());
    limite.setDate(limite.getDate() + 30);
    const desde = hoy.getTime();
    const hasta = limite.getTime();
    const tiempoFin = fin.getTime();
    return tiempoFin >= desde && tiempoFin <= hasta;
  }).length;

  const licenciasVigentes = licencias
    .map((l) => normalizarLicenciaComercial(l))
    .filter((l) => l.estado === 'ACTIVE' && (l.fechaVencimiento ? esVigente(l.fechaVencimiento, hoy) : true)).length;

  return {
    institucionesRegistradas: instituciones.length,
    institucionesContratantes: new Set(suscripcionesActivas.map((s) => s.tenant).filter(Boolean)).size,
    suscripcionesActivas: suscripcionesActivas.length,
    licenciasVigentes,
    ingresosDetalle: ingresos,
    pagosPendientes: transaccionesPendientes.length,
    contratosVencidos,
    renovacionesProximas,
  };
}

export async function obtenerOrdenesDemo() {
  return extraerRegistros(await obtenerLista(RUTAS_COMERCIALES.ordenesDemo));
}

export async function aprobarOrdenDemo(orden) {
  await api.post(RUTAS_COMERCIALES.confirmarDemo, {
    orden,
    resultado: 'paid',
    referencia: `demo_${orden}`,
  });
}

/** Listado de instituciones (escuelas) con contexto comercial. */
export async function obtenerEscuelasComerciales(params = {}) {
  return await obtenerLista(RUTAS_COMERCIALES.instituciones, params);
}

/** Detalle de una institución: contrato vigente, plan comercial y contexto de contratación. */
export async function obtenerEscuelaComercial(id) {
  const { data } = await api.get(RUTAS_COMERCIALES.institucionesDetalle(id));
  return data;
}

/** Catálogo de planes comerciales con precios, modalidades, límites y funcionalidades. */
export async function obtenerPlanesComerciales(params = {}) {
  const datos = await comercialService.getPlanes();
  const lista = extraerRegistros(datos).map((p) => normalizarPlanComercial(p));
  const precios = await comercialService.getPrecios(params);
  const preciosDePlan = extraerRegistros(precios);
  const resultado = lista.map((plan) => ({
    ...plan,
    precios: preciosDePlan.filter((p) => String(p.plan) === String(plan.id)),
  }));
  const estado = normalizarEstado(params?.estado);
  const conDisponibilidad = estado
    ? resultado.filter((p) => p.disponible === (estado === 'ACTIVO' || estado === 'ACTIVA'))
    : resultado;
  const planFiltro = String(params?.plan || '');
  const filtrado = planFiltro
    ? conDisponibilidad.filter((p) => String(p.codigo || '') === planFiltro || String(p.id || '') === planFiltro)
    : conDisponibilidad;
  return filtrado;
}

/** Catálogo de precios y modalidades por plan. */
export async function obtenerPreciosComerciales(params = {}) {
  const datos = await comercialService.getPrecios(params);
  return extraerRegistros(datos);
}

/** Contratos comerciales vigentes o cancelados por institución. */
export async function obtenerContratosComerciales(params = {}) {
  const { data } = await api.get(RUTAS_COMERCIALES.contratos, { params });
  return data;
}

/** Suscripciones comerciales activas/canceladas con contrato asociado. */
export async function obtenerSuscripcionesComerciales(params = {}) {
  const datos = await comercialService.getSuscripciones();
  const lista = extraerRegistros(datos);
  const estado = normalizarEstado(params?.estado);
  const resultado = estado ? lista.filter((s) => normalizarEstado(s.estado) === estado) : lista;
  const institucion = normalizarEstado(params?.institucion);
  if (institucion) {
    const termino = institucion.toLowerCase();
    return resultado.filter((s) => String(s.orden ?? s.orden_inicial ?? s.institucion ?? '').toLowerCase().includes(termino));
  }
  return resultado;
}

/** Licencias institucionales compradas. */
export async function obtenerLicenciasComerciales(params = {}) {
  const datos = await comercialService.getLicencias();
  const lista = extraerRegistros(datos);
  const estado = normalizarEstado(params?.estado);
  const resultado = estado ? lista.filter((l) => normalizarEstado(l.estado) === estado) : lista;
  const suscripcion = normalizarEstado(params?.suscripcion);
  if (suscripcion) {
    return resultado.filter((l) => String(l.orden || '') === suscripcion || String(l.suscripcion || '') === suscripcion);
  }
  return resultado;
}

/** Historial de transacciones (pagos) con filtros. */
export async function obtenerTransaccionesComerciales(params = {}) {
  const datos = await comercialService.getTransacciones();
  const lista = extraerRegistros(datos);
  const estado = normalizarEstado(params?.estado);
  const desde = params?.fecha_inicio ? new Date(params.fecha_inicio) : null;
  const hasta = params?.fecha_fin ? new Date(params.fecha_fin) : null;

  let resultado = lista;
  if (estado) {
    resultado = resultado.filter((t) => normalizarEstado(t.estado) === estado);
  }
  if (desde || hasta) {
    resultado = resultado.filter((t) => {
      const fecha = t.fecha ? new Date(t.fecha) : null;
      if (desde && (!fecha || fecha.getTime() < desde.getTime())) return false;
      if (hasta && (!fecha || fecha.getTime() > hasta.getTime())) return false;
      return true;
    });
  }
  const institucion = normalizarEstado(params?.institucion);
  if (institucion) {
    resultado = resultado.filter((t) => String(t.orden || '').includes(institucion) || String(t.institucion || '').includes(institucion));
  }
  return resultado;
}

/** Historial de pagos comerciales (alias de transacciones para el panel). */
export async function obtenerPagosComerciales(params = {}) {
  return await obtenerTransaccionesComerciales(params);
}

/** Solicitudes de facturación fiscal (CFDI). */
export async function obtenerSolicitudesFacturacionComerciales(params = {}) {
  const datos = await comercialService.getFacturas();
  const lista = extraerRegistros(datos);
  const estado = normalizarEstado(params?.estado);
  const resultado = estado ? lista.filter((f) => normalizarEstado(f.estado) === estado) : lista;
  const institucion = normalizarEstado(params?.institucion);
  if (institucion) {
    return resultado.filter((f) => String(f.institucion || '').toLowerCase().includes(institucion.toLowerCase()));
  }
  return resultado;
}

/** Comprobantes de pago emitidos por transacción. */
export async function obtenerComprobantesComerciales() {
  const datos = await comercialService.getComprobantes();
  return extraerRegistros(datos);
}

/** Envía una solicitud de factura fiscal a partir de una orden pagada. */
export async function solicitarFacturaComercial(datos) {
  const payload = {
    orden: datos?.orden,
    rfc: String(datos?.rfc || '').trim().toUpperCase(),
    razon_social: String(datos?.razon_social || '').trim(),
    regimen: datos?.regimen,
    codigo_postal: String(datos?.codigo_postal || '').trim(),
    uso_cfdi: datos?.uso_cfdi,
  };
  const response = await api.post('/comercial/facturas/', payload);
  return response.data;
}

/** Cancela una suscripción al final del periodo pagado. */
export async function cancelarSuscripcionComercial(id) {
  const response = await api.post(`/comercial/suscripciones/${id}/cancelar/`, {});
  return response.data;
}

/** Revoca una licencia de forma permanente. */
export async function revocarLicenciaComercial(id) {
  const response = await api.post(`/comercial/licencias/${id}/revocar/`, {});
  return response.data;
}

/**
 * Descarga el comprobante PDF autenticado de un pago.
 * No genera comprobantes: responde el recurso que el backend ya haya emitido.
 */
export async function descargarComprobanteComercial(id) {
  const { data, headers } = await api.get(`/comercial/comprobantes/${id}/pdf/`, { responseType: 'blob' });
  const disposition = String(headers?.['content-disposition'] || '');
  const nombre = /filename[^;]*=([^;]*)/.exec(disposition)?.[1];
  const url = URL.createObjectURL(data);
  return { url, nombre: nombre ? decodeURIComponent(nombre) : `comprobante-${id}.pdf` };
}
