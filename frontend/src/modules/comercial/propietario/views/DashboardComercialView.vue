<template>
  <div class="comercial-dashboard">
    <div class="page-header">
      <div>
        <h1 class="page-title">Panel Comercial del Propietario</h1>
        <p class="page-subtitle">Indicadores de adopción, facturación y renovaciones del SaaS InscripcionMadeEasy</p>
      </div>
      <div class="header-actions">
        <button
          type="button"
          class="btn btn-secondary btn-sm"
          :disabled="cargando"
          @click="cargarIndicadoresComerciales"
        >
          <svg :class="{ spinner: cargando }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
          Actualizar indicadores
        </button>
        <router-link to="/comercial/propietario/clientes" class="btn btn-outline btn-sm">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
          Clientes
        </router-link>
      </div>
    </div>

    <div v-if="error" class="alert alert-danger" role="alert">
      <span>{{ error }}</span>
      <button type="button" class="btn btn-secondary btn-sm" :disabled="cargando" @click="cargarIndicadoresComerciales">
        Reintentar
      </button>
    </div>

    <div v-if="cargando" class="empty-state">
      <div class="spinner spinner-primary" style="margin: 0 auto 0.5rem;"></div>
      <span class="text-muted">Cargando indicadores comerciales…</span>
    </div>

    <template v-else>
      <!-- Indicadores comerciales (Fase 1) -->
      <div class="stats-grid">
        <div
          v-for="tarjeta in tarjetasIndicadores"
          :key="tarjeta.clave"
          class="stat-card"
          :class="tarjeta.clase"
        >
          <div class="stat-header">
            <span class="stat-label">{{ tarjeta.etiqueta }}</span>
            <div class="stat-icon">
              <AppIcon :name="tarjeta.icono" :size="20" />
            </div>
          </div>
          <div class="stat-value">{{ tarjeta.valor }}</div>
          <div class="stat-subtext">{{ tarjeta.subtexto }}</div>
        </div>
      </div>

      <div class="dashboard-grid">
        <!-- Prioridad comercial -->
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              Prioridad Comercial
            </h2>
          </div>
          <div class="card-body">
            <p class="text-sm text-muted" style="margin-bottom: 1rem;">
              Señales de facturación y renovación que requieren la atención del propietario.
            </p>
            <div class="prioridad-lista">
              <div class="prioridad-item">
                <span class="prioridad-texto">
                  <strong>Contratos vencidos</strong>
                  <span class="text-sm text-muted">Renovación pendiente de inmediato</span>
                </span>
                <span class="prioridad-valor">{{ indicadores.contratosVencidos }}</span>
              </div>
              <div class="prioridad-item">
                <span class="prioridad-texto">
                  <strong>Renovaciones próximas</strong>
                  <span class="text-sm text-muted">Dentro de los próximos 30 días</span>
                </span>
                <span class="prioridad-valor">{{ indicadores.renovacionesProximas }}</span>
              </div>
              <div class="prioridad-item">
                <span class="prioridad-texto">
                  <strong>Pagos pendientes</strong>
                  <span class="text-sm text-muted">Ingresos por conciliar</span>
                </span>
                <span class="prioridad-valor">{{ indicadores.pagosPendientes }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Acciones del propietario -->
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
              Acciones del Propietario
            </h2>
          </div>
          <div class="card-body action-cards-list">
            <router-link to="/comercial/propietario/clientes" class="action-card-item">
              <div class="action-icon action-icon-indigo">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
              </div>
              <div class="action-text">
                <strong>Administración de clientes</strong>
                <p>Listado, filtros y detalle de escuelas contratantes</p>
              </div>
              <span class="action-arrow">→</span>
            </router-link>

            <router-link to="/comercial/propietario/planes" class="action-card-item">
              <div class="action-icon action-icon-violet">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
              </div>
              <div class="action-text">
                <strong>Gestión de planes</strong>
                <p>Precios, periodicidad, límites y disponibilidad</p>
              </div>
              <span class="action-arrow">→</span>
            </router-link>

            <router-link to="/comercial/propietario/facturacion" class="action-card-item">
              <div class="action-icon action-icon-blue">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>
              </div>
              <div class="action-text">
                <strong>Transacciones y facturación</strong>
                <p>Historial de pagos, comprobantes y solicitudes</p>
              </div>
              <span class="action-arrow">→</span>
            </router-link>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { useIndicadoresComerciales } from '../composables/useIndicadoresComerciales';
import AppIcon from '../../../../components/AppIcon.vue';

const { indicadores, cargando, error, cargarIndicadores } = useIndicadoresComerciales();

function formatearMoneda(monto) {
  try {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(Number(monto) || 0);
  } catch (_) {
    return `${Number(monto || 0).toFixed(2)} MXN`;
  }
}

const tarjetasIndicadores = computed(() => [
  {
    clave: 'institucionesRegistradas',
    etiqueta: 'Instituciones Registradas',
    valor: cargando.value ? '—' : indicadores.value.institucionesRegistradas.toLocaleString('es-MX'),
    subtexto: 'Escuelas registradas en la plataforma',
    clase: 'stat-blue',
    icono: 'grid',
  },
  {
    clave: 'institucionesContratantes',
    etiqueta: 'Instituciones Contratantes',
    valor: cargando.value ? '—' : indicadores.value.institucionesContratantes.toLocaleString('es-MX'),
    subtexto: 'Con suscripción activa',
    clase: 'stat-success',
    icono: 'check-circle',
  },
  {
    clave: 'suscripcionesActivas',
    etiqueta: 'Suscripciones Activas',
    valor: cargando.value ? '—' : indicadores.value.suscripcionesActivas.toLocaleString('es-MX'),
    subtexto: 'Suscripciones en estado activo',
    clase: 'stat-success',
    icono: 'layers',
  },
  {
    clave: 'licenciasVigentes',
    etiqueta: 'Licencias Vigentes',
    valor: cargando.value ? '—' : indicadores.value.licenciasVigentes.toLocaleString('es-MX'),
    subtexto: 'Licencias vigentes emitidas',
    clase: 'stat-success',
    icono: 'shield',
  },
  {
    clave: 'ingresosRegistrados',
    etiqueta: 'Ingresos Registrados',
    valor: cargando.value ? '—' : formatearMoneda(indicadores.value.ingresosRegistrados),
    subtexto: 'Ingresos acumulados con planes comerciales',
    clase: 'stat-blue',
    icono: 'credits',
  },
  {
    clave: 'pagosPendientes',
    etiqueta: 'Pagos Pendientes',
    valor: cargando.value ? '—' : indicadores.value.pagosPendientes.toLocaleString('es-MX'),
    subtexto: 'Pagos pendientes de conciliación',
    clase: 'stat-warning',
    icono: 'clock',
  },
  {
    clave: 'contratosVencidos',
    etiqueta: 'Contratos Vencidos',
    valor: cargando.value ? '—' : indicadores.value.contratosVencidos.toLocaleString('es-MX'),
    subtexto: 'Contratos vencidos por renovación',
    clase: 'stat-warning',
    icono: 'alert',
  },
  {
    clave: 'renovacionesProximas',
    etiqueta: 'Renovaciones Próximas',
    valor: cargando.value ? '—' : indicadores.value.renovacionesProximas.toLocaleString('es-MX'),
    subtexto: 'Renovaciones dentro de los próximos 30 días',
    clase: 'stat-blue',
    icono: 'calendar',
  },
]);

onMounted(() => {
  cargarIndicadores();
});
</script>

<style scoped>
.page-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--text-main);
}

