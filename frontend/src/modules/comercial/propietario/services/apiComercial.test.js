import { beforeEach, describe, expect, it, vi } from 'vitest';
import api from '../../../../api';
import { comercialService } from '../../cliente/api/comercialService';
import {
  RUTAS_COMERCIALES,
  cancelarSuscripcionComercial,
  revocarLicenciaComercial,
  obtenerContratosComerciales,
  obtenerEscuelaComercial,
  obtenerEscuelasComerciales,
  obtenerIndicadoresComerciales,
  obtenerLicenciasComerciales,
  obtenerPagosComerciales,
  obtenerPlanesComerciales,
  obtenerSolicitudesFacturacionComerciales,
  solicitarFacturaComercial,
} from './apiComercial';

vi.mock('../../../../api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
  obtenerMensajeError: (err) => err?.message || 'Error mock',
  decodificarToken: vi.fn(() => null),
}));

vi.mock('../../cliente/api/comercialService', () => ({
  comercialService: {
    getPlanes: vi.fn(),
    getPrecios: vi.fn(),
    getSuscripciones: vi.fn(),
    getLicencias: vi.fn(),
    getTransacciones: vi.fn(),
    getFacturas: vi.fn(),
    getComprobantes: vi.fn(),
  },
}));

describe('Servicio comercial del propietario — acciones soportadas por el contrato', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('cancelar suscripción', () => {
    it('envía la cancelación programada al endpoint del contrato', async () => {
      api.post.mockResolvedValueOnce({
        data: { id: 'sub-1', estado: 'active', cancel_at_period_end: true },
      });

      const resultado = await cancelarSuscripcionComercial('sub-1');

      expect(api.post).toHaveBeenCalledTimes(1);
      expect(api.post).toHaveBeenCalledWith('/comercial/suscripciones/sub-1/cancelar/', {});
      expect(resultado.estado).toBe('active');
      expect(resultado.cancel_at_period_end).toBe(true);
    });

    it('propaga el error del backend (propietario no autorizado, estado inválido, proveedor)', async () => {
      api.post.mockRejectedValueOnce(new Error('Solo el propietario SaaS puede cancelar suscripciones comerciales.'));

      await expect(cancelarSuscripcionComercial('sub-1')).rejects.toThrow(
        'Solo el propietario SaaS puede cancelar suscripciones comerciales.',
      );
    });
  });

  describe('revocar licencia', () => {
    it('envía la revocación permanente al endpoint del contrato', async () => {
      api.post.mockResolvedValueOnce({
        data: { id: 'lic-1', estado: 'revoked' },
      });

      const resultado = await revocarLicenciaComercial('lic-1');

      expect(api.post).toHaveBeenCalledTimes(1);
      expect(api.post).toHaveBeenCalledWith('/comercial/licencias/lic-1/revocar/', {});
      expect(resultado.estado).toBe('revoked');
    });

    it('propaga el error de autorización o de estado al backend', async () => {
      api.post.mockRejectedValueOnce(new Error('Se requiere rol de propietario SaaS.'));

      await expect(revocarLicenciaComercial('lic-1')).rejects.toThrow('Se requiere rol de propietario SaaS.');
    });
  });
});

