<template>
  <div class="alumnos-page admin-view">
    <header class="ui-page-header">
      <div>
        <h1 class="ui-large-title">Padrón de alumnos</h1>
        <p class="ui-page-subtitle">Estudiantes inscritos en la institución</p>
      </div>
      <div class="ui-page-actions">
        <router-link to="/admin/importar" class="btn btn-secondary btn-sm">
          <AppIcon name="upload" :size="14" />
          Importar alumnos con CSV
        </router-link>
      </div>
    </header>

    <ErrorBanner
      v-if="errorMsg"
      titulo="No pudimos cargar el padrón"
      :mensaje="errorMsg"
      :cargando="cargando"
      @reintentar="cargarAlumnos"
    />

    <section class="card">
      <div class="card-header">
        <h2 class="card-title">
          <AppIcon name="users" />
          Estudiantes registrados
          <span class="ui-section-count ui-num">{{ totalAlumnos }}</span>
        </h2>
      </div>

      <div class="card-body">
        <div class="ui-search alumnos-search" role="search">
          <AppIcon name="search" :size="16" class="ui-search-icon" />
          <input
            v-model="terminoBusqueda"
            type="search"
            placeholder="Buscar por matrícula, nombre o apellidos"
            aria-label="Buscar alumnos"
            @input="onSearchInput"
          />
          <button
            v-if="terminoBusqueda"
            type="button"
            class="ui-search-clear"
            aria-label="Borrar búsqueda"
            @click="limpiarBusqueda"
          >
            <AppIcon name="x-circle" :size="16" />
          </button>
        </div>

        <!-- A1: columnas esenciales -->
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Matrícula</th>
                <th>Nombre completo</th>
                <th>Plan</th>
                <th>Estatus</th>
                <th class="th-detalles">Detalles</th>
              </tr>
            </thead>
            <tbody>
              <!-- T7: filas esqueleto mientras carga -->
              <template v-if="cargando">
                <tr v-for="n in 6" :key="`sk-${n}`" aria-hidden="true">
                  <td><div class="skeleton ui-skel-line" style="width: 60px"></div></td>
                  <td><div class="skeleton ui-skel-line" style="width: 70%"></div></td>
                  <td><div class="skeleton ui-skel-line" style="width: 110px"></div></td>
                  <td><div class="skeleton ui-skel-line" style="width: 60px"></div></td>
                  <td><div class="skeleton ui-skel-line" style="width: 80px"></div></td>
                </tr>
              </template>

              <tr v-else-if="alumnos.length === 0">
                <td colspan="5" class="empty-cell">
                  {{ terminoBusqueda ? `No encontramos alumnos para «${terminoBusqueda}».` : 'Aún no hay alumnos registrados.' }}
                </td>
              </tr>

              <!-- Toda la fila abre la ficha -->
              <template v-else>
              <tr
                v-for="a in alumnos"
                :key="a.id"
                class="alumno-row"
                @click="abrirDetalle(a)"
              >
                <td class="cell-strong ui-num">{{ a.numero_de_cuenta }}</td>
                <td class="cell-strong">{{ nombreCompleto(a) }}</td>
                <!-- A4: número y nombre del plan -->
                <td>
                  <span class="ui-num">#{{ a.plan_estudios }}</span>
                  <span v-if="nombrePlan(a.plan_estudios)" class="cell-sub"> · {{ nombrePlan(a.plan_estudios) }}</span>
                </td>
                <td>
                  <span class="estatus" :class="a.activo ? 'estatus-activo' : 'estatus-inactivo'">
                    <span class="estatus-dot" aria-hidden="true"></span>
                    {{ a.activo ? 'Activo' : 'Inactivo' }}
                  </span>
                </td>
                <td class="td-detalles">
                  <button
                    type="button"
                    class="btn btn-secondary btn-sm"
                    :aria-label="`Ver ficha de ${nombreCompleto(a)}`"
                    @click.stop="abrirDetalle(a)"
                  >
                    Ver ficha
                  </button>
                </td>
              </tr>
              </template>
            </tbody>
          </table>
        </div>

        <!-- A5: paginación clara -->
        <div class="pagination-footer">
          <div class="pagination-info ui-num">
            Página {{ paginaActual }} de {{ totalPaginas }} · {{ totalAlumnos }} alumnos
          </div>
          <div class="pagination-buttons">
            <button
              type="button"
              class="btn btn-secondary btn-sm"
              :disabled="!urlAnterior || cargando"
              aria-label="Página anterior"
              @click="cambiarPagina(paginaActual - 1)"
            >
              <AppIcon name="chevron-left" :size="16" />
              Anterior
            </button>
            <button
              type="button"
              class="btn btn-secondary btn-sm"
              :disabled="!urlSiguiente || cargando"
              aria-label="Página siguiente"
              @click="cambiarPagina(paginaActual + 1)"
            >
              Siguiente
              <AppIcon name="chevron-right" :size="16" />
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- A3: ficha como hoja (Escape, clic fuera o ×) -->
    <AppSheet
      :abierto="!!alumnoSeleccionado"
      titulo="Ficha del estudiante"
      :subtitulo="alumnoSeleccionado ? `Matrícula ${alumnoSeleccionado.numero_de_cuenta}` : ''"
      @cerrar="alumnoSeleccionado = null"
    >
      <template v-if="alumnoSeleccionado">
        <div class="ficha-identidad">
          <div class="ficha-avatar" aria-hidden="true">
            {{ alumnoSeleccionado.nombre?.charAt(0) }}{{ alumnoSeleccionado.apellido_paterno?.charAt(0) }}
          </div>
          <div>
            <div class="ficha-nombre">{{ nombreCompleto(alumnoSeleccionado) }}</div>
            <div class="ficha-plan ui-num">
              Plan #{{ alumnoSeleccionado.plan_estudios }}
              <template v-if="nombrePlan(alumnoSeleccionado.plan_estudios)">
                · {{ nombrePlan(alumnoSeleccionado.plan_estudios) }}
              </template>
              · {{ alumnoSeleccionado.activo ? 'Activo' : 'Inactivo' }}
            </div>
          </div>
        </div>

        <div class="ui-grouped ficha-datos">
          <div class="ui-row">
            <span class="ui-row-label">Promedio</span>
            <span class="ui-row-value">{{ Number(alumnoSeleccionado.promedio_acumulado).toFixed(2) }}</span>
          </div>
          <div class="ui-row">
            <span class="ui-row-label">Semestre</span>
            <span class="ui-row-value">{{ alumnoSeleccionado.semestre }}</span>
          </div>
          <div class="ui-row">
            <span class="ui-row-label">Créditos</span>
            <span class="ui-row-value">{{ alumnoSeleccionado.creditos }}</span>
          </div>
          <div class="ui-row">
            <span class="ui-row-label">Indicador escolar</span>
            <span class="ui-row-value">{{ Number(alumnoSeleccionado.indicador_escolar).toFixed(2) }}</span>
          </div>
        </div>

        <h3 class="ficha-seccion">
          Materias aprobadas
          <span class="ui-section-count">{{ (alumnoSeleccionado.materias_aprobadas_ids || []).length }}</span>
        </h3>
        <div v-if="alumnoSeleccionado.materias_aprobadas_ids?.length" class="ui-grouped ficha-materias">
          <div v-for="id in alumnoSeleccionado.materias_aprobadas_ids" :key="id" class="ui-row">
            <span class="materia-id ui-num">#{{ id }}</span>
            <!-- A4: número y nombre de la materia -->
            <div class="ui-row-main">
              <div class="ui-row-title">{{ materia(id)?.nombre || 'Materia sin nombre disponible' }}</div>
              <div v-if="materia(id)?.clave" class="ui-row-subtitle"><span class="ui-code">{{ materia(id).clave }}</span></div>
            </div>
          </div>
        </div>
        <p v-else class="ficha-vacio">Sin materias aprobadas registradas.</p>

        <template v-if="alumnoSeleccionado.ventana_texto">
          <h3 class="ficha-seccion">Ventana de inscripción</h3>
          <p class="ficha-texto">{{ alumnoSeleccionado.ventana_texto }}</p>
        </template>
      </template>
    </AppSheet>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import api, { obtenerMensajeError } from '../../../api';
