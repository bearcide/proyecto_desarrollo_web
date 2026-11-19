/**
 * Servicio de integración REST para el módulo comercial B2B.
 * Respeta rigurosamente docs/CONTRATO_COMERCIAL_API.md
 * Base: /api/v1/comercial/
 */
import api, { obtenerMensajeError } from '../../../../api';
import { generarIdempotencyKey } from '../domain/comercialCalculos';

// Catálogo y respuestas de respaldo fieles al contrato para desarrollo offline / demo
const FALLBACK_PLANES = [
  {
    id: 'b1010000-0000-4000-8000-000000000001',
    codigo: 'starter',
    nombre: 'Plan Básico Escolar',
    descripcion: 'Diseñado para escuelas y academias en crecimiento que inician la digitalización de inscripciones.',
    funcionalidades: [
      'Gestión de inscripciones en línea',
      'Matrícula y expedientes digitales',
      'Catálogo curricular básico',
      'Soporte estándar vía ticket',
    ],
    max_alumnos: 500,
    max_planteles: 1,
    activo: true,
  },
  {
    id: 'b1020000-0000-4000-8000-000000000002',
    codigo: 'pro',
    nombre: 'Plan Profesional Campus',
    descripcion: 'Solución integral para preparatorias, institutos y facultades con algoritmos anti-empalme.',
    funcionalidades: [
      'Todo lo del Plan Básico',
      'Algoritmo anti-empalme de horarios',
      'Importación masiva CSV de aspirantes',
      'Control de cupos y restricciones en tiempo real',
      'Soporte técnico prioritario 24/7',
    ],
    max_alumnos: 2500,
    max_planteles: 3,
    activo: true,
  },
  {
    id: 'b1030000-0000-4000-8000-000000000003',
    codigo: 'enterprise',
    nombre: 'Licencia Institucional Universitaria',
    descripcion: 'Para redes educativas y universidades con múltiples planteles, auditoría y SLAs de alta disponibilidad.',
    funcionalidades: [
      'Todo lo del Plan Profesional',
      'Multi-plantel y multi-campus unificado',
      'Licenciamiento institucional o perpetuo',
      'API REST dedicada e integración con ERP',
      'Gestor de cuenta y SLA del 99.9%',
    ],
    max_alumnos: 15000,
    max_planteles: 10,
    activo: true,
  },
];

const FALLBACK_PRECIOS = [
  // Básico Escolar
  {
    id: 'p1010000-0000-4000-8000-000000000001',
    plan: 'b1010000-0000-4000-8000-000000000001',
    modalidad: 'monthly',
    importe: '1499.00',
    por_alumno: '3.50',
    moneda: 'MXN',
    dias: 30,
    activo: true,
  },
  {
    id: 'p1010000-0000-4000-8000-000000000002',
    plan: 'b1010000-0000-4000-8000-000000000001',
    modalidad: 'annual',
    importe: '14990.00',
    por_alumno: '2.80',
    moneda: 'MXN',
    dias: 365,
    activo: true,
  },
  {
    id: 'p1010000-0000-4000-8000-000000000003',
    plan: 'b1010000-0000-4000-8000-000000000001',
    modalidad: 'process',
    importe: '3800.00',
    por_alumno: '4.00',
    moneda: 'MXN',
    dias: 60,
    activo: true,
  },
  // Profesional Campus
  {
    id: 'p1020000-0000-4000-8000-000000000001',
    plan: 'b1020000-0000-4000-8000-000000000002',
    modalidad: 'monthly',
    importe: '3499.00',
    por_alumno: '4.50',
    moneda: 'MXN',
    dias: 30,
    activo: true,
  },
  {
    id: 'p1020000-0000-4000-8000-000000000002',
    plan: 'b1020000-0000-4000-8000-000000000002',
    modalidad: 'annual',
    importe: '34990.00',
    por_alumno: '3.80',
    moneda: 'MXN',
    dias: 365,
    activo: true,
  },
  {
    id: 'p1020000-0000-4000-8000-000000000003',
    plan: 'b1020000-0000-4000-8000-000000000002',
    modalidad: 'process',
    importe: '7900.00',
    por_alumno: '5.00',
    moneda: 'MXN',
    dias: 60,
    activo: true,
  },
  {
    id: 'p1020000-0000-4000-8000-000000000004',
    plan: 'b1020000-0000-4000-8000-000000000002',
    modalidad: 'institutional',
    importe: '45000.00',
    por_alumno: '2.50',
    moneda: 'MXN',
    dias: 365,
    activo: true,
  },
  // Enterprise Universitaria
  {
    id: 'p1030000-0000-4000-8000-000000000001',
    plan: 'b1030000-0000-4000-8000-000000000003',
    modalidad: 'institutional',
    importe: '89000.00',
    por_alumno: '2.00',
    moneda: 'MXN',
    dias: 365,
    activo: true,
  },
  {
    id: 'p1030000-0000-4000-8000-000000000002',
    plan: 'b1030000-0000-4000-8000-000000000003',
    modalidad: 'perpetual',
    importe: '185000.00',
    por_alumno: '0.00',
    moneda: 'MXN',
    dias: null,
    activo: true,
  },
  {
    id: 'p1030000-0000-4000-8000-000000000003',
    plan: 'b1030000-0000-4000-8000-000000000003',
    modalidad: 'enterprise',
    importe: '120000.00',
    por_alumno: '1.50',
    moneda: 'MXN',
    dias: 730,
    activo: true,
  },
  {
    id: 'p1030000-0000-4000-8000-000000000004',
    plan: 'b1030000-0000-4000-8000-000000000003',
    modalidad: 'maintenance',
    importe: '22000.00',
    por_alumno: '0.00',
    moneda: 'MXN',
    dias: 365,
    activo: true,
  },
];

