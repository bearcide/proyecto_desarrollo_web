<template>
  <div class="configurador-page">
    <div class="page-header">
      <div>
        <div class="header-pretitle">
          <AppIcon name="sliders" size="16" class="text-primary" />
          <span>Configurador Dinámico Institucional</span>
        </div>
        <h1 class="page-title">Personaliza la Contratación de tu Escuela</h1>
        <p class="page-subtitle">
          Ajusta el volumen de alumnos, número de planteles y módulos requeridos.
          El precio final será calculado y sellado de forma inmutable por el backend (Django).
        </p>
      </div>

      <div class="header-actions">
        <router-link to="/admin/comercial/planes" class="btn btn-secondary btn-sm">
          <AppIcon name="arrow-left" size="15" />
          <span>Volver al Catálogo</span>
        </router-link>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="error" class="alert alert-danger" role="alert">
      <AppIcon name="alert" size="18" />
      <span>{{ error }}</span>
    </div>

    <!-- Layout en 2 columnas: Configuración y Resumen Sticky -->
    <div class="config-layout">
      <!-- Columna Principal de Opciones -->
      <div class="config-main">
        <!-- 1. Selección de Plan Base -->
        <section class="card config-section">
          <div class="section-title-row">
            <span class="step-num">1</span>
            <div>
              <h2 class="section-title">Selecciona el Plan Base</h2>
              <p class="section-desc">Escoge el nivel de infraestructura adecuado para tu institución.</p>
            </div>
          </div>

          <div class="plans-select-grid">
            <div
              v-for="plan in planes"
              :key="plan.id"
              class="plan-select-card"
              :class="{ active: planSeleccionado?.id === plan.id }"
              @click="seleccionarPlan(plan)"
            >
              <div class="plan-select-header">
                <span class="plan-select-name">{{ plan.nombre }}</span>
                <span class="badge badge-indigo text-xs">{{ plan.codigo }}</span>
              </div>
              <p class="plan-select-desc">{{ plan.descripcion }}</p>
              <div class="plan-select-limits">
                <span>Máx. {{ plan.max_alumnos?.toLocaleString() }} alumnos</span> •
                <span>{{ plan.max_planteles }} plantel(es)</span>
              </div>
            </div>
          </div>
        </section>

        <!-- 2. Selección de Modelo Comercial / Modalidad -->
        <section class="card config-section">
          <div class="section-title-row">
            <span class="step-num">2</span>
            <div>
              <h2 class="section-title">Modelo Comercial y Periodo</h2>
              <p class="section-desc">Selecciona la frecuencia y modalidad de facturación autorizada.</p>
            </div>
          </div>

          <div v-if="preciosDisponibles.length" class="modalidades-grid">
            <div
              v-for="precio in preciosDisponibles"
              :key="precio.id"
              class="modalidad-card"
              :class="{ active: precioSeleccionado?.id === precio.id }"
              @click="precioSeleccionado = precio"
            >
              <div class="modalidad-header">
                <ModalidadBadge :modalidad="precio.modalidad" />
                <span class="modalidad-price">{{ formatearMoneda(precio.importe, precio.moneda) }}</span>
              </div>
              <p class="modalidad-desc">{{ obtenerDescripcionModalidad(precio.modalidad) }}</p>
              <div class="modalidad-meta">
                <span v-if="parseFloat(precio.por_alumno) > 0">
                  + {{ formatearMoneda(precio.por_alumno, precio.moneda) }} / alumno
                </span>
                <span v-else class="text-success font-bold">
                  Sin cargo por alumno
                </span>
              </div>
            </div>
          </div>

          <div v-else class="empty-state">
            <span class="text-muted text-sm">Selecciona un plan base para consultar las modalidades activas.</span>
          </div>
        </section>

        <!-- 3. Dimensionamiento de Alumnos & Planteles -->
        <section class="card config-section">
          <div class="section-title-row">
            <span class="step-num">3</span>
            <div>
              <h2 class="section-title">Volumen de Alumnos y Planteles</h2>
              <p class="section-desc">Determina el límite operativo de matrículas concurrentes.</p>
            </div>
          </div>

          <div class="dimension-controls">
            <!-- Slider Alumnos -->
            <div class="control-block">
              <div class="control-label-row">
                <label for="slider-alumnos" class="control-label">
                  <AppIcon name="user" size="16" />
                  <span>Alumnos a matricular en el periodo:</span>
                </label>
                <div class="number-input-pill">
                  <input
                    id="input-alumnos"
                    v-model.number="cantidadAlumnos"
                    type="number"
                    min="1"
                    :max="planSeleccionado ? planSeleccionado.max_alumnos * 2 : 20000"
                    class="number-input"
                  />
                  <span class="number-unit">alumnos</span>
                </div>
              </div>

              <input
                id="slider-alumnos"
                v-model.number="cantidadAlumnos"
                type="range"
                min="50"
                :max="planSeleccionado ? planSeleccionado.max_alumnos : 10000"
                step="25"
                class="range-slider"
              />

              <div class="slider-marks">
                <span>50</span>
                <span>{{ (planSeleccionado?.max_alumnos / 2) || 2500 }}</span>
                <span>{{ planSeleccionado?.max_alumnos || 5000 }} alumnos</span>
              </div>
            </div>

            <!-- Selector Planteles -->
            <div class="control-block">
              <div class="control-label-row">
                <label for="select-planteles" class="control-label">
                  <AppIcon name="building" size="16" />
                  <span>Número de planteles o sedes a operar:</span>
                </label>
                <div class="number-input-pill">
                  <select id="select-planteles" v-model.number="cantidadPlanteles" class="select-inline">
                    <option v-for="n in 10" :key="n" :value="n">
                      {{ n }} {{ n === 1 ? 'Campus / Plantel' : 'Planteles / Sedes' }}
                    </option>
                  </select>
                </div>
              </div>
              <p class="text-xs text-muted" style="margin-top: 0.25rem;">
                Cada sede adicional cuenta con base de datos sincronizada y permisos independientes por director.
              </p>
            </div>
          </div>
        </section>

        <!-- 4. Módulos & Add-ons Opcionales -->
        <section class="card config-section">
          <div class="section-title-row">
            <span class="step-num">4</span>
            <div>
              <h2 class="section-title">Módulos Especiales y Soporte</h2>
              <p class="section-desc">Habilita capacidades de integración y garantías de servicio.</p>
            </div>
          </div>

          <div class="addons-list">
            <label
              v-for="addon in catalogoAddOns"
              :key="addon.id"
              class="addon-card"
              :class="{ active: addOnsSeleccionados.includes(addon.id) }"
            >
              <input
                type="checkbox"
                :value="addon.id"
                v-model="addOnsSeleccionados"
                class="addon-checkbox"
              />
              <div class="addon-info">
                <div class="addon-title-row">
                  <span class="addon-name">{{ addon.nombre }}</span>
                  <span class="addon-cost">+ {{ formatearMoneda(addon.costo) }} MXN</span>
                </div>
                <p class="addon-desc">{{ addon.descripcion }}</p>
              </div>
            </label>
          </div>
        </section>
      </div>

      <!-- Columna Lateral: Resumen de Cotización -->
      <aside class="config-sidebar">
        <CotizadorSummary
          :plan="planSeleccionado"
          :precio="precioSeleccionado"
          :alumnos="cantidadAlumnos"
          :planteles="cantidadPlanteles"
          :add-ons="addOnsObjetos"
          :cargando="cargandoCheckout"
          @proceder-checkout="irACheckout"
        />
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import AppIcon from '../../../../components/AppIcon.vue';
import ModalidadBadge from '../components/ModalidadBadge.vue';
import CotizadorSummary from '../components/CotizadorSummary.vue';
import { useComercial } from '../composables/useComercial';
import { formatearMoneda, MODALIDADES } from '../domain/comercialCalculos';

