/**
 * Normalizadores UI del dominio comercial del panel del propietario SaaS.
 *
 * Objetivo: convertir las respuestas del backend financiero/comercial en
 * modelos ya listos para la interfaz, tolerando las nomenclaturas usadas por el
 * contrato (docs/CONTRATO_COMERCIAL_API.md) y por los catálogos de demo.
 *
 * REGLAS DE NEGOCIO DEL FRONTEND:
 * - Ningún normalizador inventa cifras: ausencias o campos no numéricos se
 *   normalizan a 0 / vacío y la interfaz muestra estados vacíos o "—".
 * - Los estados comerciales se normalizan siempre a MAYÚSCULAS.
 * - Las fechas se comparan sin mutar el instante original.
 */

export function extraerRegistros(datos) {
  if (Array.isArray(datos)) return datos;
  if (datos && Array.isArray(datos.results)) return datos.results;
  if (datos && Array.isArray(datos.data)) return datos.data;
  return [];
}

export function extraerContador(datos, fallback = 0) {
  const fuente = datos || {};
  const valor = fuente.count ?? fuente.total ?? fuente.total_count ?? fuente.totalCount ?? fuente.results?.length ?? fallback;
  const numero = Number(valor);
  return Number.isFinite(numero) ? numero : fallback;
}

function leerNumero(datos, ...claves) {
  const fuente = datos || {};
  for (const clave of claves) {
    const valor = fuente[clave];
    if (valor === null || valor === undefined) continue;
    const numero = Number(valor);
    if (Number.isFinite(numero)) return numero;
  }
  return 0;
}

function aFecha(valor) {
  if (valor === null || valor === undefined || valor === '') return null;
  const fecha = valor instanceof Date ? valor : new Date(valor);
  return Number.isNaN(fecha.getTime()) ? null : fecha;
}

function aReferencia(valor) {
  const fecha = aFecha(valor);
  return fecha ? fecha.getTime() : null;
}

/** Vigencia: una suscripción/licencia/contrato se considera vigente mientras no venza. */
export function esVigente(fechaFin, hoy = new Date()) {
  const fin = aFecha(fechaFin);
  const referencia = aFecha(hoy) || new Date();
  if (!fin) return false;
  return fin.getTime() >= referencia.getTime();
}

export function esVencido(fechaFin, hoy = new Date()) {
  const fin = aFecha(fechaFin);
  const referencia = aFecha(hoy) || new Date();
  if (!fin) return false;
  return fin.getTime() < referencia.getTime();
}

export function esRenovacionProxima(fechaFin, dias = 30, hoy = new Date()) {
  const fin = aFecha(fechaFin);
  const referencia = aFecha(hoy) || new Date();
  if (!fin) return false;
  const limite = new Date(referencia.getTime());
  limite.setDate(limite.getDate() + dias);
  const desde = referencia.getTime();
  const hasta = limite.getTime();
  const tiempoFin = fin.getTime();
  return tiempoFin >= desde && tiempoFin <= hasta;
}

export function formatearMoneda(monto, opciones = {}) {
  const valor = Number(monto);
  const numero = Number.isFinite(valor) ? valor : 0;
  const locale = opciones.locale || 'es-MX';
  const moneda = opciones.moneda || 'MXN';
  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: moneda,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(numero);
  } catch (_) {
    return `${numero.toFixed(2)} ${moneda}`;
  }
}

export function formatearFecha(valor, opciones = {}) {
  const fecha = aFecha(valor);
  if (!fecha) return null;
  try {
    return new Intl.DateTimeFormat(options.locale || 'es-MX', {
      year: 'numeric',
      month: options.estilo === 'short' ? 'short' : 'long',
      day: 'numeric',
    }).format(fecha);
  } catch (_) {
    return String(valor);
  }
}

const ETIQUETAS_ESTADOS = Object.freeze({
  // Escuelas / tenants
  ACTIVO: 'Activo',
  ACTIVA: 'Activa',
  INACTIVO: 'Inactivo',
  INACTIVA: 'Inactiva',
  // Suscripciones, licencias y contratos
  ACTIVE: 'Activa',
  PENDING: 'Pendiente',
  PAST_DUE: 'De pago',
  CANCELED: 'Cancelada',
  DRAFT: 'Borrador',
  REVOKED: 'Revocada',
  // Transacciones y comprobantes
  PAID: 'Pagado',
  FAILED: 'Fallido',
  // Solicitudes de facturación (CFDI)
  REQUESTED: 'Solicitada',
  PROCESSING: 'Procesando',
  REJECTED: 'Rechazada',
  // Vigencias
  VIGENTE: 'Vigente',
  VENCIDA: 'Vencida',
  SUSPENDIDA: 'Suspendida',
  PENDIENTE: 'Pendiente',
  CONFIRMADO: 'Confirmado',
  ACTIVADO: 'Activado',
  RENOVADO: 'Renovado',
});

