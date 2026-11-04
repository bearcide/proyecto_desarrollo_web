<template>
  <div class="planes-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Planes de Estudio y Catálogo Curricular</h1>
        <p class="page-subtitle">Estructura académica de carreras y prerrequisitos del grafo escolar</p>
      </div>
      <div class="header-actions">
        <button
          type="button"
          class="btn btn-secondary btn-sm"
          :disabled="cargando"
          @click="cargarPlanes"
        >
          <svg :class="{ spinner: cargando }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
          Actualizar
        </button>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="errorMsg" class="alert alert-danger" role="alert">
      {{ errorMsg }}
    </div>

    <!-- Lista de Planes -->
    <div v-if="cargando" class="empty-state">
      <div class="spinner spinner-primary" style="margin: 0 auto 0.5rem;"></div>
      <span class="text-muted">Cargando planes de estudio…</span>
    </div>

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
            <span class="badge badge-indigo">Plan ID #{{ plan.id }}</span>
          </div>
          <span class="badge" :class="plan.activo ? 'badge-success' : 'badge-neutral'">
            {{ plan.activo ? 'Activo' : 'Inactivo' }}
          </span>
        </div>
        <p class="plan-desc">{{ plan.descripcion || 'Sin descripción registrada' }}</p>
        <div class="plan-footer">
          <span class="text-xs text-muted">
            {{ contarMateriasDePlan(plan.id) }} materias asociadas
          </span>
          <button type="button" class="btn btn-outline btn-sm">
            {{ planSeleccionado?.id === plan.id ? 'Viendo materias' : 'Ver materias' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Materias del Plan Seleccionado -->
    <div v-if="planSeleccionado" class="card materias-card">
      <div class="card-header">
        <h2 class="card-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/></svg>
          Materias Curriculares de: {{ planSeleccionado.nombre }}
        </h2>
        <span class="badge badge-indigo">
          {{ materiasDelPlan.length }} materias registradas
        </span>
      </div>

      <div class="card-body">
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Clave</th>
                <th>Nombre de la Asignatura</th>
                <th>Semestre</th>
                <th>Créditos</th>
                <th>Prerrequisitos Requeridos</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="materiasDelPlan.length === 0">
                <td colspan="5" class="text-center" style="padding: 2rem; color: var(--text-muted);">
                  No hay materias asociadas a este plan de estudios.
                </td>
              </tr>
              <tr v-for="m in materiasDelPlan" :key="m.id">
                <td class="font-mono font-bold">{{ m.clave }}</td>
                <td><strong>{{ m.nombre }}</strong></td>
                <td>Semestre {{ m.semestre }}</td>
                <td class="font-mono">{{ m.creditos }} créditos</td>
                <td>
                  <div v-if="m.prerrequisitos && m.prerrequisitos.length" class="prereqs-wrap">
                    <span
                      v-for="reqId in m.prerrequisitos"
                      :key="reqId"
                      class="badge badge-neutral font-mono text-xs"
                    >
                      {{ obtenerClavePorId(reqId) || `#${reqId}` }}
                    </span>
                  </div>
                  <span v-else class="text-muted text-xs">Ninguno</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import api, { obtenerMensajeError } from '../../../api';

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

.planes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.75rem;
}

.plan-card {
  padding: 1.25rem;
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.plan-card:hover {
  border-color: var(--primary-border);
  transform: translateY(-2px);
}

.plan-card-active {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary-light);
}

.plan-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.plan-name {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 0.25rem;
}

.plan-desc {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 1rem;
  flex: 1;
}

.plan-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid var(--border-subtle);
  padding-top: 0.75rem;
}

.materias-card {
  margin-top: 1.5rem;
}

.prereqs-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.font-mono {
  font-family: 'JetBrains Mono', monospace;
}

.font-bold {
  font-weight: 700;
}

.text-center {
  text-align: center;
}

.text-muted {
  color: var(--text-muted);
}

.text-xs {
  font-size: 0.75rem;
}
</style>
