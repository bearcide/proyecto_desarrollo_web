<template>
  <div class="alumno-perfil-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Mi Perfil y Plan Académico</h1>
        <p class="page-subtitle">Información curricular, historial de acreditación y estatus de inscripción</p>
      </div>
      <div class="header-actions">
        <button
          type="button"
          class="btn btn-secondary btn-sm"
          :disabled="cargando"
          @click="cargarDatos"
        >
          <svg :class="{ spinner: cargando }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
          Actualizar datos
        </button>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="errorMsg" class="alert alert-danger" role="alert">
      {{ errorMsg }}
    </div>

    <div v-if="cargando && !alumno" class="empty-state">
      <div class="spinner spinner-primary" style="margin: 0 auto 0.5rem;"></div>
      <span class="text-muted">Cargando expediente escolar…</span>
    </div>

    <div v-else-if="alumno" class="perfil-layout">
      <!-- Columna Izquierda: Tarjeta de Identidad y Ventana de Inscripción -->
      <div class="perfil-col-left">
        <!-- Tarjeta de Identidad -->
        <div class="card identity-card">
          <div class="identity-banner"></div>
          <div class="identity-body">
            <div class="identity-avatar-lg">
              {{ avatarIniciales }}
            </div>
            <h2 class="identity-name">
              {{ alumno.nombre }} {{ alumno.apellido_paterno }} {{ alumno.apellido_materno }}
            </h2>
            <div class="identity-matricula font-mono">
              Matrícula: {{ alumno.numero_de_cuenta }}
            </div>

            <div class="identity-tags">
              <span class="badge badge-indigo">
                {{ nombrePlan || `Plan #${alumno.plan_estudios}` }}
              </span>
              <span class="badge badge-success">
                Alumno Regular
              </span>
            </div>

            <div class="identity-meta-list">
              <div class="id-meta-item">
                <span class="id-meta-label">Institución</span>
                <strong class="id-meta-val">{{ authStore.nombreEscuela }}</strong>
              </div>
              <div class="id-meta-item">
                <span class="id-meta-label">Semestre Actual</span>
                <strong class="id-meta-val font-mono">Semestre {{ alumno.semestre }}</strong>
              </div>
              <div class="id-meta-item">
                <span class="id-meta-label">Turno / Asignación</span>
                <strong class="id-meta-val font-mono">{{ alumno.numero_inscripcion || 'General' }}</strong>
              </div>
            </div>
          </div>
        </div>

        <!-- Ventana de Inscripción Oficial -->
        <div class="card window-card">
          <div class="card-header">
            <h3 class="card-title">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              Ventana de Inscripción
            </h3>
          </div>
          <div class="card-body">
            <div class="window-status">
              <div class="window-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              </div>
              <div class="window-info">
                <strong>Horario asignado para trámites</strong>
                <p class="text-sm text-muted">
                  {{ alumno.ventana_texto || 'Tu ventana se activa de acuerdo al promedio acumulado e indicador escolar.' }}
                </p>
                <div v-if="alumno.ventana_inicio" class="window-date font-mono text-xs">
                  Apertura: {{ formatearFecha(alumno.ventana_inicio) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Columna Derecha: Métricas Curriculares e Historial de Acreditadas -->
      <div class="perfil-col-right">
        <!-- Indicadores de Desempeño Académico -->
        <div class="stats-grid">
          <div class="stat-card stat-success">
            <div class="stat-header">
              <span class="stat-label">Promedio Acumulado</span>
              <div class="stat-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
              </div>
            </div>
            <div class="stat-value text-success font-mono">
              {{ Number(alumno.promedio_acumulado).toFixed(2) }}
            </div>
            <div class="stat-subtext">Escala oficial de 0 a 10</div>
          </div>

          <div class="stat-card stat-blue">
            <div class="stat-header">
              <span class="stat-label">Indicador Escolar</span>
              <div class="stat-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
              </div>
            </div>
            <div class="stat-value text-blue font-mono">
              {{ Number(alumno.indicador_escolar).toFixed(2) }}
            </div>
            <div class="stat-subtext">Cálculo de avance institucional</div>
          </div>

          <div class="stat-card stat-card-indigo">
            <div class="stat-header">
              <span class="stat-label">Créditos Acumulados</span>
              <div class="stat-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
              </div>
            </div>
            <div class="stat-value font-mono">
              {{ alumno.creditos }}
            </div>
            <div class="stat-subtext">Créditos aprobados en el plan</div>
          </div>

          <div class="stat-card stat-warning">
            <div class="stat-header">
              <span class="stat-label">Materias Cursadas</span>
              <div class="stat-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/></svg>
              </div>
            </div>
            <div class="stat-value font-mono">
              {{ alumno.materias_cursadas }}
            </div>
            <div class="stat-subtext">{{ alumno.materias_pasadas }} materias pasadas</div>
          </div>
        </div>

        <!-- Historial de Materias Aprobadas -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
              Materias Acreditadas en el Expediente ({{ materiasAprobadasDetalle.length }})
            </h3>
            <span class="badge badge-success">
              Prerrequisitos desbloqueados
            </span>
          </div>

          <div class="card-body">
            <div v-if="materiasAprobadasDetalle.length === 0" class="empty-state" style="padding: 2rem;">
              <p class="text-muted">Aún no cuentas con materias acreditadas en este plan de estudios.</p>
            </div>

            <div v-else class="aprobadas-list">
              <div
                v-for="mat in materiasAprobadasDetalle"
                :key="mat.id"
                class="aprobada-item"
              >
                <div class="aprobada-item-left">
                  <div class="aprobada-check">✓</div>
                  <div>
                    <strong class="aprobada-nombre">{{ mat.nombre }}</strong>
                    <div class="font-mono text-xs text-muted">{{ mat.clave }} · Semestre {{ mat.semestre }}</div>
                  </div>
                </div>
                <div class="aprobada-item-right">
                  <span class="badge badge-neutral font-mono">{{ mat.creditos }} créditos</span>
                </div>
              </div>
            </div>
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

.perfil-layout {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 1.5rem;
  align-items: start;
}

/* Columna Izquierda */
.perfil-col-left {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.identity-card {
  overflow: hidden;
  text-align: center;
}

.identity-banner {
  height: 80px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--violet) 100%);
}

.identity-body {
  padding: 0 1.5rem 1.5rem;
  margin-top: -40px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.identity-avatar-lg {
  width: 76px;
  height: 76px;
  border-radius: 50%;
  background: #ffffff;
  color: var(--primary);
  font-size: 1.6rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-md);
  border: 4px solid #ffffff;
  margin-bottom: 0.75rem;
}

.identity-name {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--text-main);
  margin-bottom: 0.25rem;
}

.identity-matricula {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 0.85rem;
}

.identity-tags {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
}

.identity-meta-list {
  width: 100%;
  border-top: 1px solid var(--border-subtle);
  padding-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  text-align: left;
}

.id-meta-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.825rem;
}

.id-meta-label {
  color: var(--text-muted);
}

.id-meta-val {
  color: var(--text-main);
}

/* Ventana Card */
.window-status {
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
}

.window-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: var(--primary-light);
  color: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.window-date {
  color: var(--primary);
  font-weight: 600;
  margin-top: 0.4rem;
}

/* Columna Derecha */
.perfil-col-right {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.aprobadas-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 0.75rem;
}

.aprobada-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.aprobada-item-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.aprobada-check {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--success);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 800;
  flex-shrink: 0;
}

.aprobada-nombre {
  display: block;
  font-size: 0.875rem;
  color: var(--text-main);
}

.font-mono {
  font-family: 'JetBrains Mono', monospace;
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

.text-blue {
  color: var(--blue);
}

.text-muted {
  color: var(--text-muted);
}

@media (max-width: 900px) {
  .perfil-layout {
    grid-template-columns: 1fr;
  }
}
</style>
