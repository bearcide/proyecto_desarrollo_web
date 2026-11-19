<template>
  <div class="horario-visual-root">
    <!-- Selector de vista: segmented control (HIG) -->
    <div class="grid-controls">
      <div class="ui-segmented" role="radiogroup" aria-label="Tipo de vista del horario">
        <button
          type="button"
          role="radio"
          :aria-checked="vistaModo === 'grid' ? 'true' : 'false'"
          @click="vistaModo = 'grid'"
        >
          <AppIcon name="grid" :size="14" />
          Cuadrícula semanal
        </button>
        <button
          type="button"
          role="radio"
          :aria-checked="vistaModo === 'lista' ? 'true' : 'false'"
          @click="vistaModo = 'lista'"
        >
          <AppIcon name="list" :size="14" />
          Vista por días
        </button>
      </div>
    </div>

    <!-- MODO 1: CUADRÍCULA VISUAL SEMANAL -->
    <div v-if="vistaModo === 'grid'" class="timetable-scroll-wrapper">
      <div class="timetable-container">
        <!-- Encabezado de Días -->
        <div class="timetable-header">
          <div class="timetable-header-cell hora-col-header">Hora</div>
          <div
            v-for="dia in diasColumnas"
            :key="dia"
            class="timetable-header-cell"
          >
            {{ dia }}
          </div>
        </div>

        <!-- Cuerpo del Horario -->
        <div class="timetable-body" :style="{ height: `${horasDelDia.length * 52}px` }">
          <!-- Columna de Horas -->
          <div class="timetable-hour-col">
            <div
              v-for="h in horasDelDia"
              :key="h"
              class="timetable-hour-cell"
            >
              {{ formatearHoraEje(h) }}
            </div>
          </div>

          <!-- Columnas de Días -->
          <div
            v-for="dia in diasColumnas"
            :key="dia"
            class="timetable-day-col"
          >
            <!-- Bloques posicionados con cálculo de minutos -->
            <div
              v-for="bloque in bloquesPorDia[dia] || []"
              :key="bloque.idUnico"
              class="timetable-card"
              :class="`card-theme-${bloque.colorIndex % 6}`"
              :style="obtenerEstiloBloque(bloque)"
              :title="`${bloque.nombre} (${bloque.clave}) - Grupo: ${bloque.grupo || 'N/A'}`"
            >
              <div class="tt-card-title">{{ bloque.clave }} · {{ bloque.nombre }}</div>
              <div class="tt-card-meta">
                <span v-if="bloque.grupo" class="badge-mini">Gpo {{ bloque.grupo }}</span>
                <span>{{ formatearRangoMinutos(bloque.inicio, bloque.fin) }}</span>
              </div>
              <div v-if="bloque.profesor" class="tt-card-prof">
                <AppIcon name="user" :size="11" />
                {{ bloque.profesor }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- MODO 2: LISTA POR DÍAS (IDEAL PARA DISPOSITIVOS MÓVILES) -->
    <div v-else class="lista-dias-container">
      <div
        v-for="dia in diasColumnas"
        :key="dia"
        class="dia-card"
      >
        <div class="dia-card-header">
          <h4>{{ dia }}</h4>
          <span class="badge badge-neutral">
            {{ (bloquesPorDia[dia] || []).length }} {{ (bloquesPorDia[dia] || []).length === 1 ? 'clase' : 'clases' }}
          </span>
        </div>

        <div v-if="!(bloquesPorDia[dia] && bloquesPorDia[dia].length)" class="dia-vacio">
          Sin clases programadas este día
        </div>

        <div v-else class="dia-clases-list">
          <div
            v-for="bloque in bloquesPorDia[dia]"
            :key="bloque.idUnico"
            class="clase-item-card"
            :class="`card-theme-${bloque.colorIndex % 6}`"
          >
            <div class="clase-item-top">
              <strong class="clase-clave">{{ bloque.clave }}</strong>
              <span class="clase-hora">{{ formatearRangoMinutos(bloque.inicio, bloque.fin) }}</span>
            </div>
            <div class="clase-nombre">{{ bloque.nombre }}</div>
            <div class="clase-detalles">
              <span v-if="bloque.grupo">Grupo: <strong>{{ bloque.grupo }}</strong></span>
              <span v-if="bloque.profesor">Profesor: <strong>{{ bloque.profesor }}</strong></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import AppIcon from './AppIcon.vue';

const props = defineProps({
  /**
   * Lista de asignaciones o materias con horarios.
   * Formato esperado:
   * Array<{
   *   materia: number,
   *   clave_materia?: string,
   *   clave?: string,
   *   nombre?: string,
   *   grupo?: string,
   *   profesor?: string,
   *   horarios: Array<{ dia: string, inicio: number, fin: number }>,
   *   detalle?: { ... }
   * }>
   */
  items: {
    type: Array,
    default: () => [],
  },
});

const vistaModo = ref('grid');

const diasColumnas = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];