export function normalizarEstado(valor) {
  if (valor === null || valor === undefined) return '';
  if (typeof valor === 'object') {
    return normalizarEstado(valor.codigo ?? valor.estado ?? valor.nombre ?? valor.value);
  }
  return String(valor).trim().toUpperCase();
}

export function etiquetaEstado(estado) {
  const valor = normalizarEstado(estado);
  if (!valor) return '—';
  const etiqueta = ETIQUETAS_ESTADOS[valor];
  if (etiqueta) return etiqueta;
  if (valor.length > 1) return valor.charAt(0) + valor.slice(1).toLowerCase();
  return valor;
}

/**
 * Normaliza los indicadores comerciales del dashboard.
 * No inventa cifras: ausencias se reportan como cero.
 */
export function normalizarIndicadores(datos = {}) {
  const fuente = datos || {};
  const instituciones = Array.isArray(fuente.instituciones)
    ? fuente.instituciones
    : Array.isArray(fuente.instituciones_registradas)
      ? fuente.instituciones_registradas
      : [];

  return {
    institucionesRegistradas: leerNumero(
      fuente, 'institucionesRegistradas', 'instituciones_registradas', 'total_instituciones', 'instituciones',
    ) || instituciones.length,
    institucionesContratantes: leerNumero(
      fuente, 'institucionesContratantes', 'instituciones_contratantes', 'contratantes',
    ),
    suscripcionesActivas: leerNumero(
      fuente, 'suscripcionesActivas', 'suscripciones_activas', 'suscripciones',
    ),
    licenciasVigentes: leerNumero(
      fuente, 'licenciasVigentes', 'licencias_vigentes', 'licencias',
    ),
    ingresosRegistrados: leerNumero(
      fuente, 'ingresosRegistrados', 'ingresos', 'monto_ingresos', 'ingresos_totales', 'total_ingresos',
    ),
    pagosPendientes: leerNumero(
      fuente, 'pagosPendientes', 'pagos_pendientes', 'pagos',
    ),
    contratosVencidos: leerNumero(
      fuente, 'contratosVencidos', 'contratos_vencidos', 'contratos',
    ),
    renovacionesProximas: leerNumero(
      fuente, 'renovacionesProximas', 'renovaciones_proximas', 'renovaciones',
    ),
  };
}

/** Normaliza una institución (escuela / tenant) comercial. */
export function normalizarEscuelaComercial(datos = {}) {
  const fuente = datos || {};
  const nombre = fuente.nombre_comercial ?? fuente.nombre ?? fuente.nombreEscuela ?? fuente.nombre_escuela ?? 'Sin nombre';
  const plan = fuente.plan_suscripcion ?? fuente.plan ?? fuente.planComercial ?? fuente.plan_comercial ?? null;
  const estado = normalizarEstado(fuente.estado_escuela ?? fuente.estado ?? fuente.estadoEscuela);

  return {
    id: fuente.id ?? fuente.tenant ?? null,
    nombre,
    plan,
    estado,
    activo: Boolean(fuente.activo ?? normalizarEstado(fuente.estado_escuela ?? fuente.estado ?? fuente.estadoEscuela) === 'ACTIVO'),
  };
}

/** Normaliza un plan comercial (código, precio, periodicidad, límites, funcionalidades, disponibilidad). */
export function normalizarPlanComercial(datos = {}) {
  const fuente = datos || {};
  const modalidad = fuente.modalidad ?? fuente.periodicidad ?? fuente.frecuencia ?? null;
  const MODALIDADES = Object.freeze({
    monthly: 'Mensual',
    annual: 'Anual',
    process: 'Por proceso',
    institutional: 'Institucional',
    perpetual: 'Perpetua',
    hybrid: 'Híbrido',
    enterprise: 'Enterprise',
    maintenance: 'Mantenimiento',
  });

  const estadoDisponibilidad = typeof fuente.activo === 'boolean'
    ? (fuente.activo ? 'ACTIVO' : 'INACTIVO')
    : normalizarEstado(fuente.estado ?? fuente.estado_plan ?? fuente.disponibilidad ?? fuente.status);
  const disponible = Boolean(fuente.disponible ?? fuente.activo ?? estadoDisponibilidad === 'ACTIVO');

  return {
    id: fuente.id ?? null,
    codigo: fuente.codigo ?? fuente.plan_codigo ?? null,
    nombre: fuente.nombre ?? fuente.nombre_plan ?? 'Plan sin nombre',
    descripcion: fuente.descripcion ?? null,
    precio: fuente.importe ?? fuente.precio ?? fuente.importe_mensual ?? fuente.monto_mensual ?? null,
    periodicidad: MODALIDADES[modalidad] ?? modalidad ?? null,
    limiteAlumnos: fuente.max_alumnos ?? fuente.limiteAlumnos ?? fuente.limite_alumnos ?? null,
    plantelesPermitidos: fuente.max_planteles ?? fuente.plantelesPermitidos ?? fuente.planteles_permitidos ?? null,
    modulos: Array.isArray(fuente.funcionalidades)
      ? fuente.funcionalidades
      : (Array.isArray(fuente.modulos) ? fuente.modulos : []),
    estado: estadoDisponibilidad,
    disponible,
  };
}

