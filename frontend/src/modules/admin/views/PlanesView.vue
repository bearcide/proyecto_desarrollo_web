<template>
  <div class="planes-page admin-view">
    <header class="ui-page-header">
      <div>
        <h1 class="ui-large-title">Planes de estudio</h1>
        <p class="ui-page-subtitle">Carreras de la institución, sus materias y los prerrequisitos de cada una</p>
      </div>
      <div class="ui-page-actions">
        <button type="button" class="btn btn-secondary btn-sm" :disabled="cargando" @click="cargarPlanes">
          <AppIcon name="refresh" :size="14" :class="{ girando: cargando }" />
          Actualizar
        </button>
      </div>
    </header>

    <ErrorBanner
      v-if="errorMsg"
      titulo="No pudimos cargar los planes de estudio"
      :mensaje="errorMsg"
      :cargando="cargando"
      @reintentar="cargarPlanes"
    />

    <!-- Carga: esqueleto (T7) -->
    <div v-if="cargando && !planes.length" class="planes-grid" aria-busy="true" aria-label="Cargando planes">
      <div v-for="n in 2" :key="n" class="card plan-card">
        <div class="skeleton ui-skel-title"></div>
        <div class="skeleton ui-skel-line" style="width: 80%"></div>
        <div class="skeleton ui-skel-line" style="width: 50%"></div>
      </div>
    </div>

    <!-- Planes (P1 no aplicado: se conservan la tarjeta, el botón y el ID) -->
    <div v-else class="planes-grid">
      <div
        v-for="plan in planes"
        :key="plan.id"
        class="card plan-card"
        :class="{ 'plan-card-active': planSeleccionado?.id === plan.id }"
        @click="seleccionarPlan(plan)"
      >
        <div class="plan-card-top">
          <div>
            <h3 class="plan-name">{{ plan.nombre }}</h3>
            <span class="badge badge-indigo ui-num">Plan #{{ plan.id }}</span>
          </div>
          <span class="estatus" :class="plan.activo ? 'estatus-activo' : 'estatus-inactivo'">
            <span class="estatus-dot" aria-hidden="true"></span>
            {{ plan.activo ? 'Activo' : 'Inactivo' }}
          </span>
        </div>
        <p class="plan-desc">{{ plan.descripcion || 'Sin descripción registrada' }}</p>
        <div class="plan-footer">
          <span class="plan-count ui-num">{{ contarMateriasDePlan(plan.id) }} materias</span>
          <button
            type="button"
            class="btn btn-sm"
            :class="planSeleccionado?.id === plan.id ? 'btn-primary' : 'btn-secondary'"
            :aria-pressed="planSeleccionado?.id === plan.id ? 'true' : 'false'"
          >
            {{ planSeleccionado?.id === plan.id ? 'Viendo materias' : 'Ver materias' }}
          </button>
        </div>
      </div>
    </div>

    <!-- P2: materias agrupadas por semestre -->
    <section v-if="planSeleccionado" class="materias-section">
      <h2 class="materias-title">
        Materias de {{ planSeleccionado.nombre }}
        <span class="ui-section-count ui-num">{{ materiasDelPlan.length }}</span>
      </h2>

      <div v-if="materiasDelPlan.length === 0" class="ui-grouped">
        <div class="ui-empty">
          <div class="ui-empty-icon"><AppIcon name="book-open" :size="22" /></div>
          <p class="ui-empty-text">Este plan de estudios aún no tiene materias.</p>
        </div>
      </div>

      <template v-else>
      <div v-for="grupo in materiasPorSemestre" :key="grupo.semestre" class="semestre-grupo">
        <h3 class="ui-section-title semestre-title">
          Semestre {{ grupo.semestre }}
          <span class="ui-section-count ui-num">
            {{ grupo.materias.length }} {{ grupo.materias.length === 1 ? 'materia' : 'materias' }} ·
            {{ grupo.creditos }} créditos
          </span>
        </h3>
        <div class="ui-grouped">
          <div v-for="m in grupo.materias" :key="m.id" class="ui-row materia-row">
            <span class="materia-clave ui-code">{{ m.clave }}</span>
            <div class="ui-row-main">
              <div class="ui-row-title">{{ m.nombre }}</div>
              <div class="ui-row-subtitle">
                <template v-if="m.prerrequisitos && m.prerrequisitos.length">
                  Requiere:
                  <span v-for="(reqId, i) in m.prerrequisitos" :key="reqId">
                    <span class="ui-code">{{ obtenerClavePorId(reqId) || `#${reqId}` }}</span>{{ i < m.prerrequisitos.length - 1 ? ', ' : '' }}
                  </span>
                </template>
                <template v-else>Sin prerrequisitos</template>
              </div>
            </div>
            <span class="ui-row-value">{{ m.creditos }} créditos</span>
          </div>
        </div>
      </div>
      </template>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import api, { obtenerMensajeError } from '../../../api';
