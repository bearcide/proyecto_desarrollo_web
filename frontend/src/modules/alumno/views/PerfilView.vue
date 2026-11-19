<template>
  <div class="alumno-perfil-page">
    <header class="ui-page-header">
      <div>
        <h1 class="ui-large-title">Mi perfil y plan académico</h1>
        <p class="ui-page-subtitle">Información curricular, historial de acreditación y estatus de inscripción</p>
      </div>
      <div class="ui-page-actions">
        <button
          type="button"
          class="btn btn-secondary btn-sm"
          :disabled="cargando"
          @click="cargarDatos"
        >
          <AppIcon name="refresh" :size="14" :class="{ girando: cargando }" />
          Actualizar datos
        </button>
      </div>
    </header>

    <ErrorBanner
      v-if="errorMsg"
      titulo="No pudimos cargar tu perfil"
      :mensaje="errorMsg"
      :cargando="cargando"
      @reintentar="cargarDatos"
    />

    <!-- Carga: esqueleto (A9) -->
    <div v-if="cargando && !alumno" class="perfil-layout" aria-busy="true" aria-label="Cargando perfil">
      <div class="perfil-col-left">
        <div class="card identity-card">
          <div class="skeleton skel-avatar"></div>
          <div class="skeleton ui-skel-title" style="margin-inline: auto"></div>
          <div class="skeleton ui-skel-line" style="width: 40%; margin-inline: auto"></div>
        </div>
      </div>
      <div class="perfil-col-right">
        <div class="stats-grid">
          <div v-for="n in 4" :key="n" class="stat-card"><div class="skeleton" style="height: 88px"></div></div>
        </div>
      </div>
    </div>

    <div v-else-if="alumno" class="perfil-layout">
      <!-- Columna izquierda: identidad y ventana de inscripción -->
      <div class="perfil-col-left">
        <!-- Tarjeta de identidad sin banner (C1) -->
        <section class="card identity-card">
          <div class="identity-avatar-lg" aria-hidden="true">{{ avatarIniciales }}</div>
          <h2 class="identity-name">
            {{ alumno.nombre }} {{ alumno.apellido_paterno }} {{ alumno.apellido_materno }}
          </h2>
          <div class="identity-matricula ui-num">Matrícula {{ alumno.numero_de_cuenta }}</div>

          <div class="identity-tags">
            <span class="badge badge-indigo">
              {{ nombrePlan || `Plan #${alumno.plan_estudios}` }}
            </span>
          </div>

          <!-- Datos como lista agrupada (C5) -->
          <div class="ui-grouped identity-list">
            <div class="ui-row">
              <span class="ui-row-label">Institución</span>
              <span class="ui-row-value">{{ authStore.nombreEscuela }}</span>
            </div>
            <div class="ui-row">
              <span class="ui-row-label">Semestre actual</span>
              <span class="ui-row-value">{{ alumno.semestre }}</span>
            </div>
            <div class="ui-row">
              <span class="ui-row-label">Turno / asignación</span>
              <span class="ui-row-value">{{ alumno.numero_inscripcion || 'General' }}</span>
            </div>
          </div>
        </section>

        <!-- Ventana de inscripción -->
        <section class="card window-card">
          <div class="card-header">
            <h3 class="card-title">
              <AppIcon name="calendar" />
              Ventana de inscripción
            </h3>
          </div>
          <div class="card-body">
            <div class="window-status">
              <div class="window-icon"><AppIcon name="clock" :size="22" /></div>
              <div class="window-info">
                <strong>Horario asignado para trámites</strong>
                <p>
                  {{ alumno.ventana_texto || 'Tu ventana se activa de acuerdo al promedio acumulado e indicador escolar.' }}
                </p>
                <div v-if="alumno.ventana_inicio" class="window-date ui-num">
                  Apertura: {{ formatearFecha(alumno.ventana_inicio) }}
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- Columna derecha: métricas e historial -->
      <div class="perfil-col-right">
        <!-- Métricas con efecto vidrio y brillo (C3) -->
        <div class="stats-grid">
          <div class="stat-card glass-card stat-success">
            <div class="stat-header">
              <span class="stat-label">Promedio acumulado</span>
              <div class="stat-icon"><AppIcon name="shield" /></div>
            </div>
            <div class="stat-value text-success ui-num">
              {{ Number(alumno.promedio_acumulado).toFixed(2) }}
            </div>
            <div class="stat-subtext">Escala oficial de 0 a 10</div>
          </div>

          <div class="stat-card glass-card stat-blue">
            <div class="stat-header">
              <span class="stat-label">Indicador escolar</span>
              <div class="stat-icon">
                <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
              </div>
            </div>
            <div class="stat-value text-blue ui-num">
              {{ Number(alumno.indicador_escolar).toFixed(2) }}
            </div>
            <div class="stat-subtext">Cálculo de avance institucional</div>
          </div>

          <div class="stat-card glass-card">
            <div class="stat-header">
              <span class="stat-label">Créditos acumulados</span>
              <div class="stat-icon"><AppIcon name="credits" /></div>
            </div>
            <div class="stat-value ui-num">{{ alumno.creditos }}</div>
            <div class="stat-subtext">Créditos aprobados en el plan</div>
          </div>

          <div class="stat-card glass-card stat-warning">
            <div class="stat-header">
              <span class="stat-label">Materias cursadas</span>
              <div class="stat-icon"><AppIcon name="book" /></div>
            </div>
            <div class="stat-value ui-num">{{ alumno.materias_cursadas }}</div>
            <div class="stat-subtext">{{ alumno.materias_pasadas }} materias pasadas</div>
          </div>
        </div>

        <!-- Materias acreditadas como lista agrupada (C6) -->
        <section>
          <h2 class="ui-section-title">
            <span>
              Materias acreditadas
              <span class="ui-section-count">{{ materiasAprobadasDetalle.length }}</span>
            </span>
            <span class="badge badge-success">Prerrequisitos desbloqueados</span>
          </h2>

          <div class="ui-grouped">
            <div v-if="materiasAprobadasDetalle.length === 0" class="ui-empty">
              <div class="ui-empty-icon"><AppIcon name="book" :size="24" /></div>
              <p class="ui-empty-text">Aún no cuentas con materias acreditadas en este plan de estudios.</p>
            </div>

            <template v-else>
            <div
              v-for="mat in materiasAprobadasDetalle"
              :key="mat.id"
              class="ui-row aprobada-row"
            >
              <span class="aprobada-check"><AppIcon name="check" :size="14" :stroke-width="3" /></span>
              <div class="ui-row-main">
                <div class="ui-row-title">{{ mat.nombre }}</div>
                <div class="ui-row-subtitle">
                  <span class="ui-code">{{ mat.clave }}</span> · Semestre {{ mat.semestre }}
                </div>
              </div>
              <span class="ui-row-value">{{ mat.creditos }} créditos</span>
            </div>
            </template>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import api, { obtenerMensajeError } from '../../../api';
