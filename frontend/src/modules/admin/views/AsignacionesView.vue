<template>
  <div class="asignaciones-page admin-view">
    <header class="ui-page-header">
      <div>
        <h1 class="ui-large-title">Generación y publicación de horarios</h1>
        <p class="ui-page-subtitle">
          Asigna las solicitudes de los alumnos respetando prioridades, cupos y cruces de horario
        </p>
      </div>
      <div class="ui-page-actions">
        <button
          type="button"
          class="btn btn-primary"
          :disabled="generando || cargandoLista"
          @click="ejecutarGeneracion"
        >
          <span v-if="generando" class="spinner" aria-hidden="true"></span>
          <AppIcon v-else name="zap" :size="16" />
          <span>{{ generando ? 'Generando asignación…' : 'Generar nueva asignación' }}</span>
        </button>
      </div>
    </header>

    <ErrorBanner
      v-if="errorMsg"
      titulo="Algo salió mal con las asignaciones"
      :mensaje="errorMsg"
      :cargando="cargandoLista || cargandoDetalle"
      @reintentar="cargarEjecuciones(true)"
    />

    <!-- Carga inicial: esqueleto (T7) -->
    <div v-if="cargandoLista && !ejecuciones.length" class="ui-grouped" aria-busy="true" aria-label="Cargando ejecuciones">
      <div v-for="n in 3" :key="n" class="ui-row">
        <div class="ui-row-main">
          <div class="skeleton ui-skel-line" style="width: 30%"></div>
          <div class="skeleton ui-skel-line" style="width: 55%"></div>
        </div>
      </div>
    </div>

    <!-- Sin ejecuciones -->
    <div v-else-if="!ejecuciones.length && !errorMsg" class="card">
      <div class="ui-empty">
        <div class="ui-empty-icon"><AppIcon name="zap" :size="24" /></div>
        <h2 class="ui-empty-title">Aún no hay asignaciones</h2>
        <p class="ui-empty-text">
          El motor procesará todas las solicitudes vigentes y creará una propuesta que podrás revisar antes de publicarla.
        </p>
        <button type="button" class="btn btn-primary" :disabled="generando" @click="ejecutarGeneracion">
          <span v-if="generando" class="spinner" aria-hidden="true"></span>
          Generar primera asignación
        </button>
      </div>
    </div>

    <template v-else-if="ejecuciones.length">
      <!-- Historial de ejecuciones como lista compacta (H1) -->
      <section class="runs-section">
        <h2 class="ui-section-title">
          Historial de ejecuciones
          <span class="ui-section-count">{{ ejecuciones.length }}</span>
        </h2>
        <div class="ui-grouped runs-list" role="listbox" aria-label="Ejecuciones">
          <button
            v-for="run in ejecuciones"
            :key="run.id"
            type="button"
            role="option"
            class="ui-row run-row"
            :class="{ 'is-selected': ejecucionActual?.id === run.id }"
            :aria-selected="ejecucionActual?.id === run.id ? 'true' : 'false'"
            @click="seleccionarEjecucion(run.id)"
          >
            <div class="ui-row-main">
              <div class="ui-row-title">Ejecución #{{ run.id }}</div>
              <div class="ui-row-subtitle ui-num">
                {{ formatearFechaCompleta(run.created_at) }}
                <template v-if="run.resumen">
                  · {{ run.resumen.asignadas || 0 }} asignadas · {{ run.resumen.pendientes || 0 }} pendientes
                </template>
              </div>
            </div>
            <span class="estado-label" :class="`estado-${(run.estado || '').toLowerCase()}`">
              <span class="estado-dot" aria-hidden="true"></span>
              {{ textoEstadoEjecucion(run.estado) }}
            </span>
            <AppIcon v-if="ejecucionActual?.id === run.id" name="check" :size="16" class="run-check" />
          </button>
        </div>
      </section>

      <!-- Detalle de la ejecución seleccionada -->
      <div v-if="cargandoDetalle" class="card" aria-busy="true" aria-label="Cargando resultados">
        <div class="card-body">
          <div class="skeleton ui-skel-title"></div>
          <div v-for="n in 5" :key="n" class="skeleton ui-skel-line"></div>
        </div>
      </div>

      <div v-else-if="ejecucionActual" class="run-detail">
        <section class="card run-banner">
          <div class="run-banner-left">
            <div class="run-banner-title">
              <h2>Ejecución #{{ ejecucionActual.id }}</h2>
              <span class="estado-label" :class="`estado-${(ejecucionActual.estado || '').toLowerCase()}`">
                <span class="estado-dot" aria-hidden="true"></span>
                {{ textoEstadoEjecucion(ejecucionActual.estado) }}
              </span>
            </div>
            <p class="run-banner-meta">
              Generada el {{ formatearFechaCompleta(ejecucionActual.created_at) }} ·
              Política {{ ejecucionActual.politica?.version || 'greedy-v1' }}
              (prioridad institucional, luego matrícula)
            </p>
          </div>

          <div class="run-banner-actions">
            <button
              type="button"
              class="btn btn-secondary btn-sm"
              :disabled="descargandoCsv"
              title="Descargar el reporte completo en CSV"
              @click="descargarCsv"
            >
              <span v-if="descargandoCsv" class="spinner spinner-primary" aria-hidden="true"></span>
              <AppIcon v-else name="download" :size="14" />
              <span>Exportar CSV</span>
            </button>

            <!-- H2: publicar sigue en verde y ahora pide confirmación -->
            <button
              v-if="ejecucionActual.estado !== 'PUBLICADO'"
              type="button"
              class="btn btn-success btn-sm"
              :disabled="publicando || ejecucionActual.estado === 'ARCHIVADO'"
              @click="confirmarPublicacionAbierta = true"
            >
              <span v-if="publicando" class="spinner" aria-hidden="true"></span>
              <AppIcon v-else name="check-circle" :size="14" />
              <span>Publicar horarios oficiales</span>
            </button>

            <span v-else class="published-tag">
              <AppIcon name="check" :size="16" :stroke-width="2.5" />
              Horarios oficiales publicados
            </span>
          </div>
        </section>

        <!-- Métricas con vidrio y barra de progreso (H3) -->
        <div class="stats-grid">
          <div class="stat-card glass-card">
            <div class="stat-header">
              <span class="stat-label">Alumnos procesados</span>
              <div class="stat-icon"><AppIcon name="users" :size="18" /></div>
            </div>
            <div class="stat-value ui-num">{{ ejecucionActual.resumen?.alumnos ?? 0 }}</div>
            <div class="stat-subtext">Con solicitudes activas</div>
          </div>

          <div class="stat-card glass-card stat-success">
            <div class="stat-header">
              <span class="stat-label">Solicitudes asignadas</span>
              <div class="stat-icon"><AppIcon name="check" :size="18" /></div>
            </div>
            <div class="stat-value text-success ui-num">{{ ejecucionActual.resumen?.asignadas ?? 0 }}</div>
            <div
              class="ui-progress satisfaccion-bar"
              role="progressbar"
              :aria-valuenow="porcentajeAsignado"
              aria-valuemin="0"
              aria-valuemax="100"
              aria-label="Satisfacción de la demanda"
            >
              <span :style="{ width: `${porcentajeAsignado}%` }"></span>
            </div>
            <div class="stat-subtext">{{ porcentajeAsignado }} % de la demanda satisfecha</div>
          </div>

          <div class="stat-card glass-card stat-warning">
            <div class="stat-header">
              <span class="stat-label">Solicitudes pendientes</span>
              <div class="stat-icon"><AppIcon name="warning" :size="18" /></div>
            </div>
            <div class="stat-value text-warning ui-num">{{ ejecucionActual.resumen?.pendientes ?? 0 }}</div>
            <div class="stat-subtext">Sin cupo, con cruce o sin prerrequisitos</div>
          </div>
        </div>

        <!-- Auditoría -->
        <section class="card">
          <div class="card-header results-header">
            <h2 class="card-title">
              <AppIcon name="select-list" />
              Auditoría de asignaciones
              <span class="ui-section-count">{{ resultadosFiltrados.length }} registros</span>
            </h2>
            <div class="results-quick-stats ui-num">
              <span class="quick-ok"><AppIcon name="check" :size="14" /> {{ totalAsignadasFiltradas }} asignadas</span>
              <span class="quick-pend"><AppIcon name="warning" :size="14" /> {{ totalPendientesFiltradas }} pendientes</span>
            </div>
          </div>

          <div class="card-body">
            <div class="filter-row">
              <div class="ui-search filter-search" role="search">
                <AppIcon name="search" :size="16" class="ui-search-icon" />
                <input
                  v-model="busquedaTexto"
                  type="search"
                  placeholder="Buscar por matrícula, clave, materia o profesor"
                  aria-label="Buscar en la auditoría"
                />
                <button
                  v-if="busquedaTexto"
                  type="button"
                  class="ui-search-clear"
                  aria-label="Borrar búsqueda"
                  @click="busquedaTexto = ''"
                >
                  <AppIcon name="x-circle" :size="16" />
                </button>
              </div>

              <!-- H6: estado como segmented control -->
              <div class="ui-segmented" role="radiogroup" aria-label="Filtrar por estado">
                <button
                  v-for="op in opcionesEstado"
                  :key="op.valor"
                  type="button"
                  role="radio"
                  :aria-checked="filtroEstado === op.valor ? 'true' : 'false'"
                  @click="filtroEstado = op.valor"
                >
                  {{ op.texto }}
                </button>
              </div>

              <select v-model="filtroMotivo" class="form-select filter-select" aria-label="Filtrar por motivo">
                <option value="TODOS">Todos los motivos</option>
                <option v-for="(texto, clave) in MOTIVOS" :key="clave" :value="clave">{{ texto }}</option>
              </select>
            </div>

            <div class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Matrícula</th>
                    <th>Materia</th>
                    <th>Prioridad</th>
                    <th>Grupo</th>
                    <th>Profesor</th>
                    <th>Horario</th>
                    <th>Estado</th>
                    <th>Detalle</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="resultadosFiltrados.length === 0">
                    <td colspan="8" class="empty-cell">No hay resultados con los filtros actuales.</td>
                  </tr>

                  <tr
                    v-for="(row, idx) in resultadosFiltrados"
                    :key="idx"
                    :class="{ 'row-pending': row.estado === 'PENDIENTE' }"
                  >
                    <td class="cell-strong ui-num">
                      {{ row.matricula || row.detalle?.matricula || `Alumno #${row.alumno}` }}
                    </td>
                    <td>
                      <div class="cell-strong">{{ row.detalle?.nombre_materia || row.clave_materia }}</div>
                      <div class="cell-sub ui-code">{{ row.clave_materia }}</div>
                    </td>
                    <!-- H4: prioridad y preferencia en texto claro -->
                    <td class="cell-sub ui-num cell-nowrap">
                      Prioridad {{ row.detalle?.prioridad_institucional ?? '—' }}<br />
                      Preferencia {{ row.detalle?.preferencia ?? '—' }}
                    </td>
                    <td>{{ row.detalle?.grupo || '—' }}</td>
                    <td class="cell-small">{{ row.detalle?.profesor || '—' }}</td>
                    <td class="cell-small ui-num cell-nowrap">
                      {{ row.detalle?.horarios?.length ? formatearHorarios(row.detalle.horarios) : '—' }}
                    </td>
                    <td>
                      <span class="estado-res" :class="row.estado === 'ASIGNADA' ? 'res-ok' : 'res-pend'">
                        <AppIcon :name="row.estado === 'ASIGNADA' ? 'check' : 'warning'" :size="13" />
                        {{ row.estado === 'ASIGNADA' ? 'Asignada' : 'Pendiente' }}
                      </span>
                    </td>
                    <!-- H5: motivo en texto humano; la explicación solo en pendientes -->
                    <td class="cell-small">
                      <template v-if="row.estado === 'PENDIENTE'">
                        <div class="motivo-text">{{ textoMotivo(row.motivo) }}</div>
                        <div v-if="row.detalle?.explicacion" class="cell-sub">{{ row.detalle.explicacion }}</div>
                      </template>
                      <span v-else class="cell-sub">—</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>
    </template>

    <!-- H2: confirmación antes de publicar -->
    <ConfirmSheet
      :abierto="confirmarPublicacionAbierta"
      titulo="¿Publicar horarios oficiales?"
      :descripcion="`Los alumnos verán de inmediato el horario de la ejecución #${ejecucionActual?.id ?? ''} en su portal.`"
      texto-confirmar="Publicar"
      variante="success"
      @cancelar="confirmarPublicacionAbierta = false"
      @confirmar="confirmarPublicacion"
    >
      <div class="ui-grouped sheet-resumen">
        <div class="ui-row">
          <span class="ui-row-label">Solicitudes asignadas</span>
          <span class="ui-row-value">{{ ejecucionActual?.resumen?.asignadas ?? 0 }}</span>
        </div>
        <div class="ui-row">
          <span class="ui-row-label">Solicitudes pendientes</span>
          <span class="ui-row-value">{{ ejecucionActual?.resumen?.pendientes ?? 0 }}</span>
        </div>
      </div>
    </ConfirmSheet>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import api, { obtenerMensajeError } from '../../../api';
