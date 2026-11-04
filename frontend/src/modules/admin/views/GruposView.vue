<template>
  <div class="grupos-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Grupos y Cupos Académicos</h1>
        <p class="page-subtitle">Oferta educativa activa con capacidad de aula y franjas horarias</p>
      </div>
      <div class="header-actions">
        <button
          type="button"
          class="btn btn-secondary btn-sm"
          :disabled="cargando"
          @click="cargarDatos"
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

    <div class="card">
      <div class="card-header">
        <h2 class="card-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          Grupos Ofertados ({{ gruposFiltrados.length }})
        </h2>
      </div>

      <div class="card-body">
        <!-- Filtro -->
        <div class="filter-bar">
          <div class="search-input-wrapper">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input
              v-model="filtroTexto"
              type="text"
              class="form-input"
              placeholder="Buscar por materia, grupo o profesor…"
            />
          </div>
        </div>

        <!-- Tabla de Grupos -->
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Materia</th>
                <th>Clave Grupo</th>
                <th>Profesor</th>
                <th>Cupo Máximo</th>
                <th>Horarios Asignados</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="cargando">
                <td colspan="6" class="text-center" style="padding: 2.5rem;">
                  <div class="spinner spinner-primary" style="margin: 0 auto 0.5rem;"></div>
                  <span class="text-muted">Cargando catálogo de grupos…</span>
                </td>
              </tr>

              <tr v-else-if="gruposFiltrados.length === 0">
                <td colspan="6" class="text-center" style="padding: 2.5rem; color: var(--text-muted);">
                  No hay grupos registrados o coincidentes con la búsqueda.
                </td>
              </tr>

              <tr v-for="g in gruposFiltrados" :key="g.id">
                <td class="font-mono text-muted">#{{ g.id }}</td>
                <td>
                  <strong>{{ obtenerNombreMateria(g.materia) }}</strong>
                  <div class="font-mono text-xs text-muted">{{ obtenerClaveMateria(g.materia) }}</div>
                </td>
                <td>
                  <span class="badge badge-indigo">{{ g.clave }}</span>
                </td>
                <td>{{ g.profesor || 'Sin profesor asignado' }}</td>
                <td>
                  <span class="badge badge-neutral font-mono">
                    {{ g.cupo }} alumnos
                  </span>
                </td>
                <td>
                  <div v-if="g.horarios && g.horarios.length" class="horarios-chips">
                    <span
                      v-for="(h, hIdx) in g.horarios"
                      :key="hIdx"
                      class="horario-chip"
                    >
                      <strong>{{ h.dia }}:</strong> {{ minutosAHora(h.inicio) }} - {{ minutosAHora(h.fin) }}
                    </span>
                  </div>
                  <span v-else class="text-muted">—</span>
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

const grupos = ref([]);
const mapaNodos = ref(new Map());
const cargando = ref(false);
const errorMsg = ref(null);
const filtroTexto = ref('');

function minutosAHora(minutos) {
  const h = Math.floor(minutos / 60);
  const m = minutos % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

function obtenerNombreMateria(materiaId) {
  const nodo = mapaNodos.value.get(materiaId);
  return nodo?.nombre || `Materia #${materiaId}`;
}

function obtenerClaveMateria(materiaId) {
  const nodo = mapaNodos.value.get(materiaId);
  return nodo?.clave || '';
}

const gruposFiltrados = computed(() => {
  const q = filtroTexto.value.trim().toLowerCase();
  if (!q) return grupos.value;

  return grupos.value.filter((g) => {
    const clave = (g.clave || '').toLowerCase();
    const prof = (g.profesor || '').toLowerCase();
    const matNombre = obtenerNombreMateria(g.materia).toLowerCase();
    const matClave = obtenerClaveMateria(g.materia).toLowerCase();

    return clave.includes(q) || prof.includes(q) || matNombre.includes(q) || matClave.includes(q);
  });
});

async function cargarDatos() {
  cargando.value = true;
  errorMsg.value = null;

  try {
    const [respGrupos, respNodos] = await Promise.all([
      api.get('/demo/grupos/'),
      api.get('/nodos/'),
    ]);

    grupos.value = Array.isArray(respGrupos.data) ? respGrupos.data : [];

    const nodosArray = Array.isArray(respNodos.data)
      ? respNodos.data
      : (respNodos.data?.results || []);

    const map = new Map();
    nodosArray.forEach((n) => map.set(n.id, n));
    mapaNodos.value = map;
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

.horarios-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.horario-chip {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.775rem;
  font-family: 'JetBrains Mono', monospace;
}

.font-mono {
  font-family: 'JetBrains Mono', monospace;
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
