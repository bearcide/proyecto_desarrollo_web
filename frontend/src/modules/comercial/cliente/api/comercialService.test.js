import { describe, it, expect, vi, beforeEach } from 'vitest';
import { comercialService } from './comercialService';
import api from '../../../../api';

vi.mock('../../../../api', () => {
  return {
    default: {
      get: vi.fn(),
      post: vi.fn(),
    },
    obtenerMensajeError: (err) => err?.message || 'Error mock',
  };
});

describe('comercialService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getPlanes', () => {
    it('retorna la lista de planes cuando la API responde exitosamente', async () => {
      const mockData = [
        { id: '1', codigo: 'starter', nombre: 'Plan Básico' },
        { id: '2', codigo: 'pro', nombre: 'Plan Pro' },
      ];
      api.get.mockResolvedValueOnce({ data: mockData });

      const res = await comercialService.getPlanes();
      expect(res).toEqual(mockData);
      expect(api.get).toHaveBeenCalledWith('/comercial/planes/');
    });

    it('extrae results si la respuesta de DRF viene paginada', async () => {
      const mockResults = [{ id: '1', nombre: 'Plan 1' }];
      api.get.mockResolvedValueOnce({ data: { count: 1, results: mockResults } });

      const res = await comercialService.getPlanes();
      expect(res).toEqual(mockResults);
    });

    it('informa de la desconexión sin inventar un catálogo', async () => {
      api.get.mockRejectedValueOnce(new Error('Network Error'));
      await expect(comercialService.getPlanes()).rejects.toThrow('Network Error');
    });
  });

  describe('getPrecios', () => {
    it('envía los parámetros de filtro correctamente a la API', async () => {
      api.get.mockResolvedValueOnce({ data: [] });

      await comercialService.getPrecios({ plan: 'plan-123', modalidad: 'annual' });
      expect(api.get).toHaveBeenCalledWith('/comercial/precios/', {
        params: { plan: 'plan-123', modalidad: 'annual' },
      });
    });
  });

  describe('crearCheckout', () => {
    it('envía payload e Idempotency-Key en la cabecera', async () => {
      const mockCheckoutRes = {
        orden: 'ord-123',
        proveedor: 'stripe',
        url: 'https://checkout.stripe.com/pay/cs_test_123',
        estado: 'pending',
      };
      api.post.mockResolvedValueOnce({ data: mockCheckoutRes });

      const res = await comercialService.crearCheckout({
        precioId: 'precio-456',
        alumnos: 300,
        idempotencyKey: 'key-test-uuid',
      });

      expect(res).toEqual(mockCheckoutRes);
      expect(api.post).toHaveBeenCalledWith(
        '/comercial/checkout/',
        { precio: 'precio-456', alumnos: 300 },
        {
          headers: {
            'Idempotency-Key': 'key-test-uuid',
          },
        },
      );
    });
  });

  it('reintenta el mismo checkout sin generar una orden local', async () => {
    const compra = { precioId: 'precio-456', alumnos: 3, idempotencyKey: 'intento-original',
      cotizacion: { total: '107.50', moneda: 'MXN' } };
    api.post.mockRejectedValueOnce(new Error('Network Error'));
    await expect(comercialService.crearCheckout(compra)).rejects.toThrow('Network Error');
    api.post.mockResolvedValueOnce({ data: { orden: 'orden-servidor' } });
    await expect(comercialService.crearCheckout(compra)).resolves.toEqual({ orden: 'orden-servidor' });
    expect(api.post.mock.calls[0]).toEqual(api.post.mock.calls[1]);
    expect(api.post.mock.calls[1][1]).toMatchObject({ importe_esperado: '107.50', moneda_esperada: 'MXN' });
  });

  describe('solicitarFactura', () => {
    it('normaliza el RFC a mayúsculas y envía los datos requeridos', async () => {
      const datos = {
        orden: 'ord-123',
        rfc: 'ime190101abc',
        razon_social: 'Escuela Demo',
        regimen: '601',
        codigo_postal: '06700',
        uso_cfdi: 'G03',
      };
      api.post.mockResolvedValueOnce({ data: { id: 'fac-1', ...datos, rfc: 'IME190101ABC' } });

      const res = await comercialService.solicitarFactura(datos);
      expect(res.rfc).toBe('IME190101ABC');
      expect(api.post).toHaveBeenCalledWith('/comercial/facturas/', {
        orden: 'ord-123',
        rfc: 'IME190101ABC',
        razon_social: 'Escuela Demo',
        regimen: '601',
        codigo_postal: '06700',
        uso_cfdi: 'G03',
      });
    });
  });
});
