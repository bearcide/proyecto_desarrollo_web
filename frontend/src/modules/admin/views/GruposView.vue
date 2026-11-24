<template>
  <div class="grupos-page admin-view">
    <header class="ui-page-header">
      <div>
        <h1 class="ui-large-title">Grupos y cupos</h1>
        <p class="ui-page-subtitle">Grupos ofertados con su profesor, cupo y horario</p>
      </div>
      <div class="ui-page-actions">
        <button type="button" class="btn btn-secondary btn-sm" :disabled="cargando" @click="cargarDatos">
          <AppIcon name="refresh" :size="14" :class="{ girando: cargando }" />
          Actualizar
        </button>
      </div>
    </header>

    <ErrorBanner
      v-if="errorMsg"
      titulo="No pudimos cargar los grupos"
      :mensaje="errorMsg"
      :cargando="cargando"
      @reintentar="cargarDatos"
    />

    <section class="card">
      <div class="card-header">
        <h2 class="card-title">
          <AppIcon name="calendar" />
          Grupos ofertados
          <span class="ui-section-count ui-num">{{ gruposFiltrados.length }}</span>
        </h2>
      </div>

      <div class="card-body">
        <!-- G2: campo de búsqueda con lupa y botón para borrar -->
        <div class="ui-search grupos-search" role="search">
          <AppIcon name="search" :size="16" class="ui-search-icon" />
          <input
            v-model="filtroTexto"
            type="search"
            placeholder="Buscar por materia, grupo o profesor"
            aria-label="Buscar grupos"
          />
          <button
            v-if="filtroTexto"
            type="button"
            class="ui-search-clear"
            aria-label="Borrar búsqueda"
            @click="filtroTexto = ''"
          >
            <AppIcon name="x-circle" :size="16" />
          </button>
        </div>

        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Materia</th>
                <th>Grupo</th>
                <th>Profesor</th>
                <th>Cupo máximo</th>
                <th>Horario</th>
              </tr>
            </thead>
            <tbody>
              <template v-if="cargando">
                <tr v-for="n in 6" :key="`sk-${n}`" aria-hidden="true">
                  <td v-for="c in 6" :key="c"><div class="skeleton ui-skel-line" style="width: 75%"></div></td>
                </tr>
              </template>

              <tr v-else-if="gruposFiltrados.length === 0">
                <td colspan="6" class="empty-cell">
                  {{ filtroTexto ? `No encontramos grupos para «${filtroTexto}».` : 'Aún no hay grupos registrados.' }}
                </td>
              </tr>

              <template v-else>
                <tr v-for="g in gruposFiltrados" :key="g.id">
                  <td class="cell-sub ui-num">#{{ g.id }}</td>
                  <td>
                    <div class="cell-strong">{{ obtenerNombreMateria(g.materia) }}</div>
                    <div class="cell-sub ui-code">{{ obtenerClaveMateria(g.materia) }}</div>
                  </td>
                  <td class="cell-strong">{{ g.clave }}</td>
                  <td>{{ g.profesor || 'Sin profesor asignado' }}</td>
                  <td class="ui-num">{{ g.cupo }} alumnos</td>
                  <td>
                    <div v-if="g.horarios && g.horarios.length" class="horarios-lista ui-num">
                      <span v-for="(h, hIdx) in g.horarios" :key="hIdx">
                        {{ h.dia }} {{ minutosAHora(h.inicio) }}–{{ minutosAHora(h.fin) }}
                      </span>
                    </div>
                    <span v-else class="cell-sub">Sin horario</span>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import api, { obtenerMensajeError } from '../../../api';
import AppIcon from '../../../components/AppIcon.vue';
import ErrorBanner from '../../../components/ErrorBanner.vue';

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
.grupos-page {
  display: flex;
  flex-direction: column;
}

.grupos-search {
  max-width: 420px;
  margin-bottom: 1rem;
}

.empty-cell {
  padding: 2.5rem !important;
  text-align: center;
  color: var(--text-muted) !important;
}

.cell-strong {
  font-weight: 600;
  color: var(--text-main);
}

.cell-sub {
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.horarios-lista {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  font-size: 0.875rem;
}

.girando {
  animation: spin 0.8s linear infinite;
}
</style>
