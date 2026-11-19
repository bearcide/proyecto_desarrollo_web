import { describe, it, expect } from 'vitest';
import {
  formatearMoneda,
  generarIdempotencyKey,
  calcularTotalEstimado,
  validarDatosFacturacion,
  clasificarEstado,
  MODALIDADES,
} from './comercialCalculos';

describe('comercialCalculos', () => {
  describe('formatearMoneda', () => {
    it('formatea cifras numéricas en formato de moneda MXN', () => {
      const formatted = formatearMoneda(1499);
      expect(formatted).toContain('1,499.00');
    });

    it('formatea cadenas decimales', () => {
      const formatted = formatearMoneda('25000.50');
      expect(formatted).toContain('25,000.50');
    });

    it('maneja valores vacíos o nulos sin romperse', () => {
      expect(formatearMoneda(null)).toContain('0.00');
      expect(formatearMoneda(undefined)).toContain('0.00');
    });
  });

  describe('generarIdempotencyKey', () => {
    it('genera una clave no vacía con formato UUID', () => {
      const key1 = generarIdempotencyKey();
      const key2 = generarIdempotencyKey();
      expect(key1).toBeTruthy();
      expect(key2).toBeTruthy();
      expect(key1).not.toBe(key2);
      expect(key1).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
    });
  });

  describe('calcularTotalEstimado', () => {
    it('calcula correctamente base + alumnos', () => {
      const precio = {
        importe: '1000.00',
        por_alumno: '10.00',
        moneda: 'MXN',
      };
      const res = calcularTotalEstimado({
        precio,
        alumnos: 100,
        planteles: 1,
      });
      expect(res.base).toBe(1000);
      expect(res.cuotaAlumnos).toBe(1000);
      expect(res.cuotaPlanteles).toBe(0);
      expect(res.total).toBe(2000);
    });

    it('aplica recargo por planteles adicionales', () => {
      const precio = {
        importe: '2000.00',
        por_alumno: '0.00',
        moneda: 'MXN',
      };
      const res = calcularTotalEstimado({
        precio,
        alumnos: 50,
        planteles: 3, // 2 adicionales -> 2 * 15% * 2000 = 600
      });
      expect(res.cuotaPlanteles).toBe(600);
      expect(res.total).toBe(2600);
    });

    it('maneja precio nulo elegantemente', () => {
      const res = calcularTotalEstimado({ precio: null });
      expect(res.total).toBe(0);
    });
  });

  describe('validarDatosFacturacion', () => {
    it('valida RFC persona moral correctamente', () => {
      const res = validarDatosFacturacion({
        rfc: 'IME190101ABC',
        razon_social: 'Inscripción Made Easy S.A.S.',
        codigo_postal: '06700',
        regimen: '601',
        uso_cfdi: 'G03',
      });
      expect(res.valido).toBe(true);
      expect(res.errores).toEqual({});
      expect(res.rfcFormateado).toBe('IME190101ABC');
    });

    it('rechaza RFC con formato inválido', () => {
      const res = validarDatosFacturacion({
        rfc: 'RFCINCORRECTO',
        razon_social: 'Escuela Demo',
        codigo_postal: '12345',
        regimen: '601',
        uso_cfdi: 'G03',
      });
      expect(res.valido).toBe(false);
      expect(res.errores.rfc).toBeDefined();
    });

    it('rechaza código postal con longitud diferente a 5 dígitos', () => {
      const res = validarDatosFacturacion({
        rfc: 'IME190101ABC',
        razon_social: 'Escuela Demo',
        codigo_postal: '123',
        regimen: '601',
        uso_cfdi: 'G03',
      });
      expect(res.valido).toBe(false);
      expect(res.errores.codigo_postal).toBeDefined();
    });
  });

  describe('clasificarEstado', () => {
    it('clasifica paid como success', () => {
      const cl = clasificarEstado('paid');
      expect(cl.tipo).toBe('success');
      expect(cl.badge).toBe('badge-success');
    });

    it('clasifica pending como warning', () => {
      const cl = clasificarEstado('pending');
      expect(cl.tipo).toBe('warning');
      expect(cl.badge).toBe('badge-warning');
    });

    it('clasifica failed como danger', () => {
      const cl = clasificarEstado('failed');
      expect(cl.tipo).toBe('danger');
      expect(cl.badge).toBe('badge-danger');
    });
  });

  describe('MODALIDADES', () => {
    it('incluye las 8 modalidades comerciales del contrato', () => {
      expect(MODALIDADES.monthly).toBeDefined();
      expect(MODALIDADES.annual).toBeDefined();
      expect(MODALIDADES.process).toBeDefined();
      expect(MODALIDADES.institutional).toBeDefined();
      expect(MODALIDADES.perpetual).toBeDefined();
      expect(MODALIDADES.hybrid).toBeDefined();
      expect(MODALIDADES.enterprise).toBeDefined();
      expect(MODALIDADES.maintenance).toBeDefined();
    });
  });
});
