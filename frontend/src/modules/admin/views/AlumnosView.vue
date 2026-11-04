<template>
  <div class="alumnos-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Padrón de Alumnos</h1>
        <p class="page-subtitle">Listado oficial de estudiantes matriculados en la institución</p>
      </div>
      <div class="header-actions">
        <router-link to="/admin/importar" class="btn btn-secondary btn-sm">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          Importar alumnos CSV
        </router-link>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="errorMsg" class="alert alert-danger" role="alert">
      {{ errorMsg }}
    </div>

    <div class="card">
      <div class="card-header">
        <h2 class="card-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          Estudiantes Registrados ({{ totalAlumnos }})
        </h2>
      </div>

      <div class="card-body">
        <!-- Buscador -->
        <div class="filter-bar">
          <div class="search-input-wrapper">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input
              v-model="terminoBusqueda"
              type="text"
              class="form-input"
              placeholder="Buscar por matrícula, nombre o apellidos…"
              @input="onSearchInput"
            />
          </div>
          <button
            v-if="terminoBusqueda"
            type="button"
            class="btn btn-outline btn-sm"
            @click="limpiarBusqueda"
          >
            Limpiar búsqueda
          </button>
        </div>

        <!-- Tabla de Alumnos -->
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Matrícula</th>
                <th>Nombre Completo</th>
                <th>Plan</th>
                <th>Semestre</th>
                <th>Promedio</th>
                <th>Créditos</th>
                <th>Materias Aprobadas</th>
                <th>Estatus</th>
                <th>Detalles</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="cargando">
                <td colspan="9" class="text-center" style="padding: 2.5rem;">
                  <div class="spinner spinner-primary" style="margin: 0 auto 0.5rem;"></div>
                  <span class="text-muted">Cargando padrón de alumnos…</span>
                </td>
              </tr>

              <tr v-else-if="alumnos.length === 0">
                <td colspan="9" class="text-center" style="padding: 2.5rem; color: var(--text-muted);">
                  No se encontraron alumnos con el criterio de búsqueda.
                </td>
              </tr>

              <tr
                v-for="a in alumnos"
                :key="a.id"
                class="alumno-row"
                @click="abrirDetalle(a)"
              >
                <td class="font-mono font-bold">{{ a.numero_de_cuenta }}</td>
                <td>
                  <strong>{{ a.nombre }} {{ a.apellido_paterno }} {{ a.apellido_materno }}</strong>
                </td>
                <td>
                  <span class="badge badge-indigo">Plan #{{ a.plan_estudios }}</span>
                </td>
                <td class="text-center font-mono">{{ a.semestre }}</td>
                <td class="font-mono font-bold">{{ Number(a.promedio_acumulado).toFixed(2) }}</td>
                <td class="font-mono">{{ a.creditos }}</td>
                <td>
                  <span class="badge badge-success">
                    {{ (a.materias_aprobadas_ids || []).length }} aprobadas
                  </span>
                </td>
                <td>
                  <span class="badge" :class="a.activo ? 'badge-success' : 'badge-neutral'">
                    {{ a.activo ? 'Activo' : 'Inactivo' }}
                  </span>
                </td>
                <td>
                  <button
                    type="button"
                    class="btn btn-secondary btn-sm"
                    @click.stop="abrirDetalle(a)"
                  >
                    Ver ficha
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Paginación DRF -->
        <div class="pagination-footer">
          <div class="text-sm text-muted">
            Mostrando página {{ paginaActual }} · Total: {{ totalAlumnos }} alumnos
          </div>
          <div class="pagination-buttons">
            <button
              type="button"
              class="btn btn-secondary btn-sm"
              :disabled="!urlAnterior || cargando"
              @click="cambiarPagina(paginaActual - 1)"
            >
              ← Anterior
            </button>
            <button
              type="button"
              class="btn btn-secondary btn-sm"
              :disabled="!urlSiguiente || cargando"
              @click="cambiarPagina(paginaActual + 1)"
            >
              Siguiente →
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Detalle del Alumno -->
    <div v-if="alumnoSeleccionado" class="modal-backdrop" @click="alumnoSeleccionado = null">
      <div class="modal-box" @click.stop>
        <div class="modal-header">
          <div>
            <h3 class="modal-title">Ficha del Estudiante</h3>
            <span class="font-mono text-xs text-muted">{{ alumnoSeleccionado.numero_de_cuenta }}</span>
          </div>
          <button
            type="button"
            class="modal-close-btn"
            @click="alumnoSeleccionado = null"
          >
            ×
          </button>
        </div>

        <div class="modal-body">
          <div class="student-profile-summary">
            <div class="student-avatar-lg">
              {{ alumnoSeleccionado.nombre?.charAt(0) }}{{ alumnoSeleccionado.apellido_paterno?.charAt(0) }}
            </div>
            <div>
              <h4 class="student-fullname">
                {{ alumnoSeleccionado.nombre }} {{ alumnoSeleccionado.apellido_paterno }} {{ alumnoSeleccionado.apellido_materno }}
              </h4>
              <p class="text-sm text-muted">
                Matrícula: <strong class="font-mono">{{ alumnoSeleccionado.numero_de_cuenta }}</strong> · Plan #{{ alumnoSeleccionado.plan_estudios }}
              </p>
            </div>
          </div>

          <div class="stats-mini-grid">
            <div class="stat-mini">
              <span class="stat-mini-label">Promedio</span>
              <strong class="stat-mini-val">{{ Number(alumnoSeleccionado.promedio_acumulado).toFixed(2) }}</strong>
            </div>
            <div class="stat-mini">
              <span class="stat-mini-label">Semestre</span>
              <strong class="stat-mini-val">{{ alumnoSeleccionado.semestre }}</strong>
            </div>
            <div class="stat-mini">
              <span class="stat-mini-label">Créditos</span>
              <strong class="stat-mini-val">{{ alumnoSeleccionado.creditos }}</strong>
            </div>
            <div class="stat-mini">
              <span class="stat-mini-label">Indicador Escolar</span>
              <strong class="stat-mini-val">{{ Number(alumnoSeleccionado.indicador_escolar).toFixed(2) }}</strong>
            </div>
          </div>

          <div class="detail-section">
            <h5 class="detail-subtitle">Materias Aprobadas (IDs)</h5>
            <div v-if="alumnoSeleccionado.materias_aprobadas_ids?.length" class="ids-wrap">
              <span
                v-for="id in alumnoSeleccionado.materias_aprobadas_ids"
                :key="id"
                class="badge badge-indigo"
              >
                Materia #{{ id }}
              </span>
            </div>
            <p v-else class="text-sm text-muted">Sin materias aprobadas registradas.</p>
          </div>

          <div v-if="alumnoSeleccionado.ventana_texto" class="detail-section">
            <h5 class="detail-subtitle">Ventana de Inscripción</h5>
            <p class="text-sm text-muted">{{ alumnoSeleccionado.ventana_texto }}</p>
          </div>
        </div>

        <div class="modal-footer">
          <button
            type="button"
            class="btn btn-secondary btn-sm"
            @click="alumnoSeleccionado = null"
          >
            Cerrar ficha
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api, { obtenerMensajeError } from '../../../api';

