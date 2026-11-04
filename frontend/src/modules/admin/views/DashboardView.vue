<template>
  <div class="admin-dashboard">
    <!-- Header de Bienvenida y Estado -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Panel Institucional</h1>
        <p class="page-subtitle">Monitoreo general de matrículas, catálogos académicos y horarios</p>
      </div>
      <div class="header-actions">
        <button
          type="button"
          class="btn btn-secondary btn-sm"
          :disabled="cargando"
          @click="cargarEstadisticas"
        >
          <svg :class="{ spinner: cargando }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
          Actualizar métricas
        </button>
        <router-link to="/admin/asignaciones" class="btn btn-primary btn-sm">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          Motor de asignación
        </router-link>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="errorMsg" class="alert alert-danger" role="alert">
      {{ errorMsg }}
    </div>

    <!-- Estado de Publicación Oficial -->
    <div
      class="publication-banner card"
      :class="stats.publicacion_id ? 'pub-active' : 'pub-pending'"
    >
      <div class="pub-content">
        <div class="pub-icon">
          <svg v-if="stats.publicacion_id" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        </div>
        <div class="pub-text">
          <div class="pub-status-label">
            {{ stats.publicacion_id ? 'Publicación Vigente Activa' : 'Sin Horarios Oficiales Publicados' }}
          </div>
          <div class="pub-title">
            {{
              stats.publicacion_id
                ? `Los alumnos ya pueden consultar sus horarios oficiales (Ejecución #${stats.publicacion_id})`
                : 'Los alumnos aún recibirán un aviso indicando que los horarios se encuentran en preparación'
            }}
          </div>
        </div>
      </div>
      <div class="pub-actions">
        <router-link to="/admin/asignaciones" class="btn btn-sm" :class="stats.publicacion_id ? 'btn-secondary' : 'btn-primary'">
          {{ stats.publicacion_id ? 'Ver asignación publicada' : 'Generar asignaciones ahora' }}
        </router-link>
      </div>
    </div>

    <!-- KPI Metrics Grid -->
    <div class="stats-grid">
      <div class="stat-card stat-card-indigo">
        <div class="stat-header">
          <span class="stat-label">Alumnos Registrados</span>
          <div class="stat-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          </div>
        </div>
        <div class="stat-value">{{ cargando ? '—' : stats.alumnos }}</div>
        <div class="stat-subtext">Estudiantes con cuenta y membresía escolar</div>
      </div>

      <div class="stat-card stat-blue">
        <div class="stat-header">
          <span class="stat-label">Solicitudes de Materias</span>
          <div class="stat-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
          </div>
        </div>
        <div class="stat-value">{{ cargando ? '—' : stats.solicitudes }}</div>
        <div class="stat-subtext">Demandas registradas para el ciclo</div>
      </div>

      <div class="stat-card stat-warning">
        <div class="stat-header">
          <span class="stat-label">Grupos y Oferta</span>
          <div class="stat-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          </div>
        </div>
        <div class="stat-value">{{ cargando ? '—' : stats.grupos }}</div>
        <div class="stat-subtext">Grupos con cupos y horarios definidos</div>
      </div>

      <div class="stat-card stat-success">
        <div class="stat-header">
          <span class="stat-label">Materias y Planes</span>
          <div class="stat-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
          </div>
        </div>
        <div class="stat-value">{{ cargando ? '—' : `${stats.materias} / ${stats.planes}` }}</div>
        <div class="stat-subtext">{{ stats.materias }} materias en {{ stats.planes }} planes de estudio</div>
      </div>
    </div>

    <!-- Secciones Rápidas de Navegación -->
    <div class="dashboard-grid">
      <!-- Acciones Recomendadas -->
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
            Acciones Principales
          </h2>
        </div>
        <div class="card-body action-cards-list">
          <router-link to="/admin/asignaciones" class="action-card-item">
            <div class="action-icon action-icon-indigo">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            </div>
            <div class="action-text">
              <strong>Generar y Publicar Horarios</strong>
              <p>Ejecutar el algoritmo de asignación respetando prioridades, cupos y cruces</p>
            </div>
            <span class="action-arrow">→</span>
          </router-link>

          <router-link to="/admin/importar" class="action-card-item">
            <div class="action-icon action-icon-violet">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            </div>
            <div class="action-text">
              <strong>Importar Datos vía CSV</strong>
              <p>Carga masiva transaccional de planes, materias, alumnos, grupos y solicitudes</p>
            </div>
            <span class="action-arrow">→</span>
          </router-link>

          <router-link to="/admin/alumnos" class="action-card-item">
            <div class="action-icon action-icon-blue">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
            </div>
            <div class="action-text">
              <strong>Padrón de Alumnos</strong>
              <p>Consultar estudiantes, búsqueda por matrícula o nombre y estatus académico</p>
            </div>
            <span class="action-arrow">→</span>
          </router-link>
        </div>
      </div>

      <!-- Resumen Operativo -->
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            Flujo de Operación SaaS
          </h2>
        </div>
        <div class="card-body">
          <ol class="flow-steps">
            <li class="flow-step">
              <div class="step-num">1</div>
              <div class="step-desc">
                <strong>Catálogo e Inscripción</strong>
                <p>Importa o verifica planes de estudio, materias, grupos y solicitudes de los alumnos.</p>
              </div>
            </li>
            <li class="flow-step">
              <div class="step-num">2</div>
              <div class="step-desc">
                <strong>Generación en Borrador</strong>
                <p>El motor asigna solicitudes en orden de prioridad institucional, verificando cupos y choques.</p>
              </div>
            </li>
            <li class="flow-step">
              <div class="step-num">3</div>
              <div class="step-desc">
                <strong>Revisión y Exportación CSV</strong>
                <p>Analiza solicitudes asignadas vs pendientes y descarga la auditoría completa en CSV.</p>
              </div>
            </li>
            <li class="flow-step">
              <div class="step-num">4</div>
              <div class="step-desc">
                <strong>Publicación Oficial</strong>
                <p>Al publicar, los estudiantes verán inmediatamente su horario visual y asignación en su portal.</p>
              </div>
            </li>
          </ol>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api, { obtenerMensajeError } from '../../../api';

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
}

.publication-banner {
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.pub-active {
  background: linear-gradient(90deg, #f0fdf4 0%, #ecfdf5 100%);
  border-left: 4px solid var(--success);
}

.pub-pending {
  background: linear-gradient(90deg, #fffbeb 0%, #fef3c7 100%);
  border-left: 4px solid var(--warning);
}

.pub-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.pub-active .pub-icon {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: var(--success-bg);
  color: var(--success);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.pub-pending .pub-icon {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: var(--warning-bg);
  color: var(--warning);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.pub-status-label {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-muted);
}

.pub-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-main);
  margin-top: 0.2rem;
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

.flow-steps {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
}

.flow-step {
  display: flex;
  gap: 0.85rem;
}

.step-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--primary-light);
  color: var(--primary);
  font-size: 0.8125rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.step-desc strong {
  font-size: 0.875rem;
  color: var(--text-main);
  display: block;
}

.step-desc p {
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin-top: 0.15rem;
}
</style>