import AppIcon from '../../../components/AppIcon.vue';
import AppSheet from '../../../components/AppSheet.vue';
import ErrorBanner from '../../../components/ErrorBanner.vue';

const alumnos = ref([]);
const totalAlumnos = ref(0);
const cargando = ref(false);
const errorMsg = ref(null);

const terminoBusqueda = ref('');
const paginaActual = ref(1);
const urlSiguiente = ref(null);
const urlAnterior = ref(null);
const tamanoPagina = ref(25); // PAGE_SIZE por defecto del backend; se ajusta con la primera página llena

const alumnoSeleccionado = ref(null);

// A4: catálogos para mostrar nombres junto a los números
const planesPorId = ref(new Map());
const materiasPorId = ref(new Map());

let debounceTimeout = null;

const totalPaginas = computed(() => Math.max(1, Math.ceil(totalAlumnos.value / tamanoPagina.value)));

function nombreCompleto(a) {
  return [a.nombre, a.apellido_paterno, a.apellido_materno].filter(Boolean).join(' ');
}

function nombrePlan(id) {
  return planesPorId.value.get(id)?.nombre || '';
}

function materia(id) {
  return materiasPorId.value.get(id);
}

function onSearchInput() {
  clearTimeout(debounceTimeout);
  debounceTimeout = setTimeout(() => {
    paginaActual.value = 1;
    cargarAlumnos();
  }, 350);
}

