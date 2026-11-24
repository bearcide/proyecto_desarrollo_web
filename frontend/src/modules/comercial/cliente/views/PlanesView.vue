<template>
  <div class="comercial-planes-page">
    <!-- Header de la página -->
    <div class="page-header">
      <div>
        <div class="header-pretitle">
          <AppIcon name="award" size="16" class="text-primary" />
          <span>Contratación de Software SaaS para Instituciones Educativas</span>
        </div>
        <h1 class="page-title">Planes Comerciales y Licenciamiento</h1>
        <p class="page-subtitle">
          Selecciona el modelo comercial idóneo para tu escuela o campus universitario.
          Precios oficiales sincronizados en tiempo real con el servidor.
        </p>
      </div>

      <div class="header-actions">
        <router-link to="/admin/comercial/suscripcion" class="btn btn-secondary btn-sm">
          <AppIcon name="credit-card" size="15" />
          <span>Mi Suscripción</span>
        </router-link>
        <button
          type="button"
          class="btn btn-secondary btn-sm"
          :disabled="cargando"
          @click="cargarDatos"
        >
          <AppIcon name="refresh" size="14" :class="{ spinner: cargando }" />
          <span>Actualizar Precios</span>
        </button>
      </div>
    </div>

    <!-- Banner si la escuela ya tiene un plan activo -->
    <div v-if="acceso?.activo" class="active-subscription-banner">
      <div class="banner-content">
        <AppIcon name="check-circle" size="20" class="text-success" />
        <div>
          <strong class="banner-title">Tu institución cuenta con acceso activo</strong>
          <p class="banner-desc">
            Plan activo: <strong>{{ acceso.plan_actual || 'Plan Institucional' }}</strong>
            • Hasta {{ acceso.max_alumnos?.toLocaleString() }} alumnos en {{ acceso.max_planteles }} plantel(es).
          </p>
        </div>
      </div>
      <router-link to="/admin/comercial/suscripcion" class="btn btn-sm btn-outline">
        Gestionar Licencias & Pagos
      </router-link>
    </div>

    <!-- Error Alert -->
    <div v-if="error" class="alert alert-danger" role="alert">
      <AppIcon name="alert" size="18" />
      <span>{{ error }}</span>
    </div>

    <!-- Selector de Filtro de Modalidad -->
    <div class="modalidades-filter-bar">
      <div class="filter-label">
        <AppIcon name="sliders" size="14" />
        <span>Filtrar por Modelo:</span>
      </div>
      <div class="filter-pills" role="tablist">
        <button
          v-for="filtro in opcionesFiltro"
          :key="filtro.clave"
          type="button"
          class="filter-pill-btn"
          :class="{ active: filtroActivo === filtro.clave }"
          @click="filtroActivo = filtro.clave"
        >
          {{ filtro.nombre }}
        </button>
      </div>
    </div>

    <!-- Estado de carga -->
    <div v-if="cargando && !planes.length" class="empty-state">
      <div class="spinner spinner-primary" style="margin: 0 auto 0.75rem;"></div>
      <span class="text-muted">Consultando catálogo oficial de precios desde la API…</span>
    </div>

    <!-- Grid de Planes Comerciales -->
    <div v-else class="planes-grid">
      <PlanCard
        v-for="plan in planesFiltrados"
        :key="plan.id"
        :plan="plan"
        :precios="precios"
        @contratar="onContratar"
        @configurar="onConfigurar"
      />
    </div>

    <!-- Tabla Comparativa Detallada -->
    <div class="matrix-section">
      <div class="matrix-header">
        <h2 class="matrix-title">Matriz Comparativa de Capacidades</h2>
        <p class="matrix-desc">
          Compara los límites operativos y funcionalidades arquitectónicas de cada versión.
        </p>
      </div>

      <div class="table-responsive matrix-table-card">
        <table class="table matrix-table">
          <thead>
            <tr>
              <th scope="col" class="feature-col">Característica Institucional</th>
              <th v-for="p in planes" :key="p.id" scope="col" class="plan-header-cell">
                <span class="matrix-plan-name">{{ p.nombre }}</span>
                <span class="badge badge-neutral text-xs">ID: {{ p.codigo }}</span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="feature-name">Límite de Alumnos Activos</td>
              <td v-for="p in planes" :key="p.id" class="text-center font-bold">
                {{ p.max_alumnos?.toLocaleString() }} alumnos
              </td>
            </tr>
            <tr>
              <td class="feature-name">Planteles Soportados</td>
              <td v-for="p in planes" :key="p.id" class="text-center font-bold">
                {{ p.max_planteles }} {{ p.max_planteles === 1 ? 'plantel' : 'planteles' }}
              </td>
            </tr>
            <tr>
              <td class="feature-name">Inscripción en Línea & Matrícula Digital</td>
              <td v-for="p in planes" :key="p.id" class="text-center">
                <AppIcon name="check" size="18" class="text-success" />
              </td>
            </tr>
            <tr>
              <td class="feature-name">Algoritmo Anti-Empalme de Horarios</td>
              <td v-for="p in planes" :key="p.id" class="text-center">
                <AppIcon
                  :name="p.codigo !== 'starter' ? 'check' : 'x'"
                  size="18"
                  :class="p.codigo !== 'starter' ? 'text-success' : 'text-muted'"
                />
              </td>
            </tr>
            <tr>
              <td class="feature-name">Importación Masiva CSV de Alumnos</td>
              <td v-for="p in planes" :key="p.id" class="text-center">
                <AppIcon
                  :name="p.codigo !== 'starter' ? 'check' : 'x'"
                  size="18"
                  :class="p.codigo !== 'starter' ? 'text-success' : 'text-muted'"
                />
              </td>
            </tr>
            <tr>
              <td class="feature-name">Soporte Técnico Especializado</td>
              <td v-for="p in planes" :key="p.id" class="text-center text-sm">
                {{ p.codigo === 'enterprise' ? '24/7 con SLA 99.9%' : p.codigo === 'pro' ? 'Prioritario (Mesa de ayuda)' : 'Estándar vía ticket' }}
              </td>
            </tr>
            <tr>
              <td class="feature-name">Modalidades Disponibles</td>
              <td v-for="p in planes" :key="p.id" class="text-center">
                <div class="tags-container">
                  <ModalidadBadge
                    v-for="precio in preciosDePlan(p.id)"
                    :key="precio.id"
                    :modalidad="precio.modalidad"
                    size="sm"
                  />
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Banner de Contratos Personalizados & Universidades -->
    <div class="custom-contract-card">
      <div class="custom-content">
        <div class="custom-badge">
          <AppIcon name="shield" size="18" />
          <span>Grandes Redes Universitarias</span>
        </div>
        <h3 class="custom-title">¿Requieres un contrato multi-campus o financiamiento institucional?</h3>
        <p class="custom-desc">
          Contamos con esquemas de licenciamiento perpetuo on-premise, despliegue en nube privada de la institución,
          convenios de pago por ciclo lectivo y acuerdos de nivel de servicio (SLA) a la medida.
        </p>
      </div>
      <div class="custom-action">
        <router-link
          to="/admin/comercial/configurador?modalidad=enterprise"
          class="btn btn-primary"
        >
          <AppIcon name="sliders" size="16" />
          <span>Cotizar Contrato Personalizado</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import AppIcon from '../../../../components/AppIcon.vue';
