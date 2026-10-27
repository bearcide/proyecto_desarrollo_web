/**
 * Validador de inscripción: reglas de negocio puras (sin red ni DOM).
 *
 * Fuente de verdad del front para avisar antes de confirmar; el backend SIEMPRE
 * debe revalidar estas reglas (y más) al recibir la solicitud.
 */

export function cumpleRequisitos(materiasAprobadas = [], requisitos = []) {
  const aprobadas = new Set(materiasAprobadas);
  return requisitos.every((req) => aprobadas.has(req));
}

export function hayCupoDisponible(inscritos = 0, cupoMaximo) {
  return inscritos < cupoMaximo;
}

/** Dos bloques se chocan si se solapan en el mismo día (inicio < fin del otro y viceversa). */
export function hayConflictoHorario(nuevo, horarios = []) {
  if (!nuevo) return false;
  const { dia, inicio, fin } = nuevo;
  return horarios.some((h) => h && h.dia === dia && inicio < h.fin && h.inicio < fin);
}

/**
 * Evalúa una solicitud de inscripción completa:
 * requisitos aprobados -> cupo -> conflicto de horario.
 * Devuelve { valido, motivo? } con motivo en:
 *   'REQUISITOS_NO_CUMPLIDOS' | 'SIN_CUPO' | 'CONFLICTO_HORARIO'
 */
export function evaluarSolicitudInscripcion({
  materiasAprobadas = [],
  requisitos = [],
  inscritosActuales = 0,
  cupoMaximo,
  horarioNuevo = null,
  horariosActuales = [],
} = {}) {
  if (!cumpleRequisitos(materiasAprobadas, requisitos)) {
    return { valido: false, motivo: 'REQUISITOS_NO_CUMPLIDOS' };
  }
  if (!hayCupoDisponible(inscritosActuales, cupoMaximo)) {
    return { valido: false, motivo: 'SIN_CUPO' };
  }
  if (horarioNuevo && hayConflictoHorario(horarioNuevo, horariosActuales)) {
    return { valido: false, motivo: 'CONFLICTO_HORARIO' };
  }
  return { valido: true };
}
