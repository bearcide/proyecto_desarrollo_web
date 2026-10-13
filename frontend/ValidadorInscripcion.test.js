const {
  cumpleRequisitos,
  hayCupoDisponible,
  hayConflictoHorario,
  evaluarSolicitudInscripcion,
} = require('../domain/ValidadorInscripcion');

describe('cumpleRequisitos', () => {
  test('permite inscripción si se cumplen todos los requisitos', () => {
    const resultado = cumpleRequisitos(['Cálculo I', 'Álgebra'], ['Cálculo I']);
    expect(resultado).toBe(true);
  });

  test('rechaza inscripción si falta un requisito', () => {
    const resultado = cumpleRequisitos(['Álgebra'], ['Cálculo I']);
    expect(resultado).toBe(false);
  });

  test('permite inscripción si no hay requisitos', () => {
    const resultado = cumpleRequisitos([], []);
    expect(resultado).toBe(true);
  });
});

describe('hayCupoDisponible', () => {
  test('hay cupo si los inscritos son menores al máximo', () => {
    expect(hayCupoDisponible(29, 30)).toBe(true);
  });

  test('no hay cupo si el grupo está lleno', () => {
    expect(hayCupoDisponible(30, 30)).toBe(false);
  });
});

describe('hayConflictoHorario', () => {
  const horarioLunes8a10 = { dia: 'Lunes', inicio: 8, fin: 10 };

  test('detecta conflicto cuando los horarios se empalman', () => {
    const nuevo = { dia: 'Lunes', inicio: 9, fin: 11 };
    expect(hayConflictoHorario(nuevo, [horarioLunes8a10])).toBe(true);
  });

  test('no hay conflicto si son días distintos', () => {
    const nuevo = { dia: 'Martes', inicio: 8, fin: 10 };
    expect(hayConflictoHorario(nuevo, [horarioLunes8a10])).toBe(false);
  });

  test('no hay conflicto si los horarios son consecutivos sin empalme', () => {
    const nuevo = { dia: 'Lunes', inicio: 10, fin: 12 };
    expect(hayConflictoHorario(nuevo, [horarioLunes8a10])).toBe(false);
  });
});

describe('evaluarSolicitudInscripcion', () => {
  const base = {
    materiasAprobadas: ['Cálculo I'],
    requisitos: ['Cálculo I'],
    inscritosActuales: 10,
    cupoMaximo: 30,
    horarioNuevo: { dia: 'Lunes', inicio: 8, fin: 10 },
    horariosActuales: [],
  };

  test('solicitud válida cuando todo se cumple', () => {
    const resultado = evaluarSolicitudInscripcion(base);
    expect(resultado).toEqual({ valido: true });
  });

  test('solicitud inválida por requisitos no cumplidos', () => {
    const resultado = evaluarSolicitudInscripcion({
      ...base,
      materiasAprobadas: [],
    });
    expect(resultado).toEqual({ valido: false, motivo: 'REQUISITOS_NO_CUMPLIDOS' });
  });

  test('solicitud inválida por falta de cupo', () => {
    const resultado = evaluarSolicitudInscripcion({
      ...base,
      inscritosActuales: 30,
    });
    expect(resultado).toEqual({ valido: false, motivo: 'SIN_CUPO' });
  });

  test('solicitud inválida por conflicto de horario', () => {
    const resultado = evaluarSolicitudInscripcion({
      ...base,
      horariosActuales: [{ dia: 'Lunes', inicio: 9, fin: 11 }],
    });
    expect(resultado).toEqual({ valido: false, motivo: 'CONFLICTO_HORARIO' });
  });
});