function limpiarBusqueda() {
  terminoBusqueda.value = '';
  paginaActual.value = 1;
  cargarAlumnos();
}

async function cargarAlumnos() {
  cargando.value = true;
  errorMsg.value = null;

  try {
    const params = {
      page: paginaActual.value,
    };
    if (terminoBusqueda.value.trim()) {
      params.search = terminoBusqueda.value.trim();
    }

    const { data } = await api.get('/alumnos/', { params });
    if (data.results) {
      alumnos.value = data.results;
      totalAlumnos.value = data.count || 0;
      urlSiguiente.value = data.next;
      urlAnterior.value = data.previous;
      if (data.next && data.results.length) tamanoPagina.value = data.results.length;
    } else if (Array.isArray(data)) {
      alumnos.value = data;
      totalAlumnos.value = data.length;
      urlSiguiente.value = null;
      urlAnterior.value = null;
    }
  } catch (err) {
    errorMsg.value = obtenerMensajeError(err);
  } finally {
    cargando.value = false;
  }
}

// Nombres de planes y materias: si falla, la vista sigue mostrando solo los números
async function cargarCatalogos() {
  const lista = (data) => (Array.isArray(data) ? data : (data?.results || []));
  try {
    const [respPlanes, respNodos] = await Promise.all([
      api.get('/planes-estudios/'),
      api.get('/nodos/'),
    ]);
    planesPorId.value = new Map(lista(respPlanes.data).map((p) => [p.id, p]));
    materiasPorId.value = new Map(lista(respNodos.data).map((n) => [n.id, n]));
  } catch {
    /* sin nombres disponibles */
  }
}

function cambiarPagina(nuevaPagina) {
  if (nuevaPagina < 1) return;
  paginaActual.value = nuevaPagina;
  cargarAlumnos();
}

function abrirDetalle(alumno) {
  alumnoSeleccionado.value = alumno;
}

onMounted(() => {
  cargarAlumnos();
  cargarCatalogos();
});
</script>

<style scoped>
.alumnos-page {
  display: flex;
  flex-direction: column;
}

.alumnos-search {
  max-width: 420px;
  margin-bottom: 1rem;
}

.empty-cell {
  padding: 2.5rem !important;
  text-align: center;
  color: var(--text-muted) !important;
}

.alumno-row {
  cursor: pointer;
}

.alumno-row:hover td {
  background-color: var(--row-hover);
}

.cell-strong {
  font-weight: 600;
  color: var(--text-main);
}

.cell-sub {
  color: var(--text-muted);
}

.th-detalles,
.td-detalles {
  text-align: right;
}

/* Estatus: punto + texto (no solo color) */
.estatus {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
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

/* Paginación */
.pagination-footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-top: 1rem;
}

.pagination-info {
  font-size: 0.875rem;
  color: var(--text-muted);
}

.pagination-buttons {
  display: flex;
  gap: 0.5rem;
}

/* Ficha */
.ficha-identidad {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  margin-bottom: 1.1rem;
}

.ficha-avatar {
  flex-shrink: 0;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--accent);
  color: var(--on-accent);
  font-size: 1.25rem;
  font-weight: 700;
}

.ficha-nombre {
  font-size: 1.0625rem;
  font-weight: 700;
  color: var(--text-main);
}

.ficha-plan {
  margin-top: 0.1rem;
  font-size: 0.875rem;
  color: var(--text-muted);
}

.ficha-datos,
.ficha-materias {
  background-color: var(--bg-surface);
  border-color: transparent;
}

.ficha-seccion {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin: 1.25rem 0 0.5rem;
  padding: 0 0.25rem;
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--text-main);
}

.ficha-materias .ui-row {
  --ui-separator-inset: 4rem;
}

.materia-id {
  flex-shrink: 0;
  width: 2.4rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-muted);
}

.ficha-vacio,
.ficha-texto {
  padding: 0 0.25rem;
  font-size: 0.9375rem;
  color: var(--text-muted);
}
</style>
