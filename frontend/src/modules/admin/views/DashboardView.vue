<template>
  <div class="admin-dashboard admin-view">
    <header class="ui-page-header">
      <div>
        <h1 class="ui-large-title">Panel institucional</h1>
        <p class="ui-page-subtitle">Resumen de alumnos, catálogos académicos y horarios de tu escuela</p>
      </div>
      <div class="ui-page-actions">
        <button type="button" class="btn btn-secondary btn-sm" :disabled="cargando" @click="cargarEstadisticas">
          <AppIcon name="refresh" :size="14" :class="{ girando: cargando }" />
          Actualizar métricas
        </button>
        <router-link to="/admin/asignaciones" class="btn btn-primary btn-sm">
          <AppIcon name="zap" :size="14" />
          Motor de asignación
        </router-link>
      </div>
    </header>

    <ErrorBanner
      v-if="errorMsg"
      titulo="No pudimos cargar las métricas"
      :mensaje="errorMsg"
      :cargando="cargando"
      @reintentar="cargarEstadisticas"
    />

    <!-- Estado de publicación -->
    <section class="publication-banner" :class="stats.publicacion_id ? 'pub-active' : 'pub-pending'">
      <div class="pub-icon">
        <AppIcon :name="stats.publicacion_id ? 'check-circle' : 'alert'" :size="22" />
      </div>
      <div class="pub-text">
        <div class="pub-status-label">
          {{ stats.publicacion_id ? 'Publicación vigente' : 'Sin horarios oficiales publicados' }}
        </div>
        <div class="pub-title">
          {{
            stats.publicacion_id
              ? `Los alumnos ya pueden consultar sus horarios oficiales (ejecución #${stats.publicacion_id}).`
              : 'Los alumnos verán un aviso de que sus horarios están en preparación.'
          }}
        </div>
      </div>
      <router-link
        to="/admin/asignaciones"
        class="btn btn-sm"
        :class="stats.publicacion_id ? 'btn-secondary' : 'btn-primary'"
      >
        {{ stats.publicacion_id ? 'Ver asignación publicada' : 'Generar asignaciones' }}
      </router-link>
    </section>

    <!-- Métricas con vidrio (D1) -->
    <div class="stats-grid" :aria-busy="cargando ? 'true' : 'false'">
      <div class="stat-card glass-card">
        <div class="stat-header">
          <span class="stat-label">Alumnos registrados</span>
          <div class="stat-icon"><AppIcon name="users" :size="18" /></div>
        </div>
        <div v-if="cargando" class="skeleton skel-value"></div>
        <div v-else class="stat-value ui-num">{{ stats.alumnos }}</div>
        <div class="stat-subtext">Con cuenta y membresía escolar</div>
      </div>

      <div class="stat-card glass-card stat-blue">
        <div class="stat-header">
          <span class="stat-label">Solicitudes de materias</span>
          <div class="stat-icon"><AppIcon name="file-text" :size="18" /></div>
        </div>
        <div v-if="cargando" class="skeleton skel-value"></div>
        <div v-else class="stat-value ui-num">{{ stats.solicitudes }}</div>
        <div class="stat-subtext">Registradas para el ciclo</div>
      </div>

      <div class="stat-card glass-card stat-warning">
        <div class="stat-header">
          <span class="stat-label">Grupos ofertados</span>
          <div class="stat-icon"><AppIcon name="calendar" :size="18" /></div>
        </div>
        <div v-if="cargando" class="skeleton skel-value"></div>
        <div v-else class="stat-value ui-num">{{ stats.grupos }}</div>
        <div class="stat-subtext">Con cupo y horario definidos</div>
      </div>

      <!-- D2: número principal claro y detalle debajo -->
      <div class="stat-card glass-card stat-success">
        <div class="stat-header">
          <span class="stat-label">Materias</span>
          <div class="stat-icon"><AppIcon name="book-open" :size="18" /></div>
        </div>
        <div v-if="cargando" class="skeleton skel-value"></div>
        <div v-else class="stat-value ui-num">{{ stats.materias }}</div>
        <div class="stat-subtext">
          En {{ stats.planes }} {{ stats.planes === 1 ? 'plan de estudios' : 'planes de estudio' }}
        </div>
      </div>
    </div>

    <div class="dashboard-grid">
      <!-- Acciones principales como lista agrupada (D3) -->
      <section>
        <h2 class="ui-section-title">Acciones principales</h2>
        <nav class="ui-grouped" aria-label="Acciones principales">
          <router-link to="/admin/asignaciones" class="ui-row ui-row-link action-row">
            <span class="ui-row-icon tint-indigo"><AppIcon name="zap" :size="17" /></span>
            <div class="ui-row-main">
              <div class="ui-row-title">Generar y publicar horarios</div>
              <div class="ui-row-subtitle">Asigna las solicitudes respetando prioridades, cupos y cruces</div>
            </div>
            <AppIcon name="chevron-right" :size="18" class="ui-row-chevron" />
          </router-link>

          <router-link to="/admin/importar" class="ui-row ui-row-link action-row">
            <span class="ui-row-icon tint-violet"><AppIcon name="upload" :size="17" /></span>
            <div class="ui-row-main">
              <div class="ui-row-title">Importar datos con CSV</div>
              <div class="ui-row-subtitle">Carga planes, materias, alumnos, grupos y solicitudes</div>
            </div>
            <AppIcon name="chevron-right" :size="18" class="ui-row-chevron" />
          </router-link>

          <router-link to="/admin/alumnos" class="ui-row ui-row-link action-row">
            <span class="ui-row-icon tint-blue"><AppIcon name="users" :size="17" /></span>
            <div class="ui-row-main">
              <div class="ui-row-title">Padrón de alumnos</div>
              <div class="ui-row-subtitle">Busca por matrícula o nombre y consulta su ficha</div>
            </div>
            <AppIcon name="chevron-right" :size="18" class="ui-row-chevron" />
          </router-link>
        </nav>
      </section>

      <!-- Flujo de operación -->
      <section>
        <h2 class="ui-section-title">Flujo de operación</h2>
        <div class="ui-grouped flow-card">
          <ol class="flow-steps">
            <li class="flow-step">
              <span class="step-num">1</span>
              <div>
                <strong>Catálogo e inscripción</strong>
                <p>Importa o verifica planes de estudio, materias, grupos y solicitudes de los alumnos.</p>
              </div>
            </li>
            <li class="flow-step">
              <span class="step-num">2</span>
              <div>
                <strong>Generación en borrador</strong>
                <p>El motor asigna las solicitudes por prioridad institucional, revisando cupos y cruces.</p>
              </div>
            </li>
            <li class="flow-step">
              <span class="step-num">3</span>
              <div>
                <strong>Revisión y exportación CSV</strong>
                <p>Compara solicitudes asignadas y pendientes, y descarga el reporte completo.</p>
              </div>
            </li>
            <li class="flow-step">
              <span class="step-num">4</span>
              <div>
                <strong>Publicación oficial</strong>
                <p>Al publicar, cada alumno ve de inmediato su horario en su portal.</p>
              </div>
            </li>
          </ol>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api, { obtenerMensajeError } from '../../../api';