import { useNotificationStore } from '../../../stores/notification';
import AppIcon from '../../../components/AppIcon.vue';
import ErrorBanner from '../../../components/ErrorBanner.vue';
import ConfirmSheet from '../../../components/ConfirmSheet.vue';

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
const confirmarPublicacionAbierta = ref(false);

const busquedaTexto = ref('');
const filtroEstado = ref('TODOS');
const filtroMotivo = ref('TODOS');

const opcionesEstado = [
  { valor: 'TODOS', texto: 'Todas' },
  { valor: 'ASIGNADA', texto: 'Asignadas' },
  { valor: 'PENDIENTE', texto: 'Pendientes' },
];

const MOTIVOS = {
  SIN_CUPO: 'Sin cupo',
  CONFLICTO_HORARIO: 'Cruce de horario',
  PRERREQUISITOS: 'Faltan prerrequisitos',
  SIN_GRUPO: 'Sin grupo disponible',
  YA_APROBADA: 'Ya acreditada',
  PLAN_INCORRECTO: 'No pertenece a su plan',
};

function textoMotivo(motivo) {
  return MOTIVOS[motivo] || motivo || 'Motivo no especificado';
}

function textoEstadoEjecucion(estado) {
  return { PUBLICADO: 'Publicado', BORRADOR: 'Borrador', ARCHIVADO: 'Archivado' }[estado] || estado;
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
    .map((h) => `${h.dia.slice(0, 3)} ${minutosAHora(h.inicio)}–${minutosAHora(h.fin)}`)
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
    if (estado !== 'TODOS' && r.estado !== estado) return false;
    if (motivo !== 'TODOS' && r.motivo !== motivo) return false;
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
    const { data } = await api.post('/demo/asignaciones/generar/', {});
    notifStore.success(`Ejecución #${data.id} generada como borrador.`);
    await cargarEjecuciones(false);
    await seleccionarEjecucion(data.id);
  } catch (err) {
    errorMsg.value = obtenerMensajeError(err);
    notifStore.error(`Error al generar asignación: ${errorMsg.value}`);
  } finally {
    generando.value = false;
  }
}

