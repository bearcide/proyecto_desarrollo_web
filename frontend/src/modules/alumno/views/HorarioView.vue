<template>
  <div class="alumno-horario-page">
    <!-- Bienvenida Personalizada -->
    <div class="welcome-banner card">
      <div class="welcome-content">
        <div class="welcome-avatar">
          {{ avatarIniciales }}
        </div>
        <div class="welcome-text">
          <span class="welcome-saludo">¡Hola, {{ authStore.alumno?.nombre || 'Estudiante' }}!</span>
          <h1 class="welcome-name">
            {{ authStore.nombreCompleto }}
          </h1>
          <div class="welcome-meta">
            <span class="meta-item">
              Matrícula: <strong class="font-mono">{{ authStore.matriculaOId }}</strong>
            </span>
            <span class="meta-item">
              Plan de Estudios: <strong>#{{ authStore.alumno?.plan_estudios || '1' }}</strong>
            </span>
            <span class="meta-item">
              Semestre: <strong>{{ authStore.alumno?.semestre ?? '—' }}</strong>
            </span>
          </div>
        </div>
      </div>

      <div class="welcome-badge-wrap">
        <span
          class="badge badge-lg"
          :class="hayPublicacion ? 'badge-success' : 'badge-warning'"
        >
          ● {{ hayPublicacion ? 'Horarios Oficiales Publicados' : 'Horarios en Proceso' }}
        </span>
      </div>
    </div>

    <!-- Error Alert Si Existe -->
    <div v-if="errorGenerico" class="alert alert-danger" role="alert">
      {{ errorGenerico }}
    </div>

    <!-- Estado de Carga -->
    <div v-if="cargando" class="empty-state">
      <div class="spinner spinner-primary" style="width: 2rem; height: 2rem; margin: 0 auto 1rem;"></div>
      <div class="empty-state-title">Consultando tus asignaciones oficiales…</div>
    </div>

    <!-- Caso 1: Horarios Aún No Publicados (404 del Backend) -->
    <div v-else-if="!hayPublicacion" class="card empty-publication-card">
      <div class="empty-pub-icon">
        <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
      </div>
      <h2 class="empty-pub-title">Horarios del periodo en proceso de asignación</h2>
      <p class="empty-pub-desc">
        La administración escolar aún no ha publicado los horarios oficiales definitivos para tu carrera.
        En cuanto la asignación sea confirmada, tus materias y cuadrícula semanal aparecerán automáticamente en esta pantalla.
      </p>

      <div class="notice-box">
        <div class="notice-item">
          <strong>Ventana de consulta:</strong>
          <span>{{ authStore.alumno?.ventana_texto || 'Pendiente de notificación oficial' }}</span>
        </div>
        <div class="notice-item">
          <strong>Materias solicitadas:</strong>
          <span>Tus solicitudes han sido registradas para el algoritmo determinista.</span>
        </div>
      </div>

      <div class="empty-pub-actions">
        <router-link to="/alumno/perfil" class="btn btn-secondary">
          Consultar mi perfil académico
        </router-link>
        <button
          type="button"
          class="btn btn-outline"
          @click="consultarHorario"
        >
          Reintentar consulta
        </button>
      </div>
    </div>

    <!-- Caso 2: Horarios Publicados Exitosamente -->
    <div v-else class="schedule-content-wrap">
      <!-- KPIs de la Carga Asignada -->
      <div class="stats-grid">
        <div class="stat-card stat-success">
          <div class="stat-header">
            <span class="stat-label">Materias Asignadas</span>
            <div class="stat-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            </div>
          </div>
          <div class="stat-value text-success">{{ materiasAsignadas.length }}</div>
          <div class="stat-subtext">Carga académica oficial confirmada</div>
        </div>

        <div class="stat-card stat-blue">
          <div class="stat-header">
            <span class="stat-label">Total de Créditos</span>
            <div class="stat-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
            </div>
          </div>
          <div class="stat-value text-blue">{{ totalCreditosAsignados }}</div>
          <div class="stat-subtext">Créditos curriculares en curso</div>
        </div>

        <div class="stat-card stat-warning" v-if="materiasPendientes.length > 0">
          <div class="stat-header">
            <span class="stat-label">Solicitudes No Asignadas</span>
            <div class="stat-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            </div>
          </div>
          <div class="stat-value text-warning">{{ materiasPendientes.length }}</div>
          <div class="stat-subtext">Por cupo o conflicto de horario</div>
        </div>

        <div class="stat-card stat-card-indigo">
          <div class="stat-header">
            <span class="stat-label">Estatus de Inscripción</span>
            <div class="stat-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            </div>
          </div>
          <div class="stat-value" style="font-size: 1.35rem; color: var(--primary);">
            OFICIAL
          </div>
          <div class="stat-subtext">Ejecución institucional #{{ ejecucionId }}</div>
        </div>
      </div>

      <!-- Cuadrícula Semanal Visual Reutilizable -->
      <div class="card visual-schedule-card">
        <div class="card-header">
          <h2 class="card-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
            Horario Semanal
          </h2>
          <span class="badge badge-success">
            {{ materiasAsignadas.length }} asignaturas con aula y horario
          </span>
        </div>

        <div class="card-body">
          <HorarioGrid :items="materiasAsignadas" />
        </div>
      </div>

      <!-- Detalle de Materias Asignadas -->
      <div class="card detailed-subjects-card">
        <div class="card-header">
          <h2 class="card-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/></svg>
            Detalle de Materias Asignadas
          </h2>
        </div>

        <div class="card-body">
          <div class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Clave</th>
                  <th>Materia</th>
                  <th>Grupo</th>
                  <th>Profesor</th>
                  <th>Horario Asignado</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in materiasAsignadas" :key="idx">
                  <td class="font-mono font-bold">{{ item.clave_materia }}</td>
                  <td>
                    <strong>{{ item.detalle?.nombre_materia || item.clave_materia }}</strong>
                  </td>
                  <td>
                    <span class="badge badge-indigo">
                      {{ item.detalle?.grupo || item.grupo || 'G1' }}
                    </span>
                  </td>
                  <td>{{ item.detalle?.profesor || 'Por asignar' }}</td>
                  <td>
                    <span class="font-mono text-sm">
                      {{ formatearHorarios(item.detalle?.horarios) }}
                    </span>
                  </td>
                  <td>
                    <span class="badge badge-success">ASIGNADA</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Detalle de Solicitudes Pendientes (Si hay alguna) -->
      <div v-if="materiasPendientes.length > 0" class="card pending-subjects-card">
        <div class="card-header">
          <h2 class="card-title text-warning">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            Solicitudes no asignadas en este ciclo ({{ materiasPendientes.length }})
          </h2>
        </div>

        <div class="card-body">
          <div class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Clave</th>
                  <th>Materia</th>
                  <th>Estado</th>
                  <th>Motivo Institucional</th>
                  <th>Explicación</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in materiasPendientes" :key="idx">
                  <td class="font-mono font-bold">{{ item.clave_materia }}</td>
                  <td>{{ item.detalle?.nombre_materia || item.clave_materia }}</td>
                  <td><span class="badge badge-warning">PENDIENTE</span></td>
                  <td><span class="badge badge-danger text-xs">{{ item.motivo }}</span></td>
                  <td class="text-sm text-muted">
                    {{ item.detalle?.explicacion || 'No fue posible asignar cupo en las opciones solicitadas.' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import api, { obtenerMensajeError } from '../../../api';
import { useAuthStore } from '../../../stores/auth';
import HorarioGrid from '../../../components/HorarioGrid.vue';

const authStore = useAuthStore();

const cargando = ref(false);
const hayPublicacion = ref(false);
const ejecucionId = ref(null);
const resultadosPropios = ref([]);
const errorGenerico = ref(null);

const avatarIniciales = computed(() => {
  const al = authStore.alumno;
  if (!al) return 'AL';
  const n = al.nombre ? al.nombre[0] : '';
  const p = al.apellido_paterno ? al.apellido_paterno[0] : '';
  return (n + p).toUpperCase() || 'AL';
});

const materiasAsignadas = computed(() => {
  return resultadosPropios.value.filter((r) => r.estado === 'ASIGNADA');
});

const materiasPendientes = computed(() => {
  return resultadosPropios.value.filter((r) => r.estado === 'PENDIENTE');
});

const totalCreditosAsignados = computed(() => {
  // En el esquema demo cada materia asignada otorga créditos (usualmente 6 créditos por materia)
  return materiasAsignadas.value.length * 6;
});

function minutosAHora(minutos) {
  const h = Math.floor(minutos / 60);
  const m = minutos % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

function formatearHorarios(horarios = []) {
  if (!horarios || !horarios.length) return '—';
  return horarios
    .map((h) => `${h.dia} ${minutosAHora(h.inicio)} - ${minutosAHora(h.fin)}`)
    .join(', ');
}

async function consultarHorario() {
  cargando.value = true;
  errorGenerico.value = null;

  try {
    const { data } = await api.get('/demo/horario/me/');
    hayPublicacion.value = true;
    ejecucionId.value = data.ejecucion;
    resultadosPropios.value = data.resultados || [];
  } catch (err) {
    if (err.response?.status === 404) {
      // 404 significa que todavía no hay publicación vigente
      hayPublicacion.value = false;
      resultadosPropios.value = [];
    } else {
      errorGenerico.value = obtenerMensajeError(err);
    }
  } finally {
    cargando.value = false;
  }
}

onMounted(() => {
  consultarHorario();
});
</script>

<style scoped>
.alumno-horario-page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* Banner de Bienvenida */
.welcome-banner {
  padding: 1.5rem 1.75rem;
  background: linear-gradient(135deg, #ffffff 0%, var(--primary-light) 100%);
  border: 1px solid var(--primary-border);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1.25rem;
}

.welcome-content {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.welcome-avatar {
  width: 58px;
  height: 58px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--primary) 0%, var(--violet) 100%);
  color: #ffffff;
  font-size: 1.35rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
  flex-shrink: 0;
}

.welcome-saludo {
  font-size: 0.8125rem;
  color: var(--primary);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.welcome-name {
  font-size: 1.45rem;
  font-weight: 800;
  color: var(--text-main);
  margin: 0.15rem 0 0.35rem;
}

.welcome-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.85rem;
  font-size: 0.825rem;
  color: var(--text-muted);
}

.meta-item strong {
  color: var(--text-main);
}

.badge-lg {
  padding: 0.45rem 0.95rem;
  font-size: 0.85rem;
}

/* Estado sin publicación */
.empty-publication-card {
  padding: 3.5rem 2rem;
  text-align: center;
}

.empty-pub-icon {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--warning-bg);
  color: var(--warning);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.25rem;
}

.empty-pub-title {
  font-size: 1.35rem;
  font-weight: 800;
  color: var(--text-main);
  margin-bottom: 0.5rem;
}

.empty-pub-desc {
  max-width: 540px;
  margin: 0 auto 1.5rem;
  color: var(--text-muted);
  font-size: 0.95rem;
  line-height: 1.55;
}

.notice-box {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  max-width: 500px;
  margin: 0 auto 1.75rem;
  padding: 1rem 1.25rem;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  font-size: 0.85rem;
}

.notice-item strong {
  display: block;
  color: var(--text-main);
}

.notice-item span {
  color: var(--text-muted);
}

.empty-pub-actions {
  display: flex;
  justify-content: center;
  gap: 0.85rem;
}

/* Horario publicado */
.schedule-content-wrap {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.visual-schedule-card, .detailed-subjects-card, .pending-subjects-card {
  overflow: hidden;
}

.font-mono {
  font-family: 'JetBrains Mono', monospace;
}

.font-bold {
  font-weight: 700;
}

.text-xs {
  font-size: 0.75rem;
}

.text-sm {
  font-size: 0.875rem;
}

.text-success {
  color: var(--success);
}

.text-warning {
  color: var(--warning);
}

.text-blue {
  color: var(--blue);
}

.text-muted {
  color: var(--text-muted);
}
</style>