import AppIcon from '../../../components/AppIcon.vue';
import ErrorBanner from '../../../components/ErrorBanner.vue';

const stats = ref({
  alumnos: 0,
  planes: 0,
  materias: 0,
  grupos: 0,
  solicitudes: 0,
  ejecuciones: 0,
  publicacion_id: null,
});

const cargando = ref(false);
const errorMsg = ref(null);

async function cargarEstadisticas() {
  cargando.value = true;
  errorMsg.value = null;
  try {
    const { data } = await api.get('/demo/estadisticas/');
    stats.value = data;
  } catch (err) {
    errorMsg.value = obtenerMensajeError(err);
  } finally {
    cargando.value = false;
  }
}

onMounted(cargarEstadisticas);
</script>

<style scoped>
.admin-dashboard {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.admin-dashboard > .ui-page-header {
  margin-bottom: 0.25rem;
}

/* Estado de publicación */
.publication-banner {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.25rem;
  border-radius: 14px;
  border: 1px solid;
}

.pub-active {
  background-color: var(--success-bg);
  border-color: var(--success-border);
}

.pub-pending {
  background-color: var(--warning-bg);
  border-color: var(--warning-border);
}

.pub-icon {
  flex-shrink: 0;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-card);
}

.pub-active .pub-icon { color: var(--success); }
.pub-pending .pub-icon { color: var(--warning); }

.pub-text {
  flex: 1;
  min-width: 0;
}

.pub-status-label {
  font-size: 0.8125rem;
  font-weight: 700;
}

.pub-active .pub-status-label { color: var(--success-text); }
.pub-pending .pub-status-label { color: var(--warning-text); }

.pub-title {
  margin-top: 0.1rem;
  font-size: 0.9375rem;
  color: var(--text-main);
}

/* Métricas */
.stats-grid {
  margin-bottom: 0;
}

.stat-value {
  font-variant-numeric: tabular-nums;
}

.skel-value {
  height: 2.1rem;
  width: 45%;
  margin: 0.1rem 0 0.2rem;
}

/* Secciones inferiores */
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.5rem;
  align-items: start;
}

.action-row {
  --ui-separator-inset: 3.55rem;
  min-height: 64px;
}

.tint-indigo { background-color: var(--primary-light); color: var(--accent-text); }
.tint-violet { background-color: var(--violet-light); color: var(--violet); }
.tint-blue { background-color: var(--blue-light); color: var(--blue); }

/* Flujo */
.flow-card {
  padding: 1rem 1.1rem;
}

.flow-steps {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.flow-step {
  display: flex;
  align-items: flex-start;
  gap: 0.8rem;
}

.step-num {
  flex-shrink: 0;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--primary-light);
  color: var(--accent-text);
  font-size: 0.8125rem;
  font-weight: 700;
}

.flow-step strong {
  display: block;
  font-size: 0.9375rem;
  color: var(--text-main);
}

.flow-step p {
  margin-top: 0.1rem;
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.girando {
  animation: spin 0.8s linear infinite;
}

@media (max-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
</style>