const alumnos = ref([]);
const totalAlumnos = ref(0);
const cargando = ref(false);
const errorMsg = ref(null);

const terminoBusqueda = ref('');
const paginaActual = ref(1);
const urlSiguiente = ref(null);
const urlAnterior = ref(null);

const alumnoSeleccionado = ref(null);

let debounceTimeout = null;

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
});
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

.alumno-row {
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.alumno-row:hover {
  background-color: var(--primary-light) !important;
}

.pagination-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 1rem;
  margin-top: 1rem;
  border-top: 1px solid var(--border);
}

.pagination-buttons {
  display: flex;
  gap: 0.5rem;
}

/* Modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(15, 23, 42, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-box {
  background: #ffffff;
  border-radius: var(--radius-md);
  width: 100%;
  max-width: 520px;
  box-shadow: var(--shadow-xl);
  overflow: hidden;
  animation: modalEnter 0.2s ease-out;
}

@keyframes modalEnter {
  from { opacity: 0; transform: scale(0.96); }
  to { opacity: 1; transform: scale(1); }
}

.modal-header {
  padding: 1.15rem 1.5rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-main);
}

.modal-close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--text-light);
  cursor: pointer;
}

.modal-close-btn:hover {
  color: var(--text-main);
}

.modal-body {
  padding: 1.5rem;
}

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border);
  background-color: var(--bg-main);
  display: flex;
  justify-content: flex-end;
}

.student-profile-summary {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.student-avatar-lg {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary) 0%, var(--violet) 100%);
  color: #ffffff;
  font-weight: 800;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.student-fullname {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 0.15rem;
}

.stats-mini-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
  margin-bottom: 1.25rem;
}

.stat-mini {
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.5rem;
  text-align: center;
}

.stat-mini-label {
  display: block;
  font-size: 0.65rem;
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: 600;
}

.stat-mini-val {
  font-size: 1.1rem;
  font-family: 'JetBrains Mono', monospace;
  color: var(--primary);
}

.detail-section {
  margin-top: 1rem;
  border-top: 1px solid var(--border-subtle);
  padding-top: 0.75rem;
}

.detail-subtitle {
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 0.4rem;
}

.ids-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
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

.text-sm {
  font-size: 0.875rem;
}
</style>
