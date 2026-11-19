<template>
  <div class="asignaciones-page">
    <!-- Header Principal -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Generación y Publicación de Horarios</h1>
        <p class="page-subtitle">
          Motor greedy determinista con políticas institucionales, resolución de cupos y no-solapamiento
        </p>
      </div>
      <div class="header-actions">
        <button
          type="button"
          class="btn btn-primary"
          :disabled="generando || cargandoLista"
          @click="ejecutarGeneracion"
        >
          <span v-if="generando" class="spinner"></span>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          <span>{{ generando ? 'Generando asignaciones…' : 'Generar Nueva Asignación' }}</span>
        </button>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="errorMsg" class="alert alert-danger" role="alert">
      {{ errorMsg }}
    </div>

    <!-- Barra de selección de ejecuciones -->
    <div v-if="ejecuciones.length > 0" class="runs-selector-card card">
      <div class="runs-header">
        <span class="runs-label">Historial de Ejecuciones ({{ ejecuciones.length }})</span>
        <span class="runs-hint">Selecciona una para auditar o publicar:</span>
      </div>
      <div class="runs-scroll">
        <button
          v-for="run in ejecuciones"
          :key="run.id"
          type="button"
          class="run-chip-btn"
          :class="{ 'run-selected': ejecucionActual?.id === run.id }"
          @click="seleccionarEjecucion(run.id)"
        >
          <div class="run-chip-top">
            <span class="run-id">#{{ run.id }}</span>
            <span
              class="badge badge-mini"
              :class="{
                'badge-success': run.estado === 'PUBLICADO',
                'badge-indigo': run.estado === 'BORRADOR',
                'badge-neutral': run.estado === 'ARCHIVADO',
              }"
            >
              {{ run.estado }}
            </span>
          </div>
          <div class="run-chip-meta">
            {{ formatearFecha(run.created_at) }}
          </div>
          <div v-if="run.resumen" class="run-chip-stats">
            <span class="text-success">✓ {{ run.resumen.asignadas || 0 }}</span>
            <span class="text-warning">⚠ {{ run.resumen.pendientes || 0 }}</span>
          </div>
        </button>
      </div>
    </div>

    <!-- Estado de Carga -->
    <div v-if="cargandoDetalle" class="empty-state">
      <div class="spinner spinner-primary" style="width: 2rem; height: 2rem; margin: 0 auto 1rem;"></div>
      <div class="empty-state-title">Cargando resultados de la asignación…</div>
    </div>

    <!-- Estado Vacío: Sin Ejecuciones -->
    <div v-else-if="!ejecuciones.length && !cargandoLista" class="empty-state">
      <div class="empty-state-icon">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
      </div>
      <h2 class="empty-state-title">No hay asignaciones generadas todavía</h2>
      <p class="empty-state-text">
        El motor procesará todas las solicitudes de materias vigentes de los alumnos y construirá una propuesta determinista.
      </p>
      <button
        type="button"
        class="btn btn-primary btn-lg"
        :disabled="generando"
        @click="ejecutarGeneracion"
      >
        <span v-if="generando" class="spinner"></span>
        <span>Ejecutar Primera Asignación</span>
      </button>
    </div>

    <!-- Detalle de Ejecución Seleccionada -->
    <div v-else-if="ejecucionActual" class="run-detail-view">
      <!-- Tarjeta Superior de Estado y Acciones -->
      <div class="card run-banner-card">
        <div class="run-banner-left">
          <div class="run-banner-badge">
            <span
              class="badge"
              :class="{
                'badge-success': ejecucionActual.estado === 'PUBLICADO',
                'badge-indigo': ejecucionActual.estado === 'BORRADOR',
                'badge-neutral': ejecucionActual.estado === 'ARCHIVADO',
              }"
            >
              ● {{ ejecucionActual.estado }}
            </span>
            <span class="run-banner-id">Ejecución #{{ ejecucionActual.id }}</span>
          </div>
          <div class="run-banner-date">
            Generada el {{ formatearFechaCompleta(ejecucionActual.created_at) }}
          </div>
          <p class="run-policy-info">
            Política institucional: <strong>{{ ejecucionActual.politica?.version || 'greedy-v1' }}</strong> ·
            Orden: prioridad institucional → matrícula lexicográfica
          </p>
        </div>

        <div class="run-banner-actions">
          <!-- Botón de Exportar CSV -->
          <button
            type="button"
            class="btn btn-secondary btn-sm"
            :disabled="descargandoCsv"
            @click="descargarCsv"
            title="Descargar auditoría completa en CSV"
          >
            <span v-if="descargandoCsv" class="spinner"></span>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            <span>Exportar CSV</span>
          </button>

          <!-- Botón de Publicar Horarios -->
          <button
            v-if="ejecucionActual.estado !== 'PUBLICADO'"
            type="button"
            class="btn btn-success btn-sm"
            :disabled="publicando || ejecucionActual.estado === 'ARCHIVADO'"
            @click="publicarHorarios"
            title="Hacer oficial esta asignación para que los alumnos la vean en su portal"
          >
            <span v-if="publicando" class="spinner"></span>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            <span>Publicar Horarios Oficiales</span>
          </button>

          <span v-else class="published-tag">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            Horarios Oficiales Publicados
          </span>
        </div>
      </div>

      <!-- Métricas de la Ejecución Actual -->
      <div class="stats-grid">
        <div class="stat-card stat-card-indigo">
          <div class="stat-header">
            <span class="stat-label">Alumnos Procesados</span>
            <div class="stat-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
            </div>
          </div>
          <div class="stat-value">{{ ejecucionActual.resumen?.alumnos ?? 0 }}</div>
          <div class="stat-subtext">Estudiantes con solicitudes activas</div>
        </div>

        <div class="stat-card stat-success">
          <div class="stat-header">
            <span class="stat-label">Solicitudes Asignadas</span>
            <div class="stat-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            </div>
          </div>
          <div class="stat-value text-success">
            {{ ejecucionActual.resumen?.asignadas ?? 0 }}
          </div>
          <div class="stat-subtext">
            {{ porcentajeAsignado }}% de satisfacción de demanda
          </div>
        </div>

        <div class="stat-card stat-warning">
          <div class="stat-header">
            <span class="stat-label">Solicitudes Pendientes</span>
            <div class="stat-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            </div>
          </div>
          <div class="stat-value text-warning">
            {{ ejecucionActual.resumen?.pendientes ?? 0 }}
          </div>
          <div class="stat-subtext">Sin cupo, cruce o prerrequisito</div>
        </div>
      </div>

      <!-- Tabla de Asignaciones y Resultados -->
      <div class="card">
        <div class="card-header results-card-header">
          <h2 class="card-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
            Auditoría de Asignaciones ({{ resultadosFiltrados.length }} registros)
          </h2>
          <div class="results-quick-stats">
            <span class="badge badge-success">✓ {{ totalAsignadasFiltradas }} Asignadas</span>
            <span class="badge badge-warning">⚠ {{ totalPendientesFiltradas }} Pendientes</span>
          </div>
        </div>

        <div class="card-body">
          <!-- Filtros de Búsqueda -->
          <div class="filter-bar">
            <div class="search-input-wrapper">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input
                v-model="busquedaTexto"
                type="text"
                class="form-input"
                placeholder="Buscar por matrícula, clave o nombre de materia…"
              />
            </div>

            <div class="filter-group">
              <select v-model="filtroEstado" class="form-select filter-select">
                <option value="TODOS">Todos los estados</option>
                <option value="ASIGNADA">Solo Asignadas</option>
                <option value="PENDIENTE">Solo Pendientes</option>
              </select>

              <select v-model="filtroMotivo" class="form-select filter-select">
                <option value="TODOS">Todos los motivos</option>
                <option value="SIN_CUPO">Sin Cupo</option>
                <option value="CONFLICTO_HORARIO">Conflicto de Horario</option>
                <option value="PRERREQUISITOS">Faltan Prerrequisitos</option>
                <option value="SIN_GRUPO">Sin Grupos Abiertos</option>
                <option value="YA_APROBADA">Ya Acreditada</option>
                <option value="PLAN_INCORRECTO">Plan Incorrecto</option>
              </select>
            </div>
          </div>

          <!-- Tabla de Resultados -->
          <div class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Matrícula</th>
                  <th>Materia</th>
                  <th>Prioridad / Pref</th>
                  <th>Grupo</th>
                  <th>Profesor</th>
                  <th>Horario</th>
                  <th>Estado</th>
                  <th>Explicación Institucional</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="resultadosFiltrados.length === 0">
                  <td colspan="8" class="text-center" style="padding: 2.5rem; color: var(--text-muted);">
                    No se encontraron resultados con los filtros actuales.
                  </td>
                </tr>

                <tr
                  v-for="(row, idx) in resultadosFiltrados"
                  :key="idx"
                  :class="{ 'row-pending': row.estado === 'PENDIENTE' }"
                >
                  <td class="font-mono font-bold">
                    {{ row.matricula || row.detalle?.matricula || `Alumno #${row.alumno}` }}
                  </td>
                  <td>
                    <strong>{{ row.detalle?.nombre_materia || row.clave_materia }}</strong>
                    <div class="text-muted font-mono text-xs">{{ row.clave_materia }}</div>
                  </td>
                  <td>
                    <div class="pref-pills">
                      <span class="badge badge-mini badge-neutral" title="Prioridad institucional de la solicitud">
                        P{{ row.detalle?.prioridad_institucional ?? '—' }}
                      </span>
                      <span class="badge badge-mini badge-indigo" title="Preferencia del alumno">
                        #{{ row.detalle?.preferencia ?? '—' }}
                      </span>
                    </div>
                  </td>
                  <td>
                    <span v-if="row.detalle?.grupo" class="badge badge-indigo">
                      {{ row.detalle.grupo }}
                    </span>
                    <span v-else class="text-muted">—</span>
                  </td>
                  <td class="text-sm">
                    {{ row.detalle?.profesor || '—' }}
                  </td>
                  <td class="text-sm">
                    <span v-if="row.detalle?.horarios?.length">
                      {{ formatearHorarios(row.detalle.horarios) }}
                    </span>
                    <span v-else class="text-muted">—</span>
                  </td>
                  <td>
                    <span
                      class="badge"
                      :class="row.estado === 'ASIGNADA' ? 'badge-success' : 'badge-warning'"
                    >
                      {{ row.estado }}
                    </span>
                  </td>
                  <td class="text-sm">
                    <div v-if="row.motivo" class="motivo-badge-wrap">
                      <span class="badge badge-danger text-xs">{{ row.motivo }}</span>
                    </div>
                    <span class="text-muted">
                      {{ row.detalle?.explicacion || (row.estado === 'ASIGNADA' ? 'Asignada con éxito' : row.motivo) }}
                    </span>
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
import { useNotificationStore } from '../../../stores/notification';