import PlanCard from '../components/PlanCard.vue';
import ModalidadBadge from '../components/ModalidadBadge.vue';
import { useComercial } from '../composables/useComercial';

const router = useRouter();
const { cargando, error, planes, precios, acceso, cargarCatalogo, cargarEstadoInstitucion } = useComercial();

const filtroActivo = ref('todos');

const opcionesFiltro = [
  { clave: 'todos', nombre: 'Todos los Modelos' },
  { clave: 'annual', nombre: 'Suscripción Anual (Ahorro)' },
  { clave: 'monthly', nombre: 'Suscripción Mensual' },
  { clave: 'process', nombre: 'Por Proceso de Inscripción' },
  { clave: 'institutional', nombre: 'Licencia Institucional' },
  { clave: 'enterprise', nombre: 'Contratos Personalizados' },
];

onMounted(async () => {
  await cargarDatos();
});

async function cargarDatos() {
  await Promise.all([cargarCatalogo(), cargarEstadoInstitucion()]);
}

const planesFiltrados = computed(() => {
  if (filtroActivo.value === 'todos') {
    return planes.value;
  }
  return planes.value.filter((plan) => {
    const preciosPlan = precios.value.filter((p) => p.plan === plan.id && p.activo);
    return preciosPlan.some((p) => p.modalidad === filtroActivo.value);
  });
});

