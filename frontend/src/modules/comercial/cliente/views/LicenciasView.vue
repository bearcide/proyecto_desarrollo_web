<template>
  <div class="licencias-page">
    <div class="page-header">
      <div>
        <div class="header-pretitle">
          <AppIcon name="shield" size="16" class="text-primary" />
          <span>Gestión de Activos y Licenciamiento Institucional</span>
        </div>
        <h1 class="page-title">Licencias de Software y Contratos</h1>
        <p class="page-subtitle">
          Supervisa las licencias institucionales perpetuas y temporales, pólizas de mantenimiento y contratos formalizados.
        </p>
      </div>

      <div class="header-actions">
        <router-link to="/admin/comercial/configurador?modalidad=institutional" class="btn btn-primary btn-sm">
          <AppIcon name="shield" size="14" />
          <span>Adquirir Nueva Licencia</span>
        </router-link>
        <button
          type="button"
          class="btn btn-secondary btn-sm"
          :disabled="cargando"
          @click="cargarDatos"
        >
          <AppIcon name="refresh" size="14" :class="{ spinner: cargando }" />
          <span>Actualizar</span>
        </button>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="error" class="alert alert-danger" role="alert">
      <AppIcon name="alert" size="18" />
      <span>{{ error }}</span>
    </div>

    <!-- Carga inicial -->
    <div v-if="cargando && !licencias.length" class="empty-state">
      <div class="spinner spinner-primary" style="margin: 0 auto 0.75rem;"></div>
      <span class="text-muted">Consultando registro de licencias institucionales…</span>
    </div>

    <div v-else class="licencias-layout">
      <!-- Grid de Licencias Activas -->
      <section class="licencias-section">
        <h2 class="section-title">Licencias Institucionales Registradas</h2>

        <div v-if="!licencias.length" class="empty-state card">
          <AppIcon name="shield" size="36" class="text-muted" />
          <h3 class="text-base font-bold text-main" style="margin-top: 0.75rem;">No hay licencias registradas</h3>
          <p class="text-muted text-sm" style="margin: 0.25rem 0 1rem;">
            Tu institución aún no cuenta con licencias institucionales o perpetuas adquiridas.
          </p>
          <router-link to="/admin/comercial/planes" class="btn btn-primary btn-sm">
            Ver Planes y Licencias
          </router-link>
        </div>

        <div v-else class="licencias-cards-grid">
          <div
            v-for="lic in licencias"
            :key="lic.id"
            class="card licencia-card"
            :class="{ 'perpetual-border': !lic.fin }"
          >
            <div class="licencia-header">
              <div class="licencia-type-badge">
                <AppIcon :name="!lic.fin ? 'award' : 'shield'" size="18" />
                <span>{{ !lic.fin ? 'Licencia Perpetua Vitalicia' : (lic.es_mantenimiento ? 'Póliza de Mantenimiento' : 'Licencia Institucional') }}</span>
              </div>
              <EstadoPagoBadge :estado="lic.estado" />
            </div>

            <div class="licencia-key-box">
              <span class="key-label">Identificador de Licencia (UUID)</span>
              <code class="key-code">{{ lic.id }}</code>
            </div>

            <div class="licencia-dates-grid">
              <div class="date-item">
                <span class="label">Fecha de Emisión:</span>
                <span class="val">{{ formatearFecha(lic.inicio) }}</span>
              </div>
              <div class="date-item">
                <span class="label">Término de Vigencia:</span>
                <span class="val font-bold" :class="!lic.fin ? 'text-success' : ''">
                  {{ lic.fin ? formatearFecha(lic.fin) : 'VITALICIA (Sin expiración)' }}
                </span>
              </div>
            </div>

            <div class="licencia-limits-box">
              <div class="limit-pill">
                <AppIcon name="user" size="14" />
                <span>Capacidad: {{ lic.max_alumnos?.toLocaleString() ?? '—' }} alumnos</span>
              </div>
              <div class="limit-pill">
                <AppIcon name="building" size="14" />
                <span>Sedes: {{ lic.max_planteles ?? '—' }} campus</span>
              </div>
            </div>

            <div class="licencia-features">
              <span class="features-label">Módulos Concedidos:</span>
              <ul class="features-sublist">
                <li v-for="(f, idx) in obtenerFuncionalidades(lic)" :key="idx">
                  <AppIcon name="check" size="14" class="text-success" />
                  <span>{{ f }}</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <!-- Sección de Contratos Formalizados -->
      <section class="contratos-section">
        <div class="section-heading-row">
          <div>
            <h2 class="section-title">Contratos Empresariales Formalizados</h2>
            <p class="section-desc">Convenios negociados directamente con la administración de la plataforma.</p>
          </div>
          <router-link to="/admin/comercial/configurador?modalidad=enterprise" class="btn btn-secondary btn-sm">
            <span>Cotizar Convenio</span>
          </router-link>
        </div>

        <div v-if="!contratos.length" class="card empty-contratos">
          <AppIcon name="file-text" size="28" class="text-muted" />
          <div class="empty-contratos-text">
            <strong>Sin contratos personalizados vigentes</strong>
            <p class="text-sm text-muted" style="margin: 0.15rem 0 0;">
              Tu institución opera bajo los términos estándar del catálogo comercial SaaS.
            </p>
          </div>
        </div>

        <div v-else class="table-responsive card">
          <table class="table">
            <thead>
              <tr>
                <th>Folio Contrato</th>
                <th>Fecha Inicio</th>
                <th>Fecha Término</th>
                <th>Condiciones</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in contratos" :key="c.id">
                <td><code>{{ c.id.substring(0, 8) }}…</code></td>
                <td>{{ formatearFecha(c.inicio) }}</td>
                <td>{{ formatearFecha(c.fin) }}</td>
                <td>{{ c.condiciones || 'Convenio institucional multi-sede' }}</td>
                <td><EstadoPagoBadge :estado="c.estado" /></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import AppIcon from '../../../../components/AppIcon.vue';
