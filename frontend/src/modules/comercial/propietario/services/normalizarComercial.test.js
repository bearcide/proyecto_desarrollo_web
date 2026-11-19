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
  normalizarPlanComercial,
  normalizarSuscripcionComercial,
} from './normalizarComercial';

describe('extraerRegistros', () => {
  test('devuelve el array cuando la respuesta ya es una lista', () => {
    expect(extraerRegistros([{ id: 1 }])).toEqual([{ id: 1 }]);
  });

  test('extrae results de una respuesta paginada de DRF', () => {
    expect(
      extraerRegistros({ count: 2, next: null, previous: null, results: [{ id: 1 }, { id: 2 }] }),
    ).toEqual([{ id: 1 }, { id: 2 }]);
  });

  test('devuelve lista vacía para respuestas vacías', () => {
    expect(extraerRegistros(null)).toEqual([]);
    expect(extraerRegistros({})).toEqual([]);
  });
});

describe('extraerContador', () => {
  test('lee el contador de una respuesta paginada', () => {
    expect(extraerContador({ count: 42, results: [{}, {}, {}] }, 0)).toBe(42);
  });

  test('cae al fallback cuando no hay contador', () => {
    expect(extraerContador(null, 7)).toBe(7);
  });
});

describe('normalizarIndicadores', () => {
  test('devuelve ceros cuando el backend no reporta indicadores', () => {
    const indicadores = normalizarIndicadores(null);
    expect(indicadores.institucionesRegistradas).toBe(0);
    expect(indicadores.ingresosRegistrados).toBe(0);
    expect(indicadores.renovacionesProximas).toBe(0);
  });

  test('suma instituciones registradas cuando llega la colección completa', () => {
    const indicadores = normalizarIndicadores({ instituciones: [{}, {}, {}] });
    expect(indicadores.institucionesRegistradas).toBe(3);
  });

  test('lee indicadores numéricos con nomenclatura alternativa', () => {
    const indicadores = normalizarIndicadores({
      instituciones_registradas: 12,
      licencias_vigentes: 9,
      total_ingresos: 1500000,
    });
    expect(indicadores.institucionesRegistradas).toBe(12);
    expect(indicadores.licenciasVigentes).toBe(9);
    expect(indicadores.ingresosRegistrados).toBe(1500000);
  });
});

describe('normalizarEstado', () => {
  test('normaliza a mayúsculas y recorta espacios', () => {
    expect(normalizarEstado(' activo ')).toBe('ACTIVO');
    expect(normalizarEstado('Vigente')).toBe('VIGENTE');
    expect(normalizarEstado(null)).toBe('');
  });
});

describe('normalizarEscuelaComercial', () => {
  test('expone nombre, plan y estado de la institución', () => {
    const escuela = normalizarEscuelaComercial({
      id: 'uuid-1',
      nombre_comercial: 'Escuela Aurora',
      plan_suscripcion: 'PRO',
      estado_escuela: 'ACTIVO',
      activo: true,
    });
    expect(escuela.id).toBe('uuid-1');
    expect(escuela.nombre).toBe('Escuela Aurora');
    expect(escuela.plan).toBe('PRO');
    expect(escuela.estado).toBe('ACTIVO');
    expect(escuela.activo).toBe(true);
  });
});

describe('normalizarPlanComercial', () => {
  test('expone precio, periodicidad, límites y funcionalidades del plan', () => {
    const plan = normalizarPlanComercial({
      id: 'b1020000-0000-4000-8000-000000000002',
      codigo: 'pro',
      nombre: 'Plan Profesional Campus',
      max_alumnos: 2500,
      max_planteles: 3,
      funcionalidades: ['Anti-empalme', 'CSV'],
      activo: true,
    });
    expect(plan.nombre).toBe('Plan Profesional Campus');
    expect(plan.disponible).toBe(true);
    expect(plan.limiteAlumnos).toBe(2500);
    expect(plan.plantelesPermitidos).toBe(3);
    expect(plan.modulos).toHaveLength(2);
  });
});

describe('normalizarSuscripcionComercial', () => {
  test('expone estado, periodo y monto de la suscripción', () => {
    const suscripcion = normalizarSuscripcionComercial({
      id: 'sub-1',
      plan_nombre: 'Plan Profesional Campus',
      estado: 'active',
      fin_periodo: '2027-03-01',
      importe: '34990.00',
    });
    expect(suscripcion.estado).toBe('ACTIVE');
    expect(suscripcion.fechaFin).toBe('2027-03-01');
    expect(suscripcion.monto).toBe('34990.00');
  });
});

describe('vigencia y renovaciones', () => {
  const HOY = new Date(2026, 10, 12, 0, 0, 0);

  test('licencia vigente cuando la fecha fin no ha pasado', () => {
    expect(esVigente(new Date(2026, 11, 31), HOY)).toBe(true);
  });

  test('licencia vencida cuando la fecha fin ya pasó', () => {
    expect(esVencido(new Date(2026, 10, 11), HOY)).toBe(true);
    expect(esVencido(new Date(2026, 10, 12), HOY)).toBe(false);
  });

  test('sin fecha fin no se considera vigente', () => {
    expect(esVigente(null, HOY)).toBe(false);
    expect(esVigente('', HOY)).toBe(false);
  });

  test('renovación próxima dentro de los próximos 30 días', () => {
    expect(esRenovacionProxima(new Date(2026, 11, 10), 30, HOY)).toBe(true);
  });

  test('renovación lejana no se considera próxima', () => {
    expect(esRenovacionProxima(new Date(2027, 5, 10), 30, HOY)).toBe(false);
  });
});

describe('formateo', () => {
  test('formatea importes monetarios con dos decimales', () => {
    expect(formatearMoneda(1500)).toContain('1,500');
    expect(formatearMoneda(null)).toContain('0');
  });

  test('formatea fechas a texto legible', () => {
    expect(formatearFecha('2026-12-31T00:00:00Z')).toBeTruthy();
    expect(formatearFecha(null)).toBeNull();
  });
});
