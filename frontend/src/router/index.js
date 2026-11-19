import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { decodificarToken } from '../api';

import AdminLayout from '../layouts/AdminLayout.vue';
import AlumnoLayout from '../layouts/AlumnoLayout.vue';
import PropietarioLayout from '../layouts/PropietarioLayout.vue';

import LoginView from '../modules/auth/views/LoginView.vue';
import DashboardView from '../modules/admin/views/DashboardView.vue';
import AsignacionesView from '../modules/admin/views/AsignacionesView.vue';
import ImportarView from '../modules/admin/views/ImportarView.vue';
import AlumnosView from '../modules/admin/views/AlumnosView.vue';
import GruposView from '../modules/admin/views/GruposView.vue';
import PlanesView from '../modules/admin/views/PlanesView.vue';

import HorarioView from '../modules/alumno/views/HorarioView.vue';
import PerfilView from '../modules/alumno/views/PerfilView.vue';
import InscripcionView from '../modules/alumno/views/InscripcionView.vue';

// Módulo comercial: Cliente institucional (escuela)
import ClientePlanesView from '../modules/comercial/cliente/views/PlanesView.vue';
import ClienteConfiguradorView from '../modules/comercial/cliente/views/ConfiguradorView.vue';
import ClienteCheckoutView from '../modules/comercial/cliente/views/CheckoutView.vue';
import ClienteCheckoutResultadoView from '../modules/comercial/cliente/views/CheckoutResultadoView.vue';
import ClienteSuscripcionView from '../modules/comercial/cliente/views/SuscripcionView.vue';
import ClienteLicenciasView from '../modules/comercial/cliente/views/LicenciasView.vue';

// Módulo comercial: Propietario SaaS (superusuario B2B)
import PropietarioDashboardView from '../modules/comercial/propietario/views/DashboardComercialView.vue';
import PropietarioClientesView from '../modules/comercial/propietario/views/ClientesComercialesView.vue';
import PropietarioPlanesView from '../modules/comercial/propietario/views/PlanesComercialesView.vue';
import PropietarioSuscripcionesView from '../modules/comercial/propietario/views/SuscripcionesComercialesView.vue';
import PropietarioLicenciasView from '../modules/comercial/propietario/views/LicenciasComercialesView.vue';
import PropietarioFacturacionView from '../modules/comercial/propietario/views/FacturacionComercialView.vue';

function aBandera(valor) {
  if (typeof valor === 'boolean') return valor;
  if (typeof valor === 'string') return valor.trim().toLowerCase() === 'true';
  if (typeof valor === 'number') return valor === 1;
  return false;
}