const route = useRoute();
const router = useRouter();
const { planes, precios, error, cargarCatalogo } = useComercial();

const planSeleccionado = ref(null);
const precioSeleccionado = ref(null);
const cantidadAlumnos = ref(500);
const cantidadPlanteles = ref(1);
const addOnsSeleccionados = ref([]);
const cargandoCheckout = ref(false);

const catalogoAddOns = [
  {
    id: 'api_webhooks',
    nombre: 'API REST Escolar & Webhooks en Tiempo Real',
    descripcion: 'Conectividad bidireccional con tu ERP administrativo, Banner, SAP o Moodle.',
    costo: 3500.0,
  },
  {
    id: 'sla_999',
    nombre: 'SLA Empresarial 99.9% & Teléfono de Emergencia',
    descripcion: 'Garantía de respuesta técnica en menos de 15 minutos en días de inscripción masiva.',
    costo: 4900.0,
  },
  {
    id: 'migracion_asistida',
    nombre: 'Servicio de Migración y Validación de Planes de Estudio',
    descripcion: 'Ingeniero asignado para modelar el grafo curricular y verificar prerrequisitos.',
    costo: 6000.0,
  },
];

onMounted(async () => {
  await cargarCatalogo();

  // Preseleccionar si viene por query param
  const planIdQuery = route.query.plan_id;
  const precioIdQuery = route.query.precio_id;
  const modalidadQuery = route.query.modalidad;

  if (planIdQuery && planes.value.length) {
    const matchPlan = planes.value.find((p) => p.id === planIdQuery);
    if (matchPlan) planSeleccionado.value = matchPlan;
  } else if (planes.value.length) {
    planSeleccionado.value = planes.value.find((p) => p.codigo === 'pro') || planes.value[0];
  }

  actualizarPrecioPorDefecto(precioIdQuery, modalidadQuery);
});