const notifStore = useNotificationStore();

const ejecuciones = ref([]);
const ejecucionActual = ref(null);
const resultados = ref([]);

const cargandoLista = ref(false);
const cargandoDetalle = ref(false);
const generando = ref(false);
const publicando = ref(false);
const descargandoCsv = ref(false);
const errorMsg = ref(null);

const busquedaTexto = ref('');
const filtroEstado = ref('TODOS');
const filtroMotivo = ref('TODOS');

function formatearFecha(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' });
}

function formatearFechaCompleta(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });
}

function minutosAHora(minutos) {
  const h = Math.floor(minutos / 60);
  const m = minutos % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

function formatearHorarios(horarios = []) {
  return horarios
    .map((h) => `${h.dia.slice(0, 3)} ${minutosAHora(h.inicio)}-${minutosAHora(h.fin)}`)
    .join(', ');
}

const porcentajeAsignado = computed(() => {
  const res = ejecucionActual.value?.resumen;
  if (!res) return 0;
  const total = (res.asignadas || 0) + (res.pendientes || 0);
  if (!total) return 0;
  return Math.round(((res.asignadas || 0) / total) * 100);
});

const resultadosFiltrados = computed(() => {
  const q = busquedaTexto.value.trim().toLowerCase();
  const estado = filtroEstado.value;
  const motivo = filtroMotivo.value;

  return resultados.value.filter((r) => {
    // Filtro por Estado
    if (estado !== 'TODOS' && r.estado !== estado) return false;

    // Filtro por Motivo
    if (motivo !== 'TODOS' && r.motivo !== motivo) return false;

    // Búsqueda por texto
    if (!q) return true;
    const matricula = (r.matricula || r.detalle?.matricula || '').toLowerCase();
    const clave = (r.clave_materia || r.detalle?.clave_materia || '').toLowerCase();
    const nombre = (r.detalle?.nombre_materia || '').toLowerCase();
    const profesor = (r.detalle?.profesor || '').toLowerCase();

    return matricula.includes(q) || clave.includes(q) || nombre.includes(q) || profesor.includes(q);
  });
});

const totalAsignadasFiltradas = computed(
  () => resultadosFiltrados.value.filter((r) => r.estado === 'ASIGNADA').length,
);

const totalPendientesFiltradas = computed(
  () => resultadosFiltrados.value.filter((r) => r.estado === 'PENDIENTE').length,
);

async function cargarEjecuciones(seleccionarPrimera = true) {
  cargandoLista.value = true;
  errorMsg.value = null;
  try {
    const { data } = await api.get('/demo/asignaciones/');
    ejecuciones.value = Array.isArray(data) ? data : [];
    if (seleccionarPrimera && ejecuciones.value.length > 0) {
      await seleccionarEjecucion(ejecuciones.value[0].id);
    }
  } catch (err) {
    errorMsg.value = obtenerMensajeError(err);
  } finally {
    cargandoLista.value = false;
  }
}

async function seleccionarEjecucion(id) {
  cargandoDetalle.value = true;
  errorMsg.value = null;
  try {
    const { data } = await api.get(`/demo/asignaciones/${id}/`);
    ejecucionActual.value = data;
    resultados.value = data.resultados || [];
  } catch (err) {
    errorMsg.value = obtenerMensajeError(err);
  } finally {
    cargandoDetalle.value = false;
  }
}

async function ejecutarGeneracion() {
  generando.value = true;
  errorMsg.value = null;
  try {
    // POST demo/asignaciones/generar/ con cuerpo {}
    const { data } = await api.post('/demo/asignaciones/generar/', {});
    notifStore.success(`Ejecución #${data.id} generada en estado BORRADOR con éxito.`);
    await cargarEjecuciones(false);
    await seleccionarEjecucion(data.id);
  } catch (err) {
    errorMsg.value = obtenerMensajeError(err);
    notifStore.error(`Error al generar asignación: ${errorMsg.value}`);
  } finally {
    generando.value = false;
  }
}

async function publicarHorarios() {
  if (!ejecucionActual.value) return;
  publicando.value = true;
  errorMsg.value = null;
  try {
    const id = ejecucionActual.value.id;
    const { data } = await api.post(`/demo/asignaciones/${id}/publicar/`, {});
    ejecucionActual.value.estado = 'PUBLICADO';
    notifStore.success(`¡Horarios de la Ejecución #${id} publicados oficialmente para los alumnos!`);
    await cargarEjecuciones(false);
  } catch (err) {
    errorMsg.value = obtenerMensajeError(err);
    notifStore.error(`No se pudo publicar: ${errorMsg.value}`);
  } finally {
    publicando.value = false;
  }
}

async function descargarCsv() {
  if (!ejecucionActual.value) return;
  descargandoCsv.value = true;
  try {
    const id = ejecucionActual.value.id;
    const resp = await api.get(`/demo/asignaciones/${id}/csv/`, {
      responseType: 'blob',
    });
    const blob = new Blob([resp.data], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `asignaciones-${id}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    notifStore.success(`Archivo asignaciones-${id}.csv descargado correctamente`);
  } catch (err) {
    notifStore.error('Error al descargar el archivo CSV');
  } finally {
    descargandoCsv.value = false;
  }
}

onMounted(() => {
  cargarEjecuciones(true);
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

/* Selector de ejecuciones */
.runs-selector-card {
  padding: 1rem 1.25rem;
  margin-bottom: 1.5rem;
}

.runs-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.runs-label {
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-main);
}

.runs-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.runs-scroll {
  display: flex;
  gap: 0.75rem;
  overflow-x: auto;
  padding-bottom: 0.25rem;
}

.run-chip-btn {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.6rem 0.85rem;
  min-width: 140px;
  text-align: left;
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.run-chip-btn:hover {
  background: var(--bg-card);
  border-color: var(--primary-border);
}

.run-chip-btn.run-selected {
  background: var(--bg-card);
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary-light);
}

.run-chip-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.run-id {
  font-weight: 800;
  font-size: 0.95rem;
  color: var(--text-main);
}

.run-chip-meta {
  font-size: 0.725rem;
  color: var(--text-muted);
}

.run-chip-stats {
  display: flex;
  gap: 0.5rem;
  font-size: 0.725rem;
  font-weight: 600;
  margin-top: 0.15rem;
}

/* Banner de la Ejecución Actual */
.run-banner-card {
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.run-banner-badge {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  margin-bottom: 0.35rem;
}

.run-banner-id {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--text-main);
}

.run-banner-date {
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin-bottom: 0.25rem;
}

.run-policy-info {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.run-banner-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.published-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--success);
  font-weight: 700;
  font-size: 0.875rem;
  background-color: var(--success-bg);
  border: 1px solid var(--success-border);
  padding: 0.4rem 0.85rem;
  border-radius: var(--radius-sm);
}

/* Resultados Header */
.results-card-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.results-quick-stats {
  display: flex;
  gap: 0.5rem;
}

.filter-group {
  display: flex;
  gap: 0.65rem;
  flex-wrap: wrap;
}

.filter-select {
  width: auto;
  min-width: 170px;
}

.row-pending {
  background-color: var(--warning-bg);
}

.pref-pills {
  display: flex;
  gap: 0.35rem;
}

.motivo-badge-wrap {
  margin-bottom: 0.2rem;
}

.font-mono {
  font-family: 'JetBrains Mono', monospace;
}

.font-bold {
  font-weight: 700;
}

.text-xs {
  font-size: 0.725rem;
}

.text-sm {
  font-size: 0.8125rem;
}

.text-success {
  color: var(--success);
}

.text-warning {
  color: var(--warning);
}

.text-muted {
  color: var(--text-muted);
}

.text-center {
  text-align: center;
}
</style>