describe('Servicio comercial del propietario — consultas del panel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('consulta indicadores agregados de instituciones, suscripciones, licencias, pagos, contratos e ingresos', async () => {
    api.get.mockImplementation(async (url) => {
      if (url === RUTAS_COMERCIALES.instituciones) {
        return { data: { count: 2, next: null, previous: null, results: [{ id: 't1' }, { id: 't2' }] } };
      }
      if (url === RUTAS_COMERCIALES.suscripciones) {
        return { data: { count: 1, next: null, previous: null, results: [{ id: 'sub-1', estado: 'active', orden: 'ord-1', tenant: 't1' }] } };
      }
      if (url === RUTAS_COMERCIALES.licencias) {
        return { data: { count: 1, next: null, previous: null, results: [{ id: 'lic-1', estado: 'active', fin: '2099-01-01T00:00:00Z' }] } };
      }
      if (url === RUTAS_COMERCIALES.transacciones) {
        return { data: { count: 1, next: null, previous: null, results: [{ id: 'tx-1', estado: 'paid', importe: '100.00' }] } };
      }
      if (url === RUTAS_COMERCIALES.contratos) {
        return { data: { count: 0, next: null, previous: null, results: [] } };
      }
      if (url === RUTAS_COMERCIALES.ingresos) {
        return { data: [{ proveedor: 'DEMO', moneda: 'MXN', total: '100.00' }] };
      }
      return { data: { count: 0, next: null, previous: null, results: [] } };
    });

    const indicadores = await obtenerIndicadoresComerciales();

    expect(indicadores.institucionesRegistradas).toBe(2);
    expect(indicadores.suscripcionesActivas).toBe(1);
    expect(indicadores.institucionesContratantes).toBe(1);
    expect(indicadores.licenciasVigentes).toBe(1);
    expect(indicadores.pagosPendientes).toBe(0);
    expect(indicadores.contratosVencidos).toBe(0);
    expect(api.get).toHaveBeenCalledWith('/comercial/ingresos/', { params: {} });
    expect(indicadores.ingresosDetalle).toEqual([{ proveedor: 'DEMO', moneda: 'MXN', total: '100.00' }]);
  });

  it('consulta el listado de instituciones (clientes comerciales)', async () => {
    api.get.mockResolvedValueOnce({ data: { count: 1, next: null, previous: null, results: [{ id: 't1', nombre_comercial: 'Escuela Aurora' }] } });

    const escuelas = await obtenerEscuelasComerciales();

    expect(api.get).toHaveBeenCalledWith(RUTAS_COMERCIALES.instituciones, { params: {} });
    expect(escuelas.results).toHaveLength(1);
  });

  it('consulta el detalle de una institución (cliente con contrato, plan y contexto)', async () => {
    api.get.mockResolvedValueOnce({
      data: { id: 't1', nombre_comercial: 'Escuela Aurora', plan_suscripcion: 'PRO', estado: 'ACTIVO', activo: true },
    });

    const escuela = await obtenerEscuelaComercial('t1');

    expect(api.get).toHaveBeenCalledWith(RUTAS_COMERCIALES.institucionesDetalle('t1'));
    expect(escuela.nombre_comercial).toBe('Escuela Aurora');
  });

  it('consulta los contratos comerciales del propietario', async () => {
    const contratos = [{ id: 'c1', estado: 'active', tenant: 't1' }];
    api.get.mockResolvedValueOnce({ data: { count: 1, next: null, previous: null, results: contratos } });

    const resultado = await obtenerContratosComerciales();

    expect(api.get).toHaveBeenCalledWith(RUTAS_COMERCIALES.contratos, { params: {} });
    expect(resultado.results).toHaveLength(1);
  });

  it('consulta los pagos (transacciones) con el alias del panel propietario', async () => {
    comercialService.getTransacciones.mockResolvedValueOnce({
      count: 1,
      results: [{ id: 'tx-1', estado: 'paid', importe: '34990.00' }],
    });

    const pagos = await obtenerPagosComerciales();

    expect(comercialService.getTransacciones).toHaveBeenCalled();
    expect(pagos[0].estado).toBe('paid');
  });

  it('consulta las solicitudes de facturación (CFDI) del propietario', async () => {
    comercialService.getFacturas.mockResolvedValueOnce({
      count: 1,
      results: [{ id: 'f1', estado: 'requested', orden: 'ord-1' }],
    });

    const solicitudes = await obtenerSolicitudesFacturacionComerciales();

    expect(comercialService.getFacturas).toHaveBeenCalled();
    expect(solicitudes[0].estado).toBe('requested');
  });

  it('consulta las licencias comerciales y aplica el filtro de estado local', async () => {
    comercialService.getLicencias.mockResolvedValueOnce({
      count: 2,
      results: [
        { id: 'lic-1', estado: 'active', orden: 'ord-1', tenant: 't1' },
        { id: 'lic-2', estado: 'revoked', orden: 'ord-2' },
      ],
    });

    const licencias = await obtenerLicenciasComerciales({ estado: 'ACTIVE' });

    expect(comercialService.getLicencias).toHaveBeenCalled();
    expect(licencias).toHaveLength(1);
    expect(licencias[0].estado).toBe('active');
  });

  it('consulta los planes comerciales con precios del catálogo', async () => {
    comercialService.getPlanes.mockResolvedValueOnce([
      { id: 'b1', codigo: 'pro', nombre: 'Plan Profesional Campus', max_alumnos: 2500, max_planteles: 3, funcionalidades: ['Anti-empalme'], activo: true },
    ]);
    comercialService.getPrecios.mockResolvedValueOnce([
      { id: 'p1', plan: 'b1', modalidad: 'annual', importe: '34990.00', activo: true },
    ]);

    const planes = await obtenerPlanesComerciales({ estado: 'ACTIVO', plan: 'b1' });

    expect(comercialService.getPlanes).toHaveBeenCalled();
    expect(comercialService.getPrecios).toHaveBeenCalledWith({ estado: 'ACTIVO', plan: 'b1' });
    expect(planes).toHaveLength(1);
    expect(planes[0].disponible).toBe(true);
  });

  it('envía la solicitud de factura fiscal con el orden pagado validando campos obligatorios', async () => {
    api.post.mockResolvedValueOnce({ data: { id: 'f1', estado: 'requested' } });

    const respuesta = await solicitarFacturaComercial({
      orden: 'ord-1',
      rfc: 'ime190101abc',
      razon_social: 'Escuela Demo',
      regimen: '601',
      codigo_postal: '06700',
      uso_cfdi: 'G03',
    });

    expect(api.post).toHaveBeenCalledWith('/comercial/facturas/', {
      orden: 'ord-1',
      rfc: 'IME190101ABC',
      razon_social: 'Escuela Demo',
      regimen: '601',
      codigo_postal: '06700',
      uso_cfdi: 'G03',
    });
    expect(respuesta.estado).toBe('requested');
  });
});