// Rango de horas a renderizar en el horario: de 07:00 (420 min) a 20:00 (1200 min)
const HORA_INICIO_DIA = 7;
const HORA_FIN_DIA = 20;

const horasDelDia = computed(() => {
  const horas = [];
  for (let h = HORA_INICIO_DIA; h <= HORA_FIN_DIA; h++) {
    horas.push(h);
  }
  return horas;
});

function normalizarDia(dia) {
  if (!dia) return '';
  const d = dia.trim().toLowerCase();
  if (d.startsWith('lun')) return 'Lunes';
  if (d.startsWith('mar')) return 'Martes';
  if (d.startsWith('mie') || d.startsWith('mié')) return 'Miércoles';
  if (d.startsWith('jue')) return 'Jueves';
  if (d.startsWith('vie')) return 'Viernes';
  if (d.startsWith('sab') || d.startsWith('sáb')) return 'Sábado';
  if (d.startsWith('dom')) return 'Domingo';
  return dia;
}

function minutosAHora(minutos) {
  const h = Math.floor(minutos / 60);
  const m = minutos % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

function formatearRangoMinutos(inicio, fin) {
  return `${minutosAHora(inicio)} - ${minutosAHora(fin)}`;
}

function formatearHoraEje(h) {
  return `${String(h).padStart(2, '0')}:00`;
}

// Aplanar todas las franjas horarias con su color y coordenadas
const bloquesPorDia = computed(() => {
  const porDia = {
    Lunes: [],
    Martes: [],
    Miércoles: [],
    Jueves: [],
    Viernes: [],
    Sábado: [],
  };

  const colorMap = new Map();
  let colorCounter = 0;

  props.items.forEach((item) => {
    const clave = item.clave_materia || item.clave || item.detalle?.clave_materia || `M${item.materia}`;
    const nombre = item.nombre || item.detalle?.nombre_materia || item.nombre_materia || clave;
    const grupo = item.detalle?.grupo || item.grupo || '';
    const profesor = item.profesor || item.detalle?.profesor || '';
    const horarios = item.horarios || item.detalle?.horarios || [];

    if (!colorMap.has(clave)) {
      colorMap.set(clave, colorCounter++);
    }
    const colorIndex = colorMap.get(clave);

    horarios.forEach((h, hIdx) => {
      const diaNorm = normalizarDia(h.dia);
      if (porDia[diaNorm]) {
        porDia[diaNorm].push({
          idUnico: `${clave}-${diaNorm}-${h.inicio}-${hIdx}`,
          clave,
          nombre,
          grupo,
          profesor,
          dia: diaNorm,
          inicio: h.inicio,
          fin: h.fin,
          colorIndex,
        });
      }
    });
  });

  // Ordenar bloques de cada día cronológicamente
  Object.keys(porDia).forEach((d) => {
    porDia[d].sort((a, b) => a.inicio - b.inicio);
  });

  return porDia;
});

// Cálculo de altura y posición absoluta en la cuadrícula
function obtenerEstiloBloque(bloque) {
  const alturaHoraPx = 52; // pixels per hour
  const minutosInicioBase = HORA_INICIO_DIA * 60; // 420 minutos

  const offsetMinutos = Math.max(0, bloque.inicio - minutosInicioBase);
  const duracionMinutos = Math.max(30, bloque.fin - bloque.inicio);

  const topPx = (offsetMinutos / 60) * alturaHoraPx;
  const heightPx = (duracionMinutos / 60) * alturaHoraPx;

  return {
    top: `${topPx}px`,
    height: `${heightPx - 3}px`,
  };
}
</script>

<style scoped>
.horario-visual-root {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.grid-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.timetable-scroll-wrapper {
  overflow-x: auto;
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
}

.timetable-container {
  min-width: 780px;
  background: var(--bg-card);
}

.hora-col-header {
  background: var(--bg-surface);
}

.tt-card-prof {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 0.68rem;
  color: inherit;
  opacity: 0.85;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 1px;
}

.badge-mini {
  background: var(--fill-track);
  padding: 1px 4px;
  border-radius: 3px;
  font-weight: 700;
  font-size: 0.65rem;
  margin-right: 4px;
}

/* Modo Lista por Días */
.lista-dias-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.dia-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1.15rem;
  box-shadow: var(--shadow-xs);
}

.dia-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.85rem;
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: 0.5rem;
}

.dia-card-header h4 {
  font-size: 1rem;
  color: var(--text-main);
}

.dia-vacio {
  font-size: 0.85rem;
  color: var(--text-light);
  font-style: italic;
  padding: 0.5rem 0;
}

.dia-clases-list {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.clase-item-card {
  padding: 0.75rem 0.9rem;
  border-radius: var(--radius-sm);
  border-left: 4px solid;
}

.clase-item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.25rem;
}

.clase-clave {
  font-size: 0.875rem;
}

.clase-hora {
  font-size: 0.775rem;
  font-weight: 600;
}

.clase-nombre {
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.35rem;
}

.clase-detalles {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  font-size: 0.75rem;
  opacity: 0.9;
}
</style>