import { useAuthStore } from '../../../stores/auth';
import AppIcon from '../../../components/AppIcon.vue';
import ErrorBanner from '../../../components/ErrorBanner.vue';

const authStore = useAuthStore();

const alumno = ref(null);
const planes = ref([]);
const nodos = ref([]);
const cargando = ref(false);
const errorMsg = ref(null);

const avatarIniciales = computed(() => {
  const al = alumno.value;
  if (!al) return 'AL';
  const n = al.nombre ? al.nombre[0] : '';
  const p = al.apellido_paterno ? al.apellido_paterno[0] : '';
  return (n + p).toUpperCase() || 'AL';
});

const nombrePlan = computed(() => {
  if (!alumno.value) return '';
  const p = planes.value.find((x) => x.id === alumno.value.plan_estudios);
  return p ? p.nombre : '';
});

const materiasAprobadasDetalle = computed(() => {
  if (!alumno.value || !alumno.value.materias_aprobadas_ids) return [];
  const aprobadasSet = new Set(alumno.value.materias_aprobadas_ids);

  return nodos.value
    .filter((n) => aprobadasSet.has(n.id))
    .map((n) => ({
      id: n.id,
      clave: n.clave,
      nombre: n.nombre,
      semestre: n.semestre,
      creditos: n.creditos,
    }));
});

function formatearFecha(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });
}

async function cargarDatos() {
  cargando.value = true;
  errorMsg.value = null;

  try {
    const [respAlumno, respPlanes, respNodos] = await Promise.all([
      api.get('/alumnos/me/'),
      api.get('/planes-estudios/'),
      api.get('/nodos/'),
    ]);

    alumno.value = respAlumno.data;
    authStore.alumno = respAlumno.data;
    localStorage.setItem('ime_alumno', JSON.stringify(respAlumno.data));

    planes.value = Array.isArray(respPlanes.data) ? respPlanes.data : (respPlanes.data?.results || []);
    nodos.value = Array.isArray(respNodos.data) ? respNodos.data : (respNodos.data?.results || []);
  } catch (err) {
    errorMsg.value = obtenerMensajeError(err);
  } finally {
    cargando.value = false;
  }
}

onMounted(cargarDatos);
</script>

<style scoped>
.perfil-layout {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 1.5rem;
  align-items: start;
}

.perfil-col-left,
.perfil-col-right {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  min-width: 0;
}

/* Identidad: avatar centrado, sin banner (C1) */
.identity-card {
  padding: 1.75rem 1.25rem 1.25rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.identity-avatar-lg {
  width: 84px;
  height: 84px;
  border-radius: 50%;
  background-color: var(--accent);
  color: var(--on-accent);
  font-size: 1.75rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 0 4px var(--primary-light);
  margin-bottom: 0.9rem;
}

.skel-avatar {
  width: 84px;
  height: 84px;
  border-radius: 50%;
  margin-bottom: 0.9rem;
}

.identity-name {
  font-size: 1.375rem; /* 22px · Title 2 */
  font-weight: 700;
  line-height: 1.25;
  color: var(--text-main);
}

.identity-matricula {
  margin-top: 0.25rem;
  font-size: 0.9375rem;
  color: var(--text-muted);
}

.identity-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.5rem;
  margin: 0.9rem 0 1.25rem;
}

.identity-list {
  width: 100%;
  text-align: left;
  background-color: var(--bg-surface);
  border-color: transparent;
}

/* Ventana de inscripción */
.window-status {
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
}

.window-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--primary-light);
  color: var(--accent-text);
}

.window-info strong {
  display: block;
  font-size: 0.9375rem;
  color: var(--text-main);
}

.window-info p {
  margin-top: 0.2rem;
  font-size: 0.875rem;
  color: var(--text-muted);
}

.window-date {
  margin-top: 0.5rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--accent-text);
}

/* Métricas */
.stats-grid {
  margin-bottom: 0;
}

.stat-value {
  font-variant-numeric: tabular-nums;
}

.text-success { color: var(--success); }
.text-blue { color: var(--blue); }

/* Materias acreditadas */
.aprobada-row {
  --ui-separator-inset: 3.2rem;
}

.aprobada-check {
  flex-shrink: 0;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--success);
  color: #ffffff;
}

:root[data-theme="dark"] .aprobada-check {
  background-color: #059669;
}

.girando {
  animation: spin 0.8s linear infinite;
}

@media (max-width: 1024px) {
  .perfil-layout {
    grid-template-columns: 1fr;
  }
}
</style>