function confirmarPublicacion() {
  confirmarPublicacionAbierta.value = false;
  publicarHorarios();
}

async function publicarHorarios() {
  if (!ejecucionActual.value) return;
  publicando.value = true;
  errorMsg.value = null;
  try {
    const id = ejecucionActual.value.id;
    await api.post(`/demo/asignaciones/${id}/publicar/`, {});
    ejecucionActual.value.estado = 'PUBLICADO';
    notifStore.success(`Horarios de la ejecución #${id} publicados para los alumnos.`);
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
.asignaciones-page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.asignaciones-page > .ui-page-header {
  margin-bottom: 0.25rem;
}

/* Historial (H1) */
.runs-list {
  max-height: 260px;
  overflow-y: auto;
}

.run-row {
  width: 100%;
  border: none;
  background: transparent;
  font-family: inherit;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.run-row:hover {
  background-color: var(--row-hover);
}

.run-row.is-selected {
  background-color: var(--primary-light);
}

.run-row:focus-visible {
  outline: none;
  box-shadow: inset 0 0 0 2px var(--focus-ring);
}

.run-check {
  flex-shrink: 0;
  color: var(--accent-text);
}

/* Estado de ejecución: punto de color + texto */
.estado-label {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  flex-shrink: 0;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-muted);
}

.estado-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--text-light);
}