function preciosDePlan(planId) {
  return precios.value.filter((p) => p.plan === planId && p.activo);
}

function onContratar({ plan, precio }) {
  router.push({
    path: '/admin/comercial/checkout',
    query: {
      plan_id: plan.id,
      precio_id: precio.id,
    },
  });
}

function onConfigurar({ plan, precio }) {
  router.push({
    path: '/admin/comercial/configurador',
    query: {
      plan_id: plan.id,
      precio_id: precio?.id,
      modalidad: precio?.modalidad,
    },
  });
}
</script>

<style scoped>
.comercial-planes-page {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
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

.active-subscription-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  background: var(--success-bg);
  border: 1px solid var(--success-border);
  border-radius: var(--radius-md);
  padding: 1rem 1.25rem;
  flex-wrap: wrap;
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.banner-title {
  color: var(--success-text);
  font-size: 0.95rem;
  display: block;
}

.banner-desc {
  color: var(--success-text);
  font-size: 0.82rem;
  margin: 0.15rem 0 0;
  opacity: 0.9;
}

.modalidades-filter-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 0.75rem 1rem;
  flex-wrap: wrap;
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-light);
  text-transform: uppercase;
}

.filter-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.filter-pill-btn {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  font-size: 0.8rem;
  font-weight: 600;
  padding: 0.4rem 0.8rem;
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all 0.15s ease;
}

.filter-pill-btn:hover {
  color: var(--text-main);
  border-color: var(--border);
}

.filter-pill-btn.active {
  background: var(--accent);
  color: #ffffff;
  border-color: var(--primary);
}

.planes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
  align-items: stretch;
}

.matrix-section {
  margin-top: 1.5rem;
}

.matrix-header {
  margin-bottom: 1rem;
}

.matrix-title {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--text-main);
  margin: 0;
}

.matrix-desc {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin: 0.25rem 0 0;
}

.matrix-table-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.matrix-table {
  width: 100%;
  border-collapse: collapse;
}

.matrix-table th,
.matrix-table td {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border-subtle);
}

.feature-col {
  width: 32%;
  text-align: left;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-muted);
}

.plan-header-cell {
  text-align: center;
}

.matrix-plan-name {
  display: block;
  font-size: 1rem;
  font-weight: 800;
  color: var(--text-main);
  margin-bottom: 0.2rem;
}

.feature-name {
  font-weight: 600;
  font-size: 0.88rem;
  color: var(--text-main);
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  justify-content: center;
}

.custom-contract-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2rem;
  background: linear-gradient(135deg, rgba(79, 70, 229, 0.08), rgba(124, 58, 237, 0.08));
  border: 1px solid var(--primary-border);
  border-radius: var(--radius-lg);
  padding: 2rem;
  flex-wrap: wrap;
}

.custom-content {
  flex: 1;
  min-width: 280px;
}

.custom-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  color: var(--primary);
  font-size: 0.75rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.custom-title {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--text-main);
  margin: 0 0 0.5rem;
}

.custom-desc {
  font-size: 0.88rem;
  color: var(--text-muted);
  line-height: 1.5;
  margin: 0;
}

.custom-action {
  flex-shrink: 0;
}
</style>
