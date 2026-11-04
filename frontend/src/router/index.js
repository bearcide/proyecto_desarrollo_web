import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth';

import AdminLayout from '../layouts/AdminLayout.vue';
import AlumnoLayout from '../layouts/AlumnoLayout.vue';

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

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: () => {
        const auth = useAuthStore();
        return auth.estaAutenticado ? auth.rutaInicio : '/login';
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
      ],
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

  // 1. Si la ruta requiere perfil de administrador
  if (to.matched.some((record) => record.meta.requiereAdmin)) {
    if (!auth.estaAutenticado) {
      return { path: '/login' };
    }
    if (!auth.esAdministrador) {
      return { path: '/alumno/horario' };
    }
  }

  // 2. Si la ruta requiere perfil de alumno
  if (to.matched.some((record) => record.meta.requiereAlumno)) {
    if (!auth.estaAutenticado) {
      return { path: '/login' };
    }
    if (!auth.esAlumno) {
      return { path: '/admin/dashboard' };
    }
  }

  // 3. Si ya está autenticado e intenta ir a /login
  if (to.path === '/login' && auth.estaAutenticado) {
    return { path: auth.rutaInicio };
  }

  return true;
});

export default router;
