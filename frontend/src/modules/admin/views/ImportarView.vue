<template>
  <div class="importar-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Carga Masiva e Importación CSV</h1>
        <p class="page-subtitle">
          Validación sintáctica y relacional estricta, upsert transaccional de catálogos y matrículas
        </p>
      </div>
      <div class="header-actions">
        <button
          type="button"
          class="btn btn-secondary btn-sm"
          @click="cargarDatosDeMuestra"
          title="Carga datos sintéticos válidos para probar la importación en 1 clic"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
          Cargar plantilla demo
        </button>
        <button
          type="button"
          class="btn btn-outline btn-sm"
          @click="limpiarTodo"
        >
          Limpiar campos
        </button>
      </div>
    </div>

    <!-- Feedback de Éxito / Errores de Validación -->
    <div v-if="resultadoImportacion?.importado" class="alert alert-success" role="alert">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
      <div>
        <strong>¡Importación completada con éxito!</strong>
        <div>
          Se importaron transaccionalmente:
          <span v-for="(cant, tipo) in resultadoImportacion.filas" :key="tipo" class="chip-count">
            {{ cant }} {{ tipo }}
          </span>
        </div>
      </div>
    </div>

    <div v-if="resultadoValidacion && resultadoValidacion.valido && !resultadoImportacion?.importado" class="alert alert-success" role="alert">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
      <div>
        <strong>Validación Exitosa</strong>: Todos los registros cumplen con las reglas institucionales.
        <div>
          Filas válidas detectadas:
          <span v-for="(cant, tipo) in resultadoValidacion.filas" :key="tipo" class="chip-count">
            {{ cant }} {{ tipo }}
          </span>
        </div>
      </div>
    </div>

    <div v-if="listaErrores.length > 0" class="alert alert-danger" role="alert">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      <div>
        <strong>Se encontraron {{ listaErrores.length }} inconsistencia(s) en los archivos CSV.</strong>
        <p class="text-xs">Revisa la tabla de auditoría al final de la página para corregir los campos señalados.</p>
      </div>
    </div>

    <div v-if="errorGenerico" class="alert alert-danger" role="alert">
      {{ errorGenerico }}
    </div>

    <!-- Navegación por Pestañas de Archivos -->
    <div class="tabs-nav">
      <button
        v-for="f in tiposArchivo"
        :key="f.clave"
        type="button"
        class="tab-btn"
        :class="{ active: tabActivo === f.clave }"
        @click="tabActivo = f.clave"
      >
        <span class="tab-title">{{ f.titulo }}</span>
        <span v-if="archivos[f.clave].trim()" class="tab-badge-filled">✓ cargado</span>
      </button>
    </div>

    <!-- Editor / Carga del Archivo Seleccionado -->
    <div class="card file-editor-card">
      <div class="card-header file-card-header">
        <div>
          <h2 class="card-title">{{ infoTabActivo.titulo }}</h2>
          <p class="text-muted text-xs">
            Encabezados requeridos: <code class="header-code">{{ infoTabActivo.encabezados }}</code>
          </p>
        </div>
        <div class="file-card-actions">
          <label class="btn btn-secondary btn-sm file-upload-label">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            <span>Subir .csv</span>
            <input
              type="file"
              accept=".csv,text/csv,text/plain"
              class="hidden-file-input"
              @change="(e) => handleFileUpload(e, tabActivo)"
            />
          </label>
          <button
            type="button"
            class="btn btn-outline btn-sm"
            @click="archivos[tabActivo] = ''"
          >
            Limpiar este archivo
          </button>
        </div>
      </div>

      <div class="card-body">
        <textarea
          v-model="archivos[tabActivo]"
          rows="10"
          class="form-textarea font-mono text-sm csv-textarea"
          :placeholder="`Pega aquí el contenido CSV o usa el botón 'Subir .csv'...\nEncabezados: ${infoTabActivo.encabezados}`"
        ></textarea>

        <div class="csv-meta-info">
          <span>Líneas: {{ contarLineas(archivos[tabActivo]) }}</span>
          <span>Tamaño: {{ (new Blob([archivos[tabActivo]]).size / 1024).toFixed(1) }} KB</span>
        </div>
      </div>
    </div>

    <!-- Barra de Acciones de Validación y Confirmación -->
    <div class="actions-dock card">
      <div class="actions-dock-left">
        <span class="text-sm font-semibold">
          Archivos listos para enviar: {{ totalArchivosConContenido }} de 5
        </span>
      </div>

      <div class="actions-dock-right">
        <!-- Paso 1: Validar -->
        <button
          type="button"
          class="btn btn-secondary btn-lg"
          :disabled="validando || confirmando || totalArchivosConContenido === 0"
          @click="ejecutarValidacion"
        >
          <span v-if="validando" class="spinner spinner-primary"></span>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 14 14"/></svg>
          <span>{{ validando ? 'Validando…' : '1. Validar CSVs' }}</span>
        </button>

        <!-- Paso 2: Confirmar -->
        <button
          type="button"
          class="btn btn-primary btn-lg"
          :disabled="confirmando || validando || totalArchivosConContenido === 0"
          @click="ejecutarConfirmacion"
        >
          <span v-if="confirmando" class="spinner"></span>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
          <span>{{ confirmando ? 'Confirmando importación…' : '2. Confirmar e Importar' }}</span>
        </button>
      </div>
    </div>

    <!-- Tabla Detallada de Errores de CSV si existen -->
    <div v-if="listaErrores.length > 0" class="card errors-card">
      <div class="card-header bg-danger-subtle">
        <h2 class="card-title text-danger">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          Detalle de Inconsistencias Detectadas ({{ listaErrores.length }})
        </h2>
      </div>

      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Archivo</th>
              <th>Fila</th>
              <th>Campo</th>
              <th>Mensaje de Error</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(err, idx) in listaErrores" :key="idx">
              <td>
                <span class="badge badge-indigo">{{ err.archivo }}</span>
              </td>
              <td class="font-mono font-bold">{{ err.fila ?? '—' }}</td>
              <td>
                <code class="text-xs font-bold">{{ err.campo || '—' }}</code>
              </td>
              <td class="text-danger font-medium">{{ err.mensaje }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import api, { obtenerMensajeError } from '../../../api';
import { useNotificationStore } from '../../../stores/notification';

const notifStore = useNotificationStore();

const tiposArchivo = [
  { clave: 'planes', titulo: 'Planes de Estudio', encabezados: 'nombre,descripcion' },
  { clave: 'materias', titulo: 'Materias', encabezados: 'plan,clave,nombre,creditos,semestre,prerrequisitos' },
  { clave: 'alumnos', titulo: 'Alumnos', encabezados: 'matricula,nombre,apellido_paterno,apellido_materno,plan,aprobadas,password' },
  { clave: 'grupos', titulo: 'Grupos y Horarios', encabezados: 'materia,clave,profesor,cupo,horarios' },
  { clave: 'solicitudes', titulo: 'Solicitudes', encabezados: 'matricula,materia,preferencia,prioridad_institucional' },
];

const tabActivo = ref('planes');

const archivos = ref({
  planes: '',
  materias: '',
  alumnos: '',
  grupos: '',
  solicitudes: '',
});

const validando = ref(false);
const confirmando = ref(false);
const errorGenerico = ref(null);
const resultadoValidacion = ref(null);
const resultadoImportacion = ref(null);
const listaErrores = ref([]);

const infoTabActivo = computed(
  () => tiposArchivo.find((t) => t.clave === tabActivo.value) || tiposArchivo[0],
);

const totalArchivosConContenido = computed(() => {
  return Object.values(archivos.value).filter((txt) => txt.trim().length > 0).length;
});

function contarLineas(texto) {
  if (!texto || !texto.trim()) return 0;
  return texto.trim().split('\n').length;
}

function handleFileUpload(event, clave) {
  const file = event.target.files?.[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    archivos.value[clave] = e.target.result;
    notifStore.info(`Archivo cargado en ${clave}: ${file.name}`);
  };
  reader.readAsText(file);
}

function limpiarTodo() {
  archivos.value = {
    planes: '',
    materias: '',
    alumnos: '',
    grupos: '',
    solicitudes: '',
  };
  resultadoValidacion.value = null;
  resultadoImportacion.value = null;
  listaErrores.value = [];
  errorGenerico.value = null;
}

function cargarDatosDeMuestra() {
  archivos.value = {
    planes: `nombre,descripcion
Informática,Plan ficticio de informática
Gestión,Plan ficticio de gestión`,

    materias: `plan,clave,nombre,creditos,semestre,prerrequisitos
Informática,INF1,Introducción,6,1,
Informática,INF2,Datos,6,1,INF1
Informática,INF3,Álgebra,6,1,
Informática,INF4,Redes,6,1,
Informática,INF5,Taller,6,1,INF3
Informática,INF6,Optativa,6,1,
Gestión,GES1,Introducción,6,1,
Gestión,GES2,Datos,6,1,GES1
Gestión,GES3,Álgebra,6,1,
Gestión,GES4,Redes,6,1,
Gestión,GES5,Taller,6,1,GES3
Gestión,GES6,Optativa,6,1,`,

    alumnos: `matricula,nombre,apellido_paterno,apellido_materno,plan,aprobadas,password
D001,Alumno ficticio 001,Demo,Local,Informática,INF1,DemoLocal2026!
D002,Alumno ficticio 002,Demo,Local,Gestión,,DemoLocal2026!
D003,Alumno ficticio 003,Demo,Local,Informática,,DemoLocal2026!`,

    grupos: `materia,clave,profesor,cupo,horarios
INF1,G1,Profesor ficticio INF1-1,20,Viernes:08:00-10:00
INF1,G2,Profesor ficticio INF1-2,20,Viernes:10:00-12:00
INF2,G1,Profesor ficticio INF2-1,20,Lunes:08:00-10:00
INF2,G2,Profesor ficticio INF2-2,20,Lunes:10:00-12:00
INF3,G1,Profesor ficticio INF3-1,20,Martes:08:00-10:00
INF3,G2,Profesor ficticio INF3-2,20,Martes:10:00-12:00
INF4,G1,Profesor ficticio INF4-1,20,Lunes:08:00-10:00
INF4,G2,Profesor ficticio INF4-2,20,Lunes:10:00-12:00
INF6,G1,Profesor ficticio INF6-1,20,Jueves:08:00-10:00
INF6,G2,Profesor ficticio INF6-2,20,Jueves:10:00-12:00
GES1,G1,Profesor ficticio GES1-1,20,Viernes:08:00-10:00
GES2,G1,Profesor ficticio GES2-1,20,Lunes:08:00-10:00
GES3,G1,Profesor ficticio GES3-1,20,Martes:08:00-10:00
GES4,G1,Profesor ficticio GES4-1,20,Lunes:08:00-10:00
GES6,G1,Profesor ficticio GES6-1,20,Jueves:08:00-10:00`,

    solicitudes: `matricula,materia,preferencia,prioridad_institucional
D001,INF2,1,1
D001,INF3,2,1
D001,INF4,3,1
D001,INF6,4,1
D002,GES2,1,2
D002,GES3,2,2
D002,GES4,3,2
D002,GES6,4,2
D003,INF2,1,0
D003,INF3,2,0`,
  };

  resultadoValidacion.value = null;
  resultadoImportacion.value = null;
  listaErrores.value = [];
  notifStore.success('Plantilla de datos cargada. Haz clic en "1. Validar CSVs".');
}

function filtrarArchivosParaEnvio() {
  const obj = {};
  for (const [k, v] of Object.entries(archivos.value)) {
    if (v.trim()) {
      obj[k] = v.trim();
    }
  }
  return obj;
}

async function ejecutarValidacion() {
  const payloadArchivos = filtrarArchivosParaEnvio();
  if (Object.keys(payloadArchivos).length === 0) {
    notifStore.warning('Por favor carga al menos un archivo CSV con datos.');
    return;
  }

  validando.value = true;
  errorGenerico.value = null;
  listaErrores.value = [];
  resultadoValidacion.value = null;

  try {
    const { data } = await api.post('/demo/importaciones/validar/', {
      archivos: payloadArchivos,
    });
    resultadoValidacion.value = data;
    listaErrores.value = data.errores || [];
    if (data.valido) {
      notifStore.success('Validación exitosa: los archivos CSV son consistentes.');
    }
  } catch (err) {
    const dataErr = err.response?.data;
    if (dataErr?.errores) {
      listaErrores.value = dataErr.errores;
      resultadoValidacion.value = dataErr;
    } else {
      errorGenerico.value = obtenerMensajeError(err);
    }
    notifStore.error('Se detectaron inconsistencias en la validación.');
  } finally {
    validando.value = false;
  }
}

async function ejecutarConfirmacion() {
  const payloadArchivos = filtrarArchivosParaEnvio();
  if (Object.keys(payloadArchivos).length === 0) {
    notifStore.warning('Por favor carga al menos un archivo CSV con datos.');
    return;
  }

  confirmando.value = true;
  errorGenerico.value = null;
  listaErrores.value = [];

  try {
    const { data } = await api.post('/demo/importaciones/confirmar/', {
      archivos: payloadArchivos,
    });
    resultadoImportacion.value = data;
    resultadoValidacion.value = data;
    listaErrores.value = data.errores || [];
    notifStore.success('¡Importación completada y guardada en la base de datos!');
  } catch (err) {
    const dataErr = err.response?.data;
    if (dataErr?.errores) {
      listaErrores.value = dataErr.errores;
      resultadoValidacion.value = dataErr;
    } else {
      errorGenerico.value = obtenerMensajeError(err);
    }
    notifStore.error('No se pudo confirmar la importación.');
  } finally {
    confirmando.value = false;
  }
}
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

.chip-count {
  display: inline-block;
  background: rgba(0, 0, 0, 0.08);
  padding: 0.1rem 0.5rem;
  border-radius: var(--radius-sm);
  font-weight: 700;
  margin: 0 0.25rem;
}

/* Tabs */
.tabs-nav {
  display: flex;
  gap: 0.35rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: -1px;
  overflow-x: auto;
}

.tab-btn {
  background: transparent;
  border: 1px solid transparent;
  border-bottom: none;
  padding: 0.75rem 1.15rem;
  font-family: inherit;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.tab-btn:hover {
  color: var(--text-main);
  background-color: var(--bg-surface);
}

.tab-btn.active {
  background: var(--bg-card);
  border-color: var(--border);
  border-bottom-color: var(--bg-card);
  color: var(--primary);
}

.tab-badge-filled {
  font-size: 0.7rem;
  color: var(--success);
  font-weight: 700;
}

/* Editor */
.file-editor-card {
  border-top-left-radius: 0;
  margin-bottom: 1.5rem;
}

.file-card-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.header-code {
  background-color: var(--bg-surface);
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  color: var(--primary);
}

.file-card-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.file-upload-label {
  cursor: pointer;
}

.hidden-file-input {
  display: none;
}

.csv-textarea {
  width: 100%;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.825rem;
  line-height: 1.6;
  white-space: pre;
  resize: vertical;
}

.csv-meta-info {
  display: flex;
  gap: 1.25rem;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.5rem;
}

/* Actions dock */
.actions-dock {
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.5rem;
  background-color: #ffffff;
}

.actions-dock-right {
  display: flex;
  gap: 0.85rem;
}

/* Errors card */
.errors-card {
  margin-top: 1.5rem;
}

.bg-danger-subtle {
  background-color: var(--danger-bg);
}

.font-mono {
  font-family: 'JetBrains Mono', monospace;
}

.font-bold {
  font-weight: 700;
}

.font-semibold {
  font-weight: 600;
}

.font-medium {
  font-weight: 500;
}

.text-xs {
  font-size: 0.75rem;
}

.text-sm {
  font-size: 0.875rem;
}

.text-danger {
  color: var(--danger);
}

.text-muted {
  color: var(--text-muted);
}
</style>