import EstadoPagoBadge from '../components/EstadoPagoBadge.vue';
import { useComercial } from '../composables/useComercial';

const { cargando, error, licencias, contratos, cargarEstadoInstitucion } = useComercial();

onMounted(async () => {
  await cargarDatos();
});

async function cargarDatos() {
  await cargarEstadoInstitucion();
}

function formatearFecha(isoString) {
  if (!isoString) return 'Sin fecha';
  try {
    const d = new Date(isoString);
    return new Intl.DateTimeFormat('es-MX', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    }).format(d);
  } catch {
    return isoString;
  }
}

function obtenerFuncionalidades(lic) {
  if (Array.isArray(lic.funcionalidades)) return lic.funcionalidades;
  return Object.entries(lic.funcionalidades ?? {})
    .filter(([, habilitada]) => habilitada)
    .map(([modulo]) => modulo.replaceAll('_', ' '));
}
</script>

<style scoped>
.licencias-page {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem 1rem 3rem;
}

.header-pretitle {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--primary);
  margin-bottom: 0.35rem;
}

.licencias-layout {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--text-main);
  margin: 0 0 1rem;
}

.section-desc {
  font-size: 0.84rem;
  color: var(--text-muted);
  margin: 0.2rem 0 0;
}

.section-heading-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.licencias-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 1.5rem;
}

.licencia-card {
  padding: 1.5rem;
  border-radius: var(--radius-lg);
  background: var(--bg-card);
  border: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.perpetual-border {
  border-color: var(--violet);
  box-shadow: 0 0 0 1px var(--violet-border);
}

.licencia-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.licencia-type-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-weight: 800;
  font-size: 0.88rem;
  color: var(--primary);
}

.licencia-key-box {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 0.65rem 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.key-label {
  font-size: 0.7rem;
  text-transform: uppercase;
  color: var(--text-light);
  font-weight: 700;
}

.key-code {
  font-size: 0.82rem;
  color: var(--text-main);
  word-break: break-all;
}

.licencia-dates-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  font-size: 0.84rem;
}

.date-item {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.date-item .label {
  font-size: 0.72rem;
  color: var(--text-light);
  text-transform: uppercase;
  font-weight: 700;
}

.date-item .val {
  color: var(--text-main);
}

.licencia-limits-box {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.limit-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--bg-surface);
  border-radius: var(--radius-full);
  padding: 0.35rem 0.75rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-muted);
}

.licencia-features {
  border-top: 1px solid var(--border-subtle);
  padding-top: 0.75rem;
}

.features-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-light);
  margin-bottom: 0.45rem;
}

.features-sublist {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.82rem;
  color: var(--text-main);
}

.features-sublist li {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.empty-contratos {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem 1.5rem;
  border-radius: var(--radius-md);
}
</style>