.estado-publicado { color: var(--success-text); }
.estado-publicado .estado-dot { background-color: var(--success); }
.estado-borrador { color: var(--accent-text); }
.estado-borrador .estado-dot { background-color: var(--accent-text); }

/* Detalle */
.run-detail {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.run-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.1rem 1.25rem;
}

.run-banner-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.run-banner-title h2 {
  font-size: 1.375rem;
  font-weight: 700;
}

.run-banner-meta {
  margin-top: 0.25rem;
  font-size: 0.875rem;
  color: var(--text-muted);
}

.run-banner-actions {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.published-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--success-text);
}

/* Métricas (H3) */
.stats-grid {
  margin-bottom: 0;
}

.text-success { color: var(--success); }
.text-warning { color: var(--warning); }

.satisfaccion-bar {
  margin-top: 0.6rem;
}

/* Auditoría */
.results-header .ui-section-count {
  margin-left: 0.25rem;
  font-size: 0.875rem;
}

.results-quick-stats {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
  font-weight: 600;
}

.quick-ok,
.quick-pend {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}

.quick-ok { color: var(--success-text); }
.quick-pend { color: var(--warning-text); }

.filter-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.filter-search {
  flex: 1 1 280px;
}

.filter-select {
  width: auto;
  min-width: 200px;
  height: 38px;
  padding-block: 0;
  border-radius: 10px;
  font-size: 0.9375rem;
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

.cell-small {
  font-size: 0.875rem;
}

.cell-nowrap {
  white-space: nowrap;
}

.row-pending {
  background-color: var(--warning-bg);
}

.estado-res {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.875rem;
  font-weight: 600;
  white-space: nowrap;
}

.res-ok { color: var(--success-text); }
.res-pend { color: var(--warning-text); }

.motivo-text {
  font-weight: 600;
  color: var(--warning-text);
}

.sheet-resumen {
  background-color: var(--bg-surface);
  border-color: transparent;
}
</style>