function esPropietarioSaaS(auth) {
  const claims = decodificarToken(auth?.token) || {};
  const candidata = claims.is_superuser ?? claims.superuser ?? claims.es_propietario;
  const valor = candidata === undefined ? Boolean(auth?.membresia?.es_propietario) : candidata;
  return aBandera(valor);
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: () => {
        const auth = useAuthStore();
        if (!auth.estaAutenticado) return '/login';
        if (auth.esAdministrador) return '/admin/dashboard';
        if (esPropietarioSaaS(auth)) return '/comercial/propietario/dashboard';
        if (auth.esAlumno) return '/alumno/horario';
        return '/login';
      },
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/admin',
      component: AdminLayout,
      meta: { requiereAdmin: true },
      children: [
        { path: '', redirect: '/admin/dashboard' },
        { path: 'dashboard', name: 'admin-dashboard', component: DashboardView },
        { path: 'asignaciones', name: 'admin-asignaciones', component: AsignacionesView },
        { path: 'importar', name: 'admin-importar', component: ImportarView },
        { path: 'alumnos', name: 'admin-alumnos', component: AlumnosView },
        { path: 'grupos', name: 'admin-grupos', component: GruposView },
        { path: 'planes', name: 'admin-planes', component: PlanesView },
        { path: 'materias', redirect: '/admin/planes' },
        { path: 'comercial/planes', name: 'admin-comercial-planes', component: ClientePlanesView },
        { path: 'comercial/configurador', name: 'admin-comercial-configurador', component: ClienteConfiguradorView },
        { path: 'comercial/checkout', name: 'admin-comercial-checkout', component: ClienteCheckoutView },
        { path: 'comercial/checkout/resultado', name: 'admin-comercial-checkout-resultado', component: ClienteCheckoutResultadoView },
        { path: 'comercial/suscripcion', name: 'admin-comercial-suscripcion', component: ClienteSuscripcionView },
        { path: 'comercial/licencias', name: 'admin-comercial-licencias', component: ClienteLicenciasView },
      ],
    },
    {
      path: '/planes',
      redirect: '/admin/comercial/planes',
    },
    {
      path: '/precios',
      redirect: '/admin/comercial/planes',
    },
    {
      path: '/comercial/propietario',
      component: PropietarioLayout,
      meta: { requierePropietario: true },
      children: [
        { path: '', redirect: '/comercial/propietario/dashboard' },
        {
          path: 'dashboard',
          name: 'propietario-dashboard',
          component: PropietarioDashboardView,
          meta: { title: 'Dashboard Comercial' },
        },
        {
          path: 'clientes',
          name: 'propietario-clientes',
          component: PropietarioClientesView,
          meta: { title: 'Clientes Comerciales' },
        },
        {
          path: 'planes',
          name: 'propietario-planes',
          component: PropietarioPlanesView,
          meta: { title: 'Gestión de Planes' },
        },
        {
          path: 'suscripciones',
          name: 'propietario-suscripciones',
          component: PropietarioSuscripcionesView,
          meta: { title: 'Suscripciones Comerciales' },
        },
        {
          path: 'licencias',
          name: 'propietario-licencias',
          component: PropietarioLicenciasView,
          meta: { title: 'Licencias Comerciales' },
        },
        {
          path: 'facturacion',
          name: 'propietario-facturacion',
          component: PropietarioFacturacionView,
          meta: { title: 'Transacciones y Facturación' },
        },
      ],
    },
    {
      path: '/propietario',
      redirect: '/comercial/propietario/dashboard',
    },
    {
      path: '/alumno',
      component: AlumnoLayout,
      meta: { requiereAlumno: true },
      children: [
        { path: '', redirect: '/alumno/horario' },
        { path: 'horario', name: 'alumno-horario', component: HorarioView },
        { path: 'perfil', name: 'alumno-perfil', component: PerfilView },
        { path: 'inscripcion', name: 'alumno-inscripcion', component: InscripcionView },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
});

router.beforeEach((to) => {
  const auth = useAuthStore();
  const esProp = esPropietarioSaaS(auth);

  // 1. Si la ruta requiere perfil de propietario SaaS
  if (to.matched.some((record) => record.meta.requierePropietario)) {
    if (!auth.estaAutenticado) {
      return { path: '/login', query: { redirect: to.fullPath } };
    }
    if (!esProp) {
      if (auth.esAdministrador) return { path: '/admin/dashboard' };
      if (auth.esAlumno) return { path: '/alumno/horario' };
      return { path: '/login' };
    }
  }

  // 2. Si la ruta requiere perfil de administrador escolar
  if (to.matched.some((record) => record.meta.requiereAdmin)) {
    if (!auth.estaAutenticado) {
      return { path: '/login', query: { redirect: to.fullPath } };
    }
    // Permitir si es administrador escolar O si es propietario SaaS con rol global
    if (!auth.esAdministrador && !esProp) {
      if (auth.esAlumno) return { path: '/alumno/horario' };
      return { path: '/login' };
    }
  }

  // 3. Si la ruta requiere perfil de alumno
  if (to.matched.some((record) => record.meta.requiereAlumno)) {
    if (!auth.estaAutenticado) {
      return { path: '/login', query: { redirect: to.fullPath } };
    }
    if (!auth.esAlumno) {
      if (esProp) return { path: '/comercial/propietario/dashboard' };
      return { path: '/admin/dashboard' };
    }
  }

  // 4. Si ya está autenticado e intenta ir a /login
  if (to.path === '/login' && auth.estaAutenticado) {
    if (esProp && !auth.esAdministrador) {
      return { path: '/comercial/propietario/dashboard' };
    }
    return { path: auth.rutaInicio };
  }

  return true;
});

export default router;