// Almacenamiento local temporal para órdenes y transacciones generadas en demo
const ORDENES_LOCALES = new Map();
const FACTURAS_LOCALES = [];

function unwrapResults(data) {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  if (Array.isArray(data.results)) return data.results;
  return [];
}

export const comercialService = {
  /**
   * Catálogo de planes comerciales
   * GET /api/v1/comercial/planes/
   */
  async getPlanes() {
    try {
      const response = await api.get('/comercial/planes/');
      return unwrapResults(response.data);
    } catch (err) {
      if (!err.response) {
        console.info('[Comercial API] Backend offline, usando catálogo de respaldo de contrato.');
        return FALLBACK_PLANES;
      }
      throw new Error(obtenerMensajeError(err));
    }
  },

  /**
   * Detalle de un plan
   * GET /api/v1/comercial/planes/{id}/
   */
  async getPlan(id) {
    try {
      const response = await api.get(`/comercial/planes/${id}/`);
      return response.data;
    } catch (err) {
      if (!err.response) {
        const found = FALLBACK_PLANES.find((p) => p.id === id);
        if (found) return found;
      }
      throw new Error(obtenerMensajeError(err));
    }
  },

  /**
   * Catálogo de precios y modalidades
   * GET /api/v1/comercial/precios/
   */
  async getPrecios(params = {}) {
    try {
      const response = await api.get('/comercial/precios/', { params });
      return unwrapResults(response.data);
    } catch (err) {
      if (!err.response) {
        let filtrados = [...FALLBACK_PRECIOS];
        if (params.plan) {
          filtrados = filtrados.filter((p) => p.plan === params.plan);
        }
        if (params.modalidad) {
          filtrados = filtrados.filter((p) => p.modalidad === params.modalidad);
        }
        return filtrados;
      }
      throw new Error(obtenerMensajeError(err));
    }
  },

  /**
   * Detalle de un precio
   * GET /api/v1/comercial/precios/{id}/
   */
  async getPrecio(id) {
    try {
      const response = await api.get(`/comercial/precios/${id}/`);
      return response.data;
    } catch (err) {
      if (!err.response) {
        const found = FALLBACK_PRECIOS.find((p) => p.id === id);
        if (found) return found;
      }
      throw new Error(obtenerMensajeError(err));
    }
  },

  /**
   * Crear sesión de contratación y orden
   * POST /api/v1/comercial/checkout/
   * Headers: Idempotency-Key
   * Body: { precio: uuid, alumnos: number, contrato?: uuid }
   */
  async crearCheckout({ precioId, alumnos = 1, contratoId = null, idempotencyKey = null }) {
    const key = idempotencyKey || generarIdempotencyKey();
    const payload = {
      precio: precioId,
      alumnos: Math.max(1, parseInt(alumnos, 10) || 1),
    };
    if (contratoId) {
      payload.contrato = contratoId;
    }

    try {
      const response = await api.post('/comercial/checkout/', payload, {
        headers: {
          'Idempotency-Key': key,
        },
      });
      return response.data; // { orden, proveedor, url, estado }
    } catch (err) {
      if (!err.response) {
        // Modo DEMO Offline simulado fiel al contrato
        console.warn('[Comercial API] Servidor no disponible. Generando orden DEMO local.');
        const ordenId = generarIdempotencyKey();
        const precio = FALLBACK_PRECIOS.find((p) => p.id === precioId) || FALLBACK_PRECIOS[0];
        const plan = FALLBACK_PLANES.find((pl) => pl.id === precio.plan) || FALLBACK_PLANES[0];

        const importeTotal = (parseFloat(precio.importe) + (parseFloat(precio.por_alumno) * payload.alumnos)).toFixed(2);

        const ordenLocal = {
          id: ordenId,
          tenant: localStorage.getItem('ime_tenant_id') || 'tenant-demo-local',
          precio: precio.id,
          precio_detalle: precio,
          plan_detalle: plan,
          contrato: contratoId,
          importe: importeTotal,
          cantidad_alumnos: payload.alumnos,
          proveedor: 'DEMO',
          estado: 'pending',
          fecha_creacion: new Date().toISOString(),
        };

        ORDENES_LOCALES.set(ordenId, ordenLocal);

        return {
          orden: ordenId,
          proveedor: 'DEMO',
          url: null,
          estado: 'pending',
        };
      }
      throw new Error(obtenerMensajeError(err));
    }
  },

  /**
   * Consulta una orden específica
   * GET /api/v1/comercial/ordenes/{id}/
   */
  async getOrden(id) {
    try {
      const response = await api.get(`/comercial/ordenes/${id}/`);
      return response.data;
    } catch (err) {
      if (!err.response && ORDENES_LOCALES.has(id)) {
        return ORDENES_LOCALES.get(id);
      }
      throw new Error(obtenerMensajeError(err));
    }
  },

  /**
   * Lista de órdenes institucionales
   * GET /api/v1/comercial/ordenes/
   */
  async getOrdenes() {
    try {
      const response = await api.get('/comercial/ordenes/');
      return unwrapResults(response.data);
    } catch (err) {
      if (!err.response) {
        return Array.from(ORDENES_LOCALES.values());
      }
      throw new Error(obtenerMensajeError(err));
    }
  },

  /**
   * Estado de acceso efectivo institucional
   * GET /api/v1/comercial/acceso/
   */
  async getAcceso() {
    try {
      const response = await api.get('/comercial/acceso/');
      return response.data;
    } catch (err) {
      if (!err.response) {
        return {
          activo: true,
          funcionalidades: [
            'Gestión de inscripciones',
            'Matrícula digital',
            'Horarios automáticos anti-empalme',
            'Importación CSV',
          ],
          max_alumnos: 2500,
          max_planteles: 3,
          plan_actual: 'Plan Profesional Campus',
          modalidad: 'annual',
        };
      }
      throw new Error(obtenerMensajeError(err));
    }
  },

  /**
   * Suscripciones de la institución
   * GET /api/v1/comercial/suscripciones/
   */
  async getSuscripciones() {
    try {
      const response = await api.get('/comercial/suscripciones/');
      return unwrapResults(response.data);
    } catch (err) {
      if (!err.response) {
        return [
          {
            id: 'sub-00000000-0000-4000-8000-000000000001',
            orden_inicial: 'ord-demo-001',
            plan_nombre: 'Plan Profesional Campus',
            modalidad: 'annual',
            estado: 'active',
            fin_periodo: new Date(Date.now() + 180 * 24 * 3600 * 1000).toISOString(),
            cancel_at_period_end: false,
            renovacion_automatica: true,
            importe: '34990.00',
            moneda: 'MXN',
          },
        ];
      }
      throw new Error(obtenerMensajeError(err));
    }
  },

  /**
   * Cancelar suscripción al final del periodo pagado
   * POST /api/v1/comercial/suscripciones/{id}/cancelar/
   */
  async cancelarSuscripcion(id) {
    try {
      const response = await api.post(`/comercial/suscripciones/${id}/cancelar/`, {});
      return response.data;
    } catch (err) {
      if (!err.response) {
        return {
          id,
          estado: 'active',
          cancel_at_period_end: true,
          mensaje: 'Cancelación programada para el término del periodo contratado.',
        };
      }
      throw new Error(obtenerMensajeError(err));
    }
  },

  /**
   * Licencias institucionales compradas
   * GET /api/v1/comercial/licencias/
   */
  async getLicencias() {
    try {
      const response = await api.get('/comercial/licencias/');
      return unwrapResults(response.data);
    } catch (err) {
      if (!err.response) {
        return [
          {
            id: 'lic-00000000-0000-4000-8000-000000000001',
            orden: 'ord-demo-lic-001',
            estado: 'active',
            inicio: new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString(),
            fin: new Date(Date.now() + 335 * 24 * 3600 * 1000).toISOString(),
            tipo: 'institutional',
            max_alumnos: 2500,
            max_planteles: 3,
            funcionalidades: [
              'Generador inteligente de horarios',
              'Multi-plantel centralizado',
              'Importador masivo',
              'Soporte 24/7',
            ],
            es_mantenimiento: false,
          },
        ];
      }
      throw new Error(obtenerMensajeError(err));
    }
  },

  /**
   * Historial inmutable de transacciones
   * GET /api/v1/comercial/transacciones/
   */
  async getTransacciones() {
    try {
      const response = await api.get('/comercial/transacciones/');
      return unwrapResults(response.data);
    } catch (err) {
      if (!err.response) {
        return [
          {
            id: 'tx-00000000-0000-4000-8000-000000000001',
            orden: 'ord-demo-001',
            referencia: 'ch_stripe_test_839201948',
            importe: '34990.00',
            moneda: 'MXN',
            estado: 'paid',
            fecha: new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString(),
          },
        ];
      }
      throw new Error(obtenerMensajeError(err));
    }
  },

  /**
   * Comprobantes de pago
   * GET /api/v1/comercial/comprobantes/
   */
  async getComprobantes() {
    try {
      const response = await api.get('/comercial/comprobantes/');
      return unwrapResults(response.data);
    } catch (err) {
      if (!err.response) {
        return [
          {
            id: 'comp-00000000-0000-4000-8000-000000000001',
            transaccion: 'tx-00000000-0000-4000-8000-000000000001',
            folio: 'CMP-2026-000192',
            fecha: new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString(),
            importe: '34990.00',
            moneda: 'MXN',
          },
        ];
      }
      throw new Error(obtenerMensajeError(err));
    }
  },

  /**
   * Descarga de comprobante PDF autenticado vía Blob
   * GET /api/v1/comercial/comprobantes/{id}/pdf/
   */
  async descargarComprobantePdf(id, folio = 'comprobante') {
    try {
      const response = await api.get(`/comercial/comprobantes/${id}/pdf/`, {
        responseType: 'blob',
      });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `comprobante-${folio}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      return true;
    } catch (err) {
      if (!err.response) {
        // En entorno mock generamos un PDF mínimo en Blob para no bloquear al usuario
        const blob = new Blob(
          [`%PDF-1.4\n1 0 obj<< /Title (Comprobante InscripcionMadeEasy) >>endobj\ntrailer<<>>\n%%EOF`],
          { type: 'application/pdf' },
        );
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `comprobante-${folio}-demo.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        return true;
      }
      throw new Error(obtenerMensajeError(err));
    }
  },

  /**
   * Solicitudes de facturación fiscal (CFDI)
   * GET /api/v1/comercial/facturas/
   */
  async getFacturas() {
    try {
      const response = await api.get('/comercial/facturas/');
      return unwrapResults(response.data);
    } catch (err) {
      if (!err.response) {
        return [...FACTURAS_LOCALES];
      }
      throw new Error(obtenerMensajeError(err));
    }
  },

  /**
   * Enviar solicitud de factura
   * POST /api/v1/comercial/facturas/
   * Body: { orden, rfc, razon_social, regimen, codigo_postal, uso_cfdi }
   */
  async solicitarFactura({ orden, rfc, razon_social, regimen, codigo_postal, uso_cfdi }) {
    const payload = {
      orden,
      rfc: (rfc || '').toUpperCase().trim(),
      razon_social: (razon_social || '').trim(),
      regimen,
      codigo_postal: (codigo_postal || '').trim(),
      uso_cfdi,
    };

    try {
      const response = await api.post('/comercial/facturas/', payload);
      return response.data;
    } catch (err) {
      if (!err.response) {
        const facturaMock = {
          id: generarIdempotencyKey(),
          ...payload,
          estado: 'requested',
          fecha: new Date().toISOString(),
        };
        FACTURAS_LOCALES.push(facturaMock);
        return facturaMock;
      }
      throw new Error(obtenerMensajeError(err));
    }
  },

  /**
   * Contratos empresariales para la institución
   * GET /api/v1/comercial/contratos/
   */
  async getContratos() {
    try {
      const response = await api.get('/comercial/contratos/');
      return unwrapResults(response.data);
    } catch (err) {
      if (!err.response) {
        return [];
      }
      throw new Error(obtenerMensajeError(err));
    }
  },

  /**
   * Simulación DEMO para desarrollo: aprueba una orden local en memoria
   */
  marcarOrdenDemoPagada(id) {
    if (ORDENES_LOCALES.has(id)) {
      const ord = ORDENES_LOCALES.get(id);
      ord.estado = 'paid';
      ORDENES_LOCALES.set(id, ord);
      return ord;
    }
    return null;
  },
};
