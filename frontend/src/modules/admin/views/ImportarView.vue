<template>
  <div class="importar-page admin-view">
    <header class="ui-page-header">
      <div>
        <h1 class="ui-large-title">Importación masiva con CSV</h1>
        <p class="ui-page-subtitle">
          Valida tus archivos antes de guardarlos. Si algo falla, no se guarda nada a medias.
        </p>
      </div>
      <!-- I2: acciones agrupadas; limpiar se ve como acción destructiva -->
      <div class="ui-page-actions header-group">
        <button
          v-if="plantillaDemoDisponible"
          type="button"
          class="btn btn-secondary btn-sm"
          title="Carga datos de ejemplo válidos para probar la importación"
          @click="cargarDatosDeMuestra"
        >
          <AppIcon name="file-text" :size="14" />
          Cargar plantilla demo
        </button>
        <button type="button" class="btn btn-sm btn-destructive" @click="limpiarTodo">
          <AppIcon name="trash" :size="14" />
          Limpiar todo
        </button>
      </div>
    </header>

    <!-- Resultados -->
    <div v-if="resultadoImportacion?.importado" class="alert alert-success" role="status">
      <AppIcon name="check-circle" :size="20" />
      <div>
        <strong>Importación completada</strong>
        <div class="chips-line">
          Se guardaron:
          <span v-for="(cant, tipo) in resultadoImportacion.filas" :key="tipo" class="chip-count ui-num">
            {{ cant }} {{ tipo }}
          </span>
        </div>
      </div>
    </div>

    <div
      v-if="resultadoValidacion && resultadoValidacion.valido && !resultadoImportacion?.importado"
      class="alert alert-success"
      role="status"
    >
      <AppIcon name="check-circle" :size="20" />
      <div>
        <strong>Validación correcta.</strong> Todos los registros cumplen las reglas de la institución.
        <div class="chips-line">
          Filas válidas:
          <span v-for="(cant, tipo) in resultadoValidacion.filas" :key="tipo" class="chip-count ui-num">
            {{ cant }} {{ tipo }}
          </span>
        </div>
      </div>
    </div>

    <div v-if="listaErrores.length > 0" class="alert alert-danger" role="alert">
      <AppIcon name="alert" :size="20" />
      <div>
        <strong>
          Encontramos {{ listaErrores.length }}
          {{ listaErrores.length === 1 ? 'problema' : 'problemas' }} en los archivos.
        </strong>
        <div>Revisa el detalle al final de la página, corrige y vuelve a validar.</div>
      </div>
    </div>

    <ErrorBanner
      v-if="errorGenerico"
      titulo="No pudimos procesar los archivos"
      :mensaje="errorGenerico"
      :reintentable="false"
    />

    <!-- I1: selector de archivo como segmented control con indicador de cargado -->
    <div class="ui-segmented file-segmented" role="tablist" aria-label="Archivo CSV">
      <button
        v-for="f in tiposArchivo"
        :key="f.clave"
        type="button"
        role="tab"
        :aria-selected="tabActivo === f.clave ? 'true' : 'false'"
        :aria-checked="tabActivo === f.clave ? 'true' : 'false'"
        @click="tabActivo = f.clave"
      >
        <span
          class="file-dot"
          :class="{ 'is-filled': archivos[f.clave].trim() }"
          :title="archivos[f.clave].trim() ? 'Con datos' : 'Vacío'"
          aria-hidden="true"
        ></span>
        {{ tituloArchivo(f) }}
        <span v-if="archivos[f.clave].trim()" class="visually-hidden">(con datos)</span>
      </button>
    </div>

    <!-- Editor del archivo seleccionado -->
    <section class="card file-editor-card">
      <div class="card-header file-card-header">
        <div>
          <h2 class="card-title">{{ tituloArchivo(infoTabActivo) }}</h2>
          <p class="file-hint">
            Encabezados requeridos: <code class="header-code">{{ infoTabActivo.encabezados }}</code>
          </p>
        </div>
        <div class="file-card-actions">
          <label class="btn btn-secondary btn-sm file-upload-label">
            <AppIcon name="upload" :size="14" />
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
            class="btn btn-sm btn-destructive-plain"
            :disabled="!archivos[tabActivo].trim()"
            @click="archivos[tabActivo] = ''"
          >
            Vaciar este archivo
          </button>
        </div>
      </div>

      <div class="card-body">
        <textarea
          v-model="archivos[tabActivo]"
          rows="10"
          class="form-textarea csv-textarea"
          :aria-label="`Contenido CSV de ${tituloArchivo(infoTabActivo)}`"
          :placeholder="`Pega aquí el contenido CSV o usa «Subir .csv».\nEncabezados: ${infoTabActivo.encabezados}`"
        ></textarea>

        <div class="csv-meta-info ui-num">
          <span>{{ contarLineas(archivos[tabActivo]) }} líneas</span>
          <span>{{ tamanoKB(archivos[tabActivo]) }} KB</span>
        </div>
      </div>
    </section>

    <!-- I3: indicador de dos pasos con su estado -->
    <section class="card actions-dock">
      <ol class="steps" aria-label="Pasos de la importación">
        <li class="step" :class="`step-${estadoValidacion}`">
          <span class="step-badge" aria-hidden="true">
            <AppIcon v-if="estadoValidacion === 'hecho'" name="check" :size="14" :stroke-width="3" />
            <AppIcon v-else-if="estadoValidacion === 'error'" name="x" :size="14" :stroke-width="3" />
            <template v-else>1</template>
          </span>
          <div>
            <div class="step-title">Validar archivos</div>
            <div class="step-state">{{ textoEstadoPaso(estadoValidacion) }}</div>
          </div>
        </li>
        <li class="step-sep" aria-hidden="true"></li>
        <li class="step" :class="`step-${estadoImportacion}`">
          <span class="step-badge" aria-hidden="true">
            <AppIcon v-if="estadoImportacion === 'hecho'" name="check" :size="14" :stroke-width="3" />
            <template v-else>2</template>
          </span>
          <div>
            <div class="step-title">Confirmar e importar</div>
            <div class="step-state">{{ textoEstadoPaso(estadoImportacion) }}</div>
          </div>
        </li>
      </ol>

      <div class="dock-right">
        <span class="dock-count ui-num">{{ totalArchivosConContenido }} de 5 archivos con datos</span>
        <button
          type="button"
          class="btn btn-secondary"
          :disabled="validando || confirmando || totalArchivosConContenido === 0"
          @click="ejecutarValidacion"
        >
          <span v-if="validando" class="spinner spinner-primary" aria-hidden="true"></span>
          <AppIcon v-else name="file-check" :size="16" />
          <span>{{ validando ? 'Validando…' : 'Validar archivos' }}</span>
        </button>
        <button
          type="button"
          class="btn btn-primary"
          :disabled="confirmando || validando || totalArchivosConContenido === 0"
          @click="ejecutarConfirmacion"
        >
          <span v-if="confirmando" class="spinner" aria-hidden="true"></span>
          <AppIcon v-else name="save" :size="16" />
          <span>{{ confirmando ? 'Importando…' : 'Confirmar e importar' }}</span>
        </button>
      </div>
    </section>

    <!-- I4: errores agrupados por archivo -->
    <section v-if="listaErrores.length > 0" class="errors-section">
      <h2 class="ui-section-title">
        Problemas encontrados
        <span class="ui-section-count">{{ listaErrores.length }}</span>
      </h2>
      <div v-for="grupo in erroresPorArchivo" :key="grupo.archivo" class="error-group">
        <h3 class="error-group-title">
          <AppIcon name="file-text" :size="15" />
          {{ grupo.archivo }}
          <span class="ui-section-count">{{ grupo.errores.length }}</span>
        </h3>
        <div class="ui-grouped">
          <div v-for="(err, idx) in grupo.errores" :key="idx" class="ui-row error-row">
            <span class="error-fila ui-num">Fila {{ err.fila ?? '—' }}</span>
            <div class="ui-row-main">
              <div class="error-msg">{{ err.mensaje }}</div>
              <div v-if="err.campo" class="ui-row-subtitle">
                Campo <code class="ui-code campo-code">{{ err.campo }}</code>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import api, { obtenerMensajeError } from '../../../api';
