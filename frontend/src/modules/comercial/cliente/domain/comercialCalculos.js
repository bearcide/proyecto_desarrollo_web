/**
 * Utilidades puras de cálculo, formateo y validación comercial
 * Contrato: docs/CONTRATO_COMERCIAL_API.md
 */

export const MODALIDADES = {
  monthly: {
    clave: 'monthly',
    etiqueta: 'Suscripción Mensual',
    etiquetaCorta: 'Mensual',
    descripcion: 'Cobro recurrente cada 30 días, cancelable en cualquier momento.',
    recurrente: true,
    icono: 'calendar',
  },
  annual: {
    clave: 'annual',
    etiqueta: 'Suscripción Anual',
    etiquetaCorta: 'Anual',
    descripcion: 'Facturación anual con descuento preferencial e inversión garantizada.',
    recurrente: true,
    icono: 'award',
  },
  process: {
    clave: 'process',
    etiqueta: 'Por Proceso de Inscripción',
    etiquetaCorta: 'Por Proceso',
    descripcion: 'Paga únicamente por el periodo o ciclo activo de inscripciones escolares.',
    recurrente: false,
    icono: 'clock',
  },
  institutional: {
    clave: 'institutional',
    etiqueta: 'Licencia Institucional',
    etiquetaCorta: 'Institucional',
    descripcion: 'Licencia para planteles consolidados con soporte directo y alta concurrencia.',
    recurrente: false,
    icono: 'building',
  },
  perpetual: {
    clave: 'perpetual',
    etiqueta: 'Licencia Perpetua',
    etiquetaCorta: 'Perpetua',
    descripcion: 'Adquisición de software de uso vitalicio en tu propia infraestructura o nube.',
    recurrente: false,
    icono: 'shield',
  },
  hybrid: {
    clave: 'hybrid',
    etiqueta: 'Modelo Híbrido',
    etiquetaCorta: 'Híbrido',
    descripcion: 'Combinación de licencia base más cuota flexible de consumo por ciclo.',
    recurrente: true,
    icono: 'layers',
  },
  enterprise: {
    clave: 'enterprise',
    etiqueta: 'Contrato Personalizado',
    etiquetaCorta: 'Enterprise',
    descripcion: 'Términos a la medida, múltiples planteles, integraciones y SLA prioritario.',
    recurrente: false,
    icono: 'sliders',
  },
  maintenance: {
    clave: 'maintenance',
    etiqueta: 'Póliza de Mantenimiento',
    etiquetaCorta: 'Mantenimiento',
    descripcion: 'Actualizaciones de seguridad, parches y soporte para licencias perpetuas.',
    recurrente: true,
    icono: 'refresh',
  },
};

/**
 * Formatea un número o string numérico como moneda en pesos mexicanos (MXN).
 */
export function formatearMoneda(valor, moneda = 'MXN') {
  const numero = typeof valor === 'string' ? parseFloat(valor) : (valor || 0);
  if (isNaN(numero)) return '$0.00 MXN';

  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: moneda || 'MXN',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(numero);
}

/**
 * Genera una clave de idempotencia UUID v4 segura.
 */
export function generarIdempotencyKey() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Calcula el desglose y costo estimado para el configurador.
 * Importante: La cifra final oficial SIEMPRE es calculada y sellada por Django en el backend.
 */