/** Normaliza una suscripción comercial. */
export function normalizarSuscripcionComercial(datos = {}) {
  const fuente = datos || {};

  return {
    id: fuente.id ?? null,
    institucion: fuente.nombre_escuela ?? fuente.institucion ?? fuente.escuela ?? fuente.tenant_nombre ?? null,
    plan: fuente.plan_nombre ?? fuente.plan ?? fuente.planComercial ?? fuente.plan_comercial ?? null,
    estado: normalizarEstado(fuente.estado ?? fuente.estadoSuscripcion ?? fuente.status),
    fechaInicio: fuente.inicio ?? fuente.fecha_inicio ?? fuente.fechaInicio ?? fuente.start_date ?? null,
    fechaFin: fuente.fin_periodo ?? fuente.fecha_fin ?? fuente.fechaFin ?? fuente.renovacion ?? fuente.end_date ?? null,
    licencia: fuente.orden ?? fuente.licencia ?? fuente.licencia_id ?? null,
    monto: fuente.importe ?? fuente.monto ?? fuente.monto_mensual ?? fuente.amount ?? null,
    cancelacionProgramada: Boolean(fuente.cancel_at_period_end ?? fuente.cancelAtPeriodEnd ?? false),
    cancelada: Boolean(fuente.cancelada ?? false) || normalizarEstado(fuente.estado ?? fuente.estadoSuscripcion ?? fuente.status) === 'CANCELED',
  };
}

/** Normaliza una licencia comercial. */
export function normalizarLicenciaComercial(datos = {}) {
  const fuente = datos || {};

  return {
    id: fuente.id ?? null,
    suscripcion: fuente.orden ?? fuente.suscripcion ?? fuente.subscription ?? null,
    institucion: fuente.institucion ?? fuente.escuela ?? fuente.tenant_nombre ?? null,
    plan: fuente.plan_nombre ?? fuente.plan ?? fuente.planComercial ?? null,
    estado: normalizarEstado(fuente.estado ?? fuente.estadoLicencia ?? fuente.status),
    fechaEmision: fuente.inicio ?? fuente.fecha_emision ?? fuente.fechaEmision ?? fuente.created_at ?? null,
    fechaVencimiento: fuente.fin ?? fuente.fecha_vencimiento ?? fuente.fechaVencimiento ?? fuente.expira_at ?? null,
    activo: Boolean(fuente.activo ?? normalizarEstado(fuente.estado ?? fuente.estadoLicencia ?? fuente.status) === 'ACTIVE'),
    limite: fuente.max_alumnos ?? fuente.limite ?? fuente.alumnos_limite ?? null,
    usados: fuente.usados ?? fuente.alumnosUsados ?? null,
    revocada: normalizarEstado(fuente.estado ?? fuente.estadoLicencia ?? fuente.status) === 'REVOKED',
  };
}

/** Normaliza un pago / transacción comercial. */
export function normalizarPagoComercial(datos = {}) {
  const fuente = datos || {};

  return {
    id: fuente.id ?? null,
    institucion: fuente.institucion ?? fuente.escuela ?? fuente.tenant_nombre ?? null,
    fecha: fuente.fecha ?? fuente.fecha_pago ?? fuente.created_at ?? fuente.creado ?? null,
    importe: fuente.importe ?? fuente.monto ?? fuente.amount ?? fuente.total ?? null,
    estado: normalizarEstado(fuente.estado ?? fuente.status ?? fuente.estadoPago),
    referenciaProveedor: fuente.referencia ?? fuente.referencia_proveedor ?? fuente.providerReference ?? fuente.provider_ref ?? null,
    comprobante: fuente.comprobante ?? fuente.comprobante_id ?? fuente.comprobanteId ?? fuente.folio ?? fuente.comprobanteUrl ?? null,
    factura: fuente.factura ?? fuente.factura_id ?? fuente.invoice ?? fuente.invoiceNumber ?? fuente.folio ?? null,
  };
}

/** Normaliza una solicitud de facturación. */
export function normalizarSolicitudFacturacion(datos = {}) {
  const fuente = datos || {};

  return {
    id: fuente.id ?? null,
    institucion: fuente.institucion ?? fuente.escuela ?? fuente.tenant_nombre ?? null,
    estado: normalizarEstado(fuente.estado ?? fuente.status ?? fuente.estadoSolicitud),
    fechaSolicitud: fuente.fecha ?? fuente.fecha_solicitud ?? fuente.fechaSolicitud ?? fuente.created_at ?? null,
    comprobante: fuente.comprobante ?? fuente.comprobante_id ?? fuente.comprobanteId ?? fuente.transaccion ?? null,
    numeroFactura: fuente.folio ?? fuente.numero_factura ?? fuente.numeroFactura ?? fuente.invoiceNumber ?? null,
  };
}
