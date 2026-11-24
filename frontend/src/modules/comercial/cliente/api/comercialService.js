import api, { obtenerMensajeError } from '../../../../api';

function unwrapResults(data) {
  return Array.isArray(data) ? data : (data?.results ?? []);
}

async function solicitar(peticion) {
  try {
    const { data } = await peticion;
    return data;
  } catch (error) {
    throw new Error(obtenerMensajeError(error), { cause: error });
  }
}

const base = '/comercial';

function listar(recurso, params) {
  const ruta = `${base}/${recurso}/`;
  return solicitar(params ? api.get(ruta, { params }) : api.get(ruta)).then(unwrapResults);
}

function datosCompra({ precioId, alumnos, contratoId }) {
  const datos = { precio: precioId, alumnos };
  if (contratoId) datos.contrato = contratoId;
  return datos;
}

export const comercialService = {
  getPlanes: () => listar('planes'),
  getPlan: (id) => solicitar(api.get(`${base}/planes/${id}/`)),
  getPrecios: (params = {}) => listar('precios', params),
  getPrecio: (id) => solicitar(api.get(`${base}/precios/${id}/`)),
  cotizar: (compra) => solicitar(api.post(`${base}/cotizacion/`, datosCompra(compra))),
  crearCheckout(compra) {
    const datos = datosCompra(compra);
    if (compra.cotizacion) {
      datos.importe_esperado = compra.cotizacion.total;
      datos.moneda_esperada = compra.cotizacion.moneda;
    }
    return solicitar(api.post(`${base}/checkout/`, datos, {
      headers: { 'Idempotency-Key': compra.idempotencyKey },
    }));
  },
  getOrden: (id) => solicitar(api.get(`${base}/ordenes/${encodeURIComponent(id)}/`)),
  getOrdenes: () => listar('ordenes'),
  getAcceso: () => solicitar(api.get(`${base}/acceso/`)),
  getSuscripciones: () => listar('suscripciones'),
  cancelarSuscripcion: (id) => solicitar(api.post(`${base}/suscripciones/${id}/cancelar/`, {})),
  getLicencias: () => listar('licencias'),
  getTransacciones: () => listar('transacciones'),
  getComprobantes: () => listar('comprobantes'),
  getFacturas: () => listar('facturas'),
  getContratos: () => listar('contratos'),

  async descargarComprobantePdf(id, folio = 'comprobante') {
    const blob = await solicitar(api.get(`${base}/comprobantes/${id}/pdf/`, { responseType: 'blob' }));
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `comprobante-${folio}.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
    return true;
  },

  solicitarFactura({ orden, rfc, razon_social, regimen, codigo_postal, uso_cfdi }) {
    return solicitar(api.post(`${base}/facturas/`, {
      orden,
      rfc: (rfc || '').toUpperCase().trim(),
      razon_social: (razon_social || '').trim(),
      regimen,
      codigo_postal: (codigo_postal || '').trim(),
      uso_cfdi,
    }));
  },
};
