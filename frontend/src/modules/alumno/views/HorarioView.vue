<template>
  <div class="alumno-horario-page">
    <!-- Encabezado uniforme (A4 / B1) -->
    <header class="ui-page-header">
      <div>
        <h1 class="ui-large-title">Mi horario</h1>
        <p class="ui-page-subtitle">Tu carga académica y horario semanal del periodo</p>
      </div>
      <div class="ui-page-actions">
        <span
          v-if="!cargando"
          class="badge badge-lg"
          :class="hayPublicacion ? 'badge-success' : 'badge-warning'"
        >
          ● {{ hayPublicacion ? 'Horarios oficiales publicados' : 'Horarios en proceso' }}
        </span>
      </div>
    </header>

    <ErrorBanner
      v-if="errorGenerico"
      titulo="No pudimos cargar tu horario"
      :mensaje="errorGenerico"
      :cargando="cargando"
      @reintentar="consultarHorario"
    />

    <!-- Carga: esqueleto con la forma del contenido (A9) -->
    <div v-if="cargando" class="horario-layout" aria-busy="true" aria-label="Cargando horario">
      <aside class="horario-col-left">
        <div class="ui-grouped skel-box">
          <div v-for="n in 4" :key="n" class="ui-row"><div class="skeleton ui-skel-line" style="width: 100%"></div></div>
        </div>
      </aside>
      <div class="horario-col-right">
        <div class="card skel-box">
          <div class="card-body">
            <div class="skeleton ui-skel-title"></div>
            <div class="skeleton" style="height: 320px"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Sin publicación todavía (B7) -->
    <div v-else-if="!hayPublicacion && !errorGenerico" class="card">
      <div class="ui-empty">
        <div class="ui-empty-icon empty-warning"><AppIcon name="clock" :size="26" /></div>
        <h2 class="ui-empty-title">Tus horarios aún no se publican</h2>
        <p class="ui-empty-text">
          En cuanto la escuela publique la asignación oficial, verás aquí tus materias y tu horario semanal.
        </p>
        <button type="button" class="btn btn-primary" @click="consultarHorario">
          <AppIcon name="refresh" :size="16" />
          Volver a consultar
        </button>
      </div>
    </div>

    <!-- Horarios publicados -->
    <div v-else-if="hayPublicacion" class="horario-layout">
      <!-- Columna izquierda: resumen compacto (A4 / B2) -->
      <aside class="horario-col-left">
        <h2 class="ui-section-title">Resumen</h2>
        <div class="ui-grouped resumen-list">
          <div class="ui-row">
            <span class="ui-row-icon tint-success"><AppIcon name="check" :size="16" /></span>
            <span class="ui-row-label">Materias asignadas</span>
            <span class="ui-row-value">{{ materiasAsignadas.length }}</span>
          </div>
          <div class="ui-row">
            <span class="ui-row-icon tint-blue"><AppIcon name="credits" :size="16" /></span>
            <span class="ui-row-label">Total de créditos</span>
            <span class="ui-row-value">{{ totalCreditosAsignados }}</span>
          </div>
          <div v-if="materiasPendientes.length > 0" class="ui-row">
            <span class="ui-row-icon tint-warning"><AppIcon name="warning" :size="16" /></span>
            <span class="ui-row-label">No asignadas</span>
            <span class="ui-row-value">{{ materiasPendientes.length }}</span>
          </div>
          <div class="ui-row">
            <span class="ui-row-icon tint-indigo"><AppIcon name="shield" :size="16" /></span>
            <div class="ui-row-main">
              <div class="ui-row-label">Estatus de inscripción</div>
              <div class="ui-row-subtitle">Ejecución institucional #{{ ejecucionId }}</div>
            </div>
            <span class="ui-row-value status-value">Oficial</span>
          </div>
        </div>
      </aside>

      <!-- Columna derecha: horario y detalle -->
      <div class="horario-col-right">
        <section class="card schedule-card">
          <div class="card-header">
            <h2 class="card-title">
              <AppIcon name="calendar" />
              Horario semanal
            </h2>
          </div>
          <div class="card-body">
            <HorarioGrid :items="materiasAsignadas" />
          </div>
        </section>

        <!-- Detalle como lista agrupada (B5) -->
        <section>
          <h2 class="ui-section-title">
            Materias asignadas
            <span class="ui-section-count">{{ materiasAsignadas.length }}</span>
          </h2>
          <div v-if="materiasAsignadas.length" class="ui-grouped">
            <div
              v-for="(item, idx) in materiasAsignadas"
              :key="item.clave_materia + idx"
              class="ui-row materia-row"
            >
              <span class="color-dot" :class="`dot-${colorDe(item) % 6}`" aria-hidden="true"></span>
              <div class="ui-row-main">
                <div class="ui-row-title">{{ item.detalle?.nombre_materia || item.clave_materia }}</div>
                <div class="ui-row-subtitle">
                  <span class="ui-code">{{ item.clave_materia }}</span>
                  · Grupo {{ item.detalle?.grupo || item.grupo || 'G1' }}
                  · {{ item.detalle?.profesor || 'Profesor por asignar' }}
                </div>
              </div>
              <div class="materia-horario ui-num">{{ formatearHorarios(item.detalle?.horarios) }}</div>
            </div>
          </div>
          <div v-else class="ui-grouped">
            <div class="ui-empty">
              <p class="ui-empty-text">No tienes materias asignadas en esta publicación.</p>
            </div>
          </div>
        </section>

        <!-- Solicitudes no asignadas: icono + texto, no solo color (B6) -->
        <section v-if="materiasPendientes.length > 0">
          <h2 class="ui-section-title">
            Solicitudes no asignadas
            <span class="ui-section-count">{{ materiasPendientes.length }}</span>
          </h2>
          <div class="ui-grouped">
            <div
              v-for="(item, idx) in materiasPendientes"
              :key="item.clave_materia + idx"
              class="ui-row pendiente-row"
            >
              <span class="ui-row-icon tint-warning"><AppIcon name="warning" :size="16" /></span>
              <div class="ui-row-main">
                <div class="ui-row-title">{{ item.detalle?.nombre_materia || item.clave_materia }}</div>
                <div class="ui-row-subtitle">
                  {{ item.detalle?.explicacion || 'No fue posible asignar cupo en las opciones solicitadas.' }}
                </div>
              </div>
              <span class="motivo-tag">
                No asignada · {{ textoMotivo(item.motivo) }}
              </span>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import api, { obtenerMensajeError } from '../../../api';