export function calcularTotalEstimado({
  precio = null,
  alumnos = 1,
  planteles = 1,
  addOns = [],
}) {
  if (!precio) {
    return {
      base: 0,
      cuotaAlumnos: 0,
      cuotaPlanteles: 0,
      costoAddOns: 0,
      total: 0,
      moneda: 'MXN',
    };
  }

  const importeBase = parseFloat(precio.importe) || 0;
  const cuotaPorAlumno = parseFloat(precio.por_alumno) || 0;

  // Los primeros 50 alumnos suelen estar cubiertos en la base, o cobro proporcional
  const cantidadAlumnos = Math.max(1, parseInt(alumnos, 10) || 1);
  const cuotaAlumnos = cuotaPorAlumno * cantidadAlumnos;

  // Planteles adicionales (+10% base por cada plantel extra después del primero)
  const numPlanteles = Math.max(1, parseInt(planteles, 10) || 1);
  const cuotaPlanteles = numPlanteles > 1 ? importeBase * 0.15 * (numPlanteles - 1) : 0;

  // Add-ons seleccionados
  const costoAddOns = addOns.reduce((acc, addon) => acc + (parseFloat(addon.costo) || 0), 0);

  const total = importeBase + cuotaAlumnos + cuotaPlanteles + costoAddOns;

  return {
    base: importeBase,
    cuotaAlumnos,
    cuotaPlanteles,
    costoAddOns,
    total: Math.round(total * 100) / 100,
    moneda: precio.moneda || 'MXN',
  };
}

/**
 * Validador para solicitud de comprobante fiscal (Factura B2B) en México.
 */
export function validarDatosFacturacion(datos = {}) {
  const errores = {};
  const rfcLimpio = (datos.rfc || '').trim().toUpperCase();

  // RFC Persona Física (13 car.) o Moral (12 car.)
  const regexRFC = /^([A-ZÑ&]{3,4}) ?(?:- ?)?(\d{6}) ?(?:- ?)?([A-Z0-9]{3})$/;
  if (!rfcLimpio) {
    errores.rfc = 'El RFC es obligatorio.';
  } else if (!regexRFC.test(rfcLimpio)) {
    errores.rfc = 'Formato de RFC inválido (debe tener 12 o 13 caracteres válidos).';
  }

  if (!datos.razon_social || datos.razon_social.trim().length < 3) {
    errores.razon_social = 'La razón social o denominación escolar es obligatoria.';
  }

  if (!datos.codigo_postal || !/^\d{5}$/.test(datos.codigo_postal.trim())) {
    errores.codigo_postal = 'El código postal fiscal debe contener 5 dígitos numéricos.';
  }

  if (!datos.regimen) {
    errores.regimen = 'Selecciona el régimen fiscal del contribuyente.';
  }

  if (!datos.uso_cfdi) {
    errores.uso_cfdi = 'Selecciona el uso de CFDI solicitado.';
  }

  return {
    valido: Object.keys(errores).length === 0,
    errores,
    rfcFormateado: rfcLimpio,
  };
}

/**
 * Clasifica los estados de pago / orden / suscripción con badges semánticos.
 */
export function clasificarEstado(estado) {
  const norm = (estado || '').toLowerCase();
  switch (norm) {
    case 'paid':
    case 'active':
    case 'completado':
      return {
        badge: 'badge-success',
        etiqueta: 'Aprobado / Activo',
        descripcion: 'La transacción ha sido acreditada y tu servicio está plenamente habilitado.',
        tipo: 'success',
      };
    case 'pending':
    case 'requested':
    case 'processing':
      return {
        badge: 'badge-warning',
        etiqueta: 'Pendiente de Confirmación',
        descripcion: 'Estamos a la espera de la confirmación bancaria o validación del operador.',
        tipo: 'warning',
      };
    case 'failed':
    case 'rejected':
    case 'revoked':
      return {
        badge: 'badge-danger',
        etiqueta: 'Rechazado / Cancelado',
        descripcion: 'No se pudo completar la operación o el cobro fue declinado por el emisor.',
        tipo: 'danger',
      };
    case 'past_due':
      return {
        badge: 'badge-danger',
        etiqueta: 'Pago Vencido',
        descripcion: 'Tu última renovación no pudo procesarse. Por favor actualiza tu método de pago.',
        tipo: 'danger',
      };
    case 'canceled':
      return {
        badge: 'badge-neutral',
        etiqueta: 'Cancelado',
        descripcion: 'El plan ha sido cancelado y continuará vigente hasta el final del periodo pagado.',
        tipo: 'neutral',
      };
    default:
      return {
        badge: 'badge-neutral',
        etiqueta: estado || 'Desconocido',
        descripcion: 'Estado en consulta.',
        tipo: 'neutral',
      };
  }
}