function seleccionarPlan(plan) {
  planSeleccionado.value = plan;
  actualizarPrecioPorDefecto();
}

const preciosDisponibles = computed(() => {
  if (!planSeleccionado.value) return [];
  return precios.value.filter((p) => p.plan === planSeleccionado.value.id && p.activo);
});

function actualizarPrecioPorDefecto(precioIdPref, modalidadPref) {
  if (!preciosDisponibles.value.length) {
    precioSeleccionado.value = null;
    return;
  }

  if (precioIdPref) {
    const p = preciosDisponibles.value.find((x) => x.id === precioIdPref);
    if (p) {
      precioSeleccionado.value = p;
      return;
    }
  }

  if (modalidadPref) {
    const p = preciosDisponibles.value.find((x) => x.modalidad === modalidadPref);
    if (p) {
      precioSeleccionado.value = p;
      return;
    }
  }

  precioSeleccionado.value =
    preciosDisponibles.value.find((p) => p.modalidad === 'annual') ||
    preciosDisponibles.value.find((p) => p.modalidad === 'monthly') ||
    preciosDisponibles.value[0];
}

const addOnsObjetos = computed(() => {
  return catalogoAddOns.filter((a) => addOnsSeleccionados.value.includes(a.id));
});

function obtenerDescripcionModalidad(modalidad) {
  return MODALIDADES[modalidad]?.descripcion || 'Modalidad de contratación.';
}

function irACheckout() {
  if (!planSeleccionado.value || !precioSeleccionado.value) return;

  router.push({
    path: '/admin/comercial/checkout',
    query: {
      plan_id: planSeleccionado.value.id,
      precio_id: precioSeleccionado.value.id,
      alumnos: cantidadAlumnos.value,
      planteles: cantidadPlanteles.value,
    },
  });
}
</script>

<style scoped>
.configurador-page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 1240px;
  margin: 0 auto;
  padding: 1.5rem 1rem 3rem;
}

.header-pretitle {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--primary);
  margin-bottom: 0.35rem;
}

.config-layout {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 1.75rem;
  align-items: flex-start;
}