import HorarioGrid from '../../../components/HorarioGrid.vue';
import AppIcon from '../../../components/AppIcon.vue';
import ErrorBanner from '../../../components/ErrorBanner.vue';

const cargando = ref(false);
const hayPublicacion = ref(false);
const ejecucionId = ref(null);
const resultadosPropios = ref([]);
const errorGenerico = ref(null);

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

// Mismo orden de colores que usa HorarioGrid (por orden de aparición de la clave)
const indicesColor = computed(() => {
  const mapa = new Map();
  materiasAsignadas.value.forEach((item) => {
    const clave = item.clave_materia || item.detalle?.clave_materia;
    if (!mapa.has(clave)) mapa.set(clave, mapa.size);
  });
  return mapa;
});

function colorDe(item) {
  return indicesColor.value.get(item.clave_materia || item.detalle?.clave_materia) ?? 0;
}

const MOTIVOS = {
  YA_APROBADA: 'Ya acreditada',
  PRERREQUISITOS: 'Faltan prerrequisitos',
  PLAN_INCORRECTO: 'No pertenece a tu plan',
  SIN_GRUPO: 'Sin grupo disponible',
  SIN_CUPO: 'Sin cupo',
  CONFLICTO_HORARIO: 'Cruce de horario',
};

function textoMotivo(motivo) {
  return MOTIVOS[motivo] || 'Motivo no especificado';
}

function minutosAHora(minutos) {
  const h = Math.floor(minutos / 60);
  const m = minutos % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

function formatearHorarios(horarios = []) {
  if (!horarios || !horarios.length) return 'Sin horario';
  return horarios
    .map((h) => `${h.dia} ${minutosAHora(h.inicio)}–${minutosAHora(h.fin)}`)
    .join(' · ');
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
}

.badge-lg {
  padding: 0.4rem 0.9rem;
  font-size: 0.875rem;
}

/* Resumen a la izquierda, contenido a la derecha (como Perfil) */
.horario-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 1.5rem;
  align-items: start;
}

.horario-col-left {
  position: sticky;
  top: calc(64px + 1.5rem);
}

.horario-col-right {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
  min-width: 0;
}

/* Iconos con tinte semántico (el texto acompaña siempre al color) */
.tint-success { background-color: var(--success-bg); color: var(--success-text); }
.tint-blue { background-color: var(--blue-light); color: var(--blue); }
.tint-warning { background-color: var(--warning-bg); color: var(--warning-text); }
.tint-indigo { background-color: var(--primary-light); color: var(--accent-text); }

.resumen-list .ui-row {
  --ui-separator-inset: 3.55rem;
}

.status-value {
  color: var(--accent-text);
}

.empty-warning {
  background-color: var(--warning-bg);
  color: var(--warning-text);
}

.schedule-card .card-header {
  padding-block: 0.9rem;
}

/* Lista de materias */
.materia-row {
  --ui-separator-inset: 2.6rem;
}

.color-dot {
  flex-shrink: 0;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

/* Mismos tonos que el borde de cada bloque en la cuadrícula */
.dot-0 { background-color: #4f46e5; }
.dot-1 { background-color: #10b981; }
.dot-2 { background-color: #f59e0b; }
.dot-3 { background-color: #8b5cf6; }
.dot-4 { background-color: #ec4899; }
.dot-5 { background-color: #0ea5e9; }

.materia-horario {
  flex-shrink: 0;
  max-width: 45%;
  font-size: 0.8125rem;
  color: var(--text-muted);
  text-align: right;
}

.pendiente-row {
  --ui-separator-inset: 3.55rem;
}

.motivo-tag {
  flex-shrink: 0;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--warning-text);
}

.skel-box .ui-row {
  min-height: 52px;
}

@media (max-width: 1024px) {
  .horario-layout {
    grid-template-columns: 1fr;
  }
  .horario-col-left {
    position: static;
  }
}
</style>
