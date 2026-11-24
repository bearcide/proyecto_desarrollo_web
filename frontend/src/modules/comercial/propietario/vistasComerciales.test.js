import { describe, test, expect, vi } from 'vitest';
import { createApp, nextTick } from 'vue';
import { createPinia } from 'pinia';
import api from '../../../api';
import DashboardComercialView from './views/DashboardComercialView.vue';
import ClientesComercialesView from './views/ClientesComercialesView.vue';
import PlanesComercialesView from './views/PlanesComercialesView.vue';
import SuscripcionesComercialesView from './views/SuscripcionesComercialesView.vue';
import LicenciasComercialesView from './views/LicenciasComercialesView.vue';
import FacturacionComercialView from './views/FacturacionComercialView.vue';
import { RUTAS_COMERCIALES, obtenerIndicadoresComerciales, obtenerPagosComerciales } from './services/apiComercial';
import {
  extraerContador,
  extraerRegistros,
  esRenovacionProxima,
  esVigente,
  esVencido,
  formatearFecha,
  formatearMoneda,
  normalizarEstado,
  normalizarIndicadores,
  normalizarEscuelaComercial,
} from './services/normalizarComercial';

describe('Módulo comercial del propietario — smoke de compilación y normalización', () => {
  test('todas las vistas del panel comercial se cargan como componentes', () => {
    expect(DashboardComercialView).toBeTruthy();
    expect(ClientesComercialesView).toBeTruthy();
    expect(PlanesComercialesView).toBeTruthy();
    expect(SuscripcionesComercialesView).toBeTruthy();
    expect(LicenciasComercialesView).toBeTruthy();
    expect(FacturacionComercialView).toBeTruthy();
  });

  test('monta facturación y consulta transacciones y solicitudes al abrir la vista', async () => {
    const get = vi.spyOn(api, 'get').mockImplementation(async (url) => ({
      data: url === '/comercial/transacciones/'
        ? [{ id: 'pago', comprobante_id: 'recibo', institucion: 'Escuela A', estado: 'paid' }]
        : [],
    }));
    const elemento = document.createElement('div');
    const app = createApp(FacturacionComercialView);
    app.use(createPinia());
    try {
      app.mount(elemento);
      await vi.waitFor(async () => {
        await nextTick();
        expect(elemento.textContent).toContain('Escuela A');
        expect(elemento.textContent).toContain('Descargar');
      });
      expect(get).toHaveBeenCalledWith('/comercial/facturas/', { params: { page: 1 } });
    } finally {
      app.unmount();
      get.mockRestore();
    }
  });

  test('las rutas provisionales del contrato comercial se exponen', () => {
    expect(RUTAS_COMERCIALES.ingresos).toContain('/comercial/ingresos/');
    expect(RUTAS_COMERCIALES.instituciones).toContain('/comercial/instituciones/');
    expect(typeof RUTAS_COMERCIALES.institucionesDetalle).toBe('function');
    expect(RUTAS_COMERCIALES.transacciones).toContain('/comercial/transacciones/');
    expect(RUTAS_COMERCIALES.facturas).toContain('/comercial/facturas/');
  });

  test('los servicios comerciales delegan en la API compartida', async () => {
    expect(typeof obtenerIndicadoresComerciales).toBe('function');
    expect(typeof obtenerPagosComerciales).toBe('function');
  });

  test('normalizadores comerciales consistentes', () => {
    expect(extraerRegistros({ results: [{ id: 1 }], count: 1 })).toHaveLength(1);
    expect(extraerContador({ count: 9, results: [{}, {}, {}] }, 0)).toBe(9);
    expect(normalizarIndicadores({}).ingresosRegistrados).toBe(0);
    expect(normalizarEstado('activo')).toBe('ACTIVO');
    expect(normalizarEscuelaComercial({ nombre_comercial: 'Aurora', plan_suscripcion: 'PRO' }).plan).toBe('PRO');
    expect(formatearMoneda(1500)).toContain('1,500');
    expect(formatearFecha('2026-12-31')).toBeTruthy();
    expect(esVigente('2026-12-31', new Date('2026-11-12T00:00:00Z'))).toBe(true);
    expect(esVencido('2026-11-11', new Date('2026-11-12T00:00:00Z'))).toBe(true);
    expect(esRenovacionProxima(new Date(2026, 11, 10), 30, new Date(2026, 10, 12))).toBe(true);
  });
});