import AppIcon from '../../../components/AppIcon.vue';
import ErrorBanner from '../../../components/ErrorBanner.vue';

const planes = ref([]);
const nodos = ref([]);
const planSeleccionado = ref(null);
const cargando = ref(false);
const errorMsg = ref(null);

function contarMateriasDePlan(planId) {
  return nodos.value.filter((n) => n.plan_estudios === planId).length;
}

const materiasDelPlan = computed(() => {
  if (!planSeleccionado.value) return [];
  return nodos.value.filter((n) => n.plan_estudios === planSeleccionado.value.id);
});

// P2: agrupar por semestre, en orden
const materiasPorSemestre = computed(() => {
  const grupos = new Map();
  materiasDelPlan.value.forEach((m) => {
    const sem = m.semestre ?? 0;
    if (!grupos.has(sem)) grupos.set(sem, []);
    grupos.get(sem).push(m);
  });
  return [...grupos.entries()]
    .sort(([a], [b]) => a - b)
    .map(([semestre, materias]) => ({
      semestre,
      materias,
      creditos: materias.reduce((s, m) => s + (Number(m.creditos) || 0), 0),
    }));
});

function obtenerClavePorId(id) {
  return nodos.value.find((n) => n.id === id)?.clave || '';
}

function seleccionarPlan(plan) {
  planSeleccionado.value = plan;
}

async function cargarPlanes() {
  cargando.value = true;
  errorMsg.value = null;

  try {
    const [respPlanes, respNodos] = await Promise.all([
      api.get('/planes-estudios/'),
      api.get('/nodos/'),
    ]);

    planes.value = Array.isArray(respPlanes.data)
      ? respPlanes.data
      : (respPlanes.data?.results || []);

    nodos.value = Array.isArray(respNodos.data)
      ? respNodos.data
      : (respNodos.data?.results || []);

    if (planes.value.length > 0 && !planSeleccionado.value) {
      planSeleccionado.value = planes.value[0];
    }
  } catch (err) {
    errorMsg.value = obtenerMensajeError(err);
  } finally {
    cargando.value = false;
  }
}

onMounted(cargarPlanes);
</script>

<style scoped>
.planes-page {
  display: flex;
  flex-direction: column;
}

.planes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.25rem;
  margin-bottom: 2rem;
}

.plan-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 1.25rem;
  border-radius: 14px;
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.plan-card:hover {
  border-color: var(--primary-border);
}

.plan-card-active {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--primary-light);
}

.plan-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.plan-name {
  margin-bottom: 0.35rem;
  font-size: 1.1875rem;
  font-weight: 700;
  color: var(--text-main);
}

.plan-desc {
  flex: 1;
  margin-bottom: 1rem;
  font-size: 0.9375rem;
  color: var(--text-muted);
}

.plan-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-subtle);
}

.plan-count {
  font-size: 0.875rem;
  color: var(--text-muted);
}

.estatus {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  flex-shrink: 0;
  font-size: 0.875rem;
  font-weight: 600;
}

.estatus-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.estatus-activo { color: var(--success-text); }
.estatus-activo .estatus-dot { background-color: var(--success); }
.estatus-inactivo { color: var(--text-muted); }
.estatus-inactivo .estatus-dot { background-color: var(--text-light); }

/* Materias por semestre (P2) */
.materias-title {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  margin-bottom: 1rem;
  font-size: 1.375rem;
  font-weight: 700;
  color: var(--text-main);
}

.semestre-grupo + .semestre-grupo {
  margin-top: 1.5rem;
}

.semestre-title {
  justify-content: flex-start;
  font-size: 0.9375rem;
}

.materia-row {
  --ui-separator-inset: 5.6rem;
}

.materia-clave {
  flex-shrink: 0;
  width: 4.5rem;
  font-weight: 600;
  color: var(--accent-text);
}

.girando {
  animation: spin 0.8s linear infinite;
}
</style>