@media (max-width: 992px) {
  .config-layout {
    grid-template-columns: 1fr;
  }
}

.config-main {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.config-section {
  padding: 1.75rem;
  border-radius: var(--radius-lg);
  background: var(--bg-card);
  border: 1px solid var(--border);
}

.section-title-row {
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
  margin-bottom: 1.5rem;
}

.step-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--primary);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 0.85rem;
  flex-shrink: 0;
}

.section-title {
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--text-main);
  margin: 0 0 0.2rem;
}

.section-desc {
  font-size: 0.84rem;
  color: var(--text-muted);
  margin: 0;
}

/* 1. Planes select grid */
.plans-select-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}

.plan-select-card {
  border: 2px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1.25rem;
  cursor: pointer;
  background: var(--bg-card);
  transition: all 0.15s ease;
}

.plan-select-card:hover {
  border-color: var(--primary-border);
  transform: translateY(-2px);
}

.plan-select-card.active {
  border-color: var(--primary);
  background: var(--primary-light);
  box-shadow: 0 0 0 1px var(--primary);
}

.plan-select-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.plan-select-name {
  font-weight: 800;
  font-size: 0.95rem;
  color: var(--text-main);
}

.plan-select-desc {
  font-size: 0.78rem;
  color: var(--text-muted);
  line-height: 1.4;
  margin: 0 0 0.75rem;
  min-height: 34px;
}

.plan-select-limits {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-light);
}

/* 2. Modalidades grid */
.modalidades-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.85rem;
}

.modalidad-card {
  border: 2px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1rem;
  cursor: pointer;
  background: var(--bg-card);
  transition: all 0.15s ease;
}

.modalidad-card:hover {
  border-color: var(--primary-border);
}

.modalidad-card.active {
  border-color: var(--primary);
  background: var(--primary-light);
}

.modalidad-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.4rem;
}

.modalidad-price {
  font-weight: 800;
  font-size: 0.92rem;
  color: var(--text-main);
}

.modalidad-desc {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin: 0 0 0.5rem;
  line-height: 1.35;
  min-height: 32px;
}

.modalidad-meta {
  font-size: 0.72rem;
  color: var(--text-muted);
  font-weight: 600;
}

/* 3. Dimension Controls */
.dimension-controls {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.control-block {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.control-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.control-label {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-weight: 700;
  font-size: 0.88rem;
  color: var(--text-main);
}

.number-input-pill {
  display: flex;
  align-items: center;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.2rem 0.6rem;
}

.number-input {
  border: none;
  background: transparent;
  font-size: 0.95rem;
  font-weight: 800;
  width: 90px;
  color: var(--text-main);
  text-align: right;
  padding: 0.2rem 0.4rem;
}

.number-unit {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-muted);
  margin-left: 0.25rem;
}

.select-inline {
  border: none;
  background: transparent;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-main);
  padding: 0.25rem;
  cursor: pointer;
}

.range-slider {
  width: 100%;
  accent-color: var(--primary);
  height: 6px;
  border-radius: var(--radius-full);
}

.slider-marks {
  display: flex;
  justify-content: space-between;
  font-size: 0.72rem;
  color: var(--text-light);
  font-weight: 600;
}

/* 4. Addons list */
.addons-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.addon-card {
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
  padding: 1rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s ease;
}

.addon-card:hover {
  background: var(--bg-surface);
}

.addon-card.active {
  border-color: var(--primary-border);
  background: var(--primary-light);
}

.addon-checkbox {
  margin-top: 0.25rem;
  accent-color: var(--primary);
  width: 18px;
  height: 18px;
}

.addon-info {
  flex: 1;
}

.addon-title-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.addon-name {
  font-weight: 700;
  font-size: 0.88rem;
  color: var(--text-main);
}

.addon-cost {
  font-weight: 800;
  font-size: 0.85rem;
  color: var(--primary);
  white-space: nowrap;
}

.addon-desc {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.4;
}

.config-sidebar {
  position: relative;
}
</style>