.page-subtitle {
  font-size: 0.875rem;
  color: var(--text-muted);
}

.header-actions {
  display: flex;
  gap: 0.65rem;
  flex-wrap: wrap;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 1.5rem;
}

.action-cards-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.action-card-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.9rem 1rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-card);
  text-decoration: none;
  transition: all 0.15s ease;
}

.action-card-item:hover {
  background: var(--bg-surface);
  border-color: var(--primary-border);
  transform: translateX(3px);
}

.action-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.action-icon-indigo { background: var(--primary-light); color: var(--primary); }
.action-icon-violet { background: var(--violet-light); color: var(--violet); }
.action-icon-blue { background: var(--blue-light); color: var(--blue); }

.action-text {
  flex: 1;
}

.action-text strong {
  display: block;
  font-size: 0.9rem;
  color: var(--text-main);
}

.action-text p {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.action-arrow {
  color: var(--text-light);
  font-weight: 700;
  font-size: 1.1rem;
}

.prioridad-lista {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.prioridad-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.85rem 1rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-card);
}

.prioridad-texto {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.prioridad-texto strong {
  font-size: 0.9rem;
  color: var(--text-main);
}

.prioridad-valor {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--danger);
  font-variant-numeric: tabular-nums;
}

@media (max-width: 640px) {
  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