import { useNotificationStore } from '../../../stores/notification';
import AppIcon from '../../../components/AppIcon.vue';
import ErrorBanner from '../../../components/ErrorBanner.vue';

const notifStore = useNotificationStore();
const timeoutImportacionMs = 300_000;

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

// Título con mayúscula solo al inicio ("Planes de Estudio" → "Planes de estudio")
function tituloArchivo(f) {
  const t = f?.titulo || '';
  return t.charAt(0) + t.slice(1).toLowerCase();
}

// I3: estado de cada paso a partir de los resultados existentes
const estadoValidacion = computed(() => {
  if (validando.value) return 'activo';
  if (resultadoImportacion.value?.importado) return 'hecho';
  if (listaErrores.value.length > 0) return 'error';
  if (resultadoValidacion.value?.valido) return 'hecho';
  return 'pendiente';
});

const estadoImportacion = computed(() => {
  if (confirmando.value) return 'activo';
  if (resultadoImportacion.value?.importado) return 'hecho';
  return 'pendiente';
});

function textoEstadoPaso(estado) {
  return {
    pendiente: 'Pendiente',
    activo: 'En curso…',
    hecho: 'Completado',
    error: 'Con problemas',
  }[estado];
}

// I4: errores agrupados por archivo
const erroresPorArchivo = computed(() => {
  const grupos = new Map();
  listaErrores.value.forEach((err) => {
    const archivo = err.archivo || 'General';
    if (!grupos.has(archivo)) grupos.set(archivo, []);
    grupos.get(archivo).push(err);
  });
  return [...grupos.entries()].map(([archivo, errores]) => ({ archivo, errores }));
});

function contarLineas(texto) {
  if (!texto || !texto.trim()) return 0;
  return texto.trim().split('\n').length;
}

/**
 * Calcula el tamaño legible (en KB) de un texto sin depender de APIs globales
 * como `Blob` dentro del render function, evitando que un fallo de render
 * deje la pantalla en blanco (pantalla negra).
 */
function tamanoKB(texto) {
  const valor = typeof texto === 'string' ? texto : '';
  return (valor.length / 1024).toFixed(1);
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

const plantillaDemoDisponible = import.meta.env.DEV
  && ['localhost', '127.0.0.1', '[::1]'].includes(window.location.hostname);

function cargarDatosDeMuestra() {
  if (!import.meta.env.DEV || !plantillaDemoDisponible) return;

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
  notifStore.success('Plantilla de datos cargada. Ahora pulsa «Validar archivos».');
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
  resultadoImportacion.value = null;

  try {
    const { data } = await api.post('/demo/importaciones/validar/', {
      archivos: payloadArchivos,
    }, { timeout: timeoutImportacionMs });
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
    notifStore.error(dataErr?.errores ? 'Se detectaron inconsistencias en la validación.' : 'No se pudo completar la validación.');
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
  resultadoValidacion.value = null;
  resultadoImportacion.value = null;

  try {
    const { data } = await api.post('/demo/importaciones/confirmar/', {
      archivos: payloadArchivos,
    }, { timeout: timeoutImportacionMs });
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
.importar-page {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.importar-page > .ui-page-header {
  margin-bottom: 0.25rem;
}

.header-group {
  gap: 0.5rem;
}

/* Acción destructiva (I2) */
.btn-destructive {
  background-color: var(--bg-card);
  border-color: var(--border);
  color: var(--danger);
}

.btn-destructive:hover:not(:disabled) {
  background-color: var(--danger-bg);
  border-color: var(--danger-border);
}

.btn-destructive-plain {
  background: transparent;
  border-color: transparent;
  color: var(--danger);
}

.btn-destructive-plain:hover:not(:disabled) {
  background-color: var(--danger-bg);
}

.btn-destructive-plain:disabled {
  background: transparent;
  color: var(--text-light);
}

.chips-line {
  margin-top: 0.25rem;
}

.chip-count {
  display: inline-block;
  margin: 0.15rem 0.35rem 0 0;
  padding: 0.1rem 0.5rem;
  border-radius: 999px;
  background-color: var(--fill-track);
  font-weight: 600;
}

/* Selector de archivo (I1) */
.file-segmented {
  align-self: flex-start;
  flex-wrap: wrap;
}

.file-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  border: 1.5px solid currentColor;
  opacity: 0.55;
}

.file-dot.is-filled {
  border-color: var(--success);
  background-color: var(--success);
  opacity: 1;
}

.ui-segmented button[aria-checked="true"] .file-dot.is-filled {
  border-color: #ffffff;
  background-color: #ffffff;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

/* Editor */
.file-card-header {
  align-items: flex-start;
  gap: 1rem;
}

.file-hint {
  margin-top: 0.25rem;
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.header-code {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.8125rem;
  padding: 0.1rem 0.4rem;
  border-radius: 6px;
  background-color: var(--primary-light);
  color: var(--accent-text);
}

.file-card-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.file-upload-label {
  position: relative;
  cursor: pointer;
}

.hidden-file-input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

/* El contenido CSV sí es código: fuente monoespaciada */
.csv-textarea {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.875rem;
  line-height: 1.55;
  resize: vertical;
  border-radius: 10px;
}

.csv-meta-info {
  display: flex;
  gap: 1.25rem;
  margin-top: 0.5rem;
  font-size: 0.8125rem;
  color: var(--text-muted);
}

/* Pasos (I3) */
.actions-dock {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.25rem;
}

.steps {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.step {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.step-badge {
  flex-shrink: 0;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--border-strong);
  color: var(--text-muted);
  font-size: 0.8125rem;
  font-weight: 700;
}

.step-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-main);
}

.step-state {
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.step-activo .step-badge {
  border-color: var(--accent);
  color: var(--accent-text);
}

.step-hecho .step-badge {
  border-color: var(--success);
  background-color: var(--success);
  color: #ffffff;
}

.step-hecho .step-state { color: var(--success-text); }

.step-error .step-badge {
  border-color: var(--danger);
  background-color: var(--danger);
  color: #ffffff;
}

.step-error .step-state { color: var(--danger-text); }

.step-sep {
  width: 36px;
  height: 2px;
  border-radius: 2px;
  background-color: var(--border);
}

.dock-right {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
}

.dock-count {
  font-size: 0.875rem;
  color: var(--text-muted);
}

/* Errores agrupados (I4) */
.errors-section {
  display: flex;
  flex-direction: column;
}

.error-group + .error-group {
  margin-top: 1rem;
}

.error-group-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0 0 0.45rem;
  padding: 0 0.25rem;
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--danger-text);
  text-transform: capitalize;
}

.error-row {
  --ui-separator-inset: 6.2rem;
  align-items: flex-start;
}

.error-fila {
  flex-shrink: 0;
  width: 4.4rem;
  padding: 0.1rem 0;
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--danger-text);
}

.error-msg {
  font-size: 0.9375rem;
  color: var(--text-main);
}

.campo-code {
  padding: 0.05rem 0.35rem;
  border-radius: 5px;
  background-color: var(--danger-bg);
  color: var(--danger-text);
}
</style>
