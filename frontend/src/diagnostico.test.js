import { describe, it, expect, beforeEach, vi } from 'vitest';
import { createApp, h, nextTick } from 'vue';
import { createPinia, setActivePinia } from 'pinia';
import router from './router/index';
import { useAuthStore } from './stores/auth';
import App from './App.vue';
import AdminLayout from './layouts/AdminLayout.vue';
import api from './api';

function crearTokenConClaims(claims) {
  const encode = (valor) =>
    btoa(JSON.stringify(valor))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '');
  const header = encode({ alg: 'HS256', typ: 'JWT' });
  const payload = encode(claims);
  return `${header}.${payload}.firma-test`;
}

describe('Diagnóstico de Navegación Consecutiva en AdminLayout', () => {
  let container;
  let appInstance;

  beforeEach(async () => {
    setActivePinia(createPinia());
    container = document.createElement('div');
    document.body.appendChild(container);
    vi.restoreAllMocks();

    const auth = useAuthStore();
    auth.token = crearTokenConClaims({ user_id: 1, is_superuser: false });
    auth.tenantId = '2a0f2ada-35cb-4bbf-a054-dc7c39853cf5';
    auth.membresia = {
      tenant: '2a0f2ada-35cb-4bbf-a054-dc7c39853cf5',
      nombre_escuela: 'Escuela Demo Local',
      estado_escuela: 'ACTIVO',
      activo: true,
      es_alumno: false,
      es_administrador: true,
    };

    // Mock API calls to return valid responses or avoid network hangs
    vi.spyOn(api, 'get').mockImplementation((url) => {
      if (url.includes('/alumnos/')) {
        return Promise.resolve({ data: { count: 0, results: [] } });
      }
      if (url.includes('/asignaciones/')) {
        return Promise.resolve({ data: [] });
      }
      if (url.includes('/grupos/')) {
        return Promise.resolve({ data: [] });
      }
      if (url.includes('/planes-estudios/')) {
        return Promise.resolve({ data: [] });
      }
      if (url.includes('/materias/')) {
        return Promise.resolve({ data: [] });
      }
      if (url.includes('/comercial/')) {
        return Promise.resolve({ data: [] });
      }
      return Promise.resolve({ data: {} });
    });
  });

  it('navega secuencialmente entre todas las rutas de AdminLayout', async () => {
    const pinia = createPinia();
    setActivePinia(pinia);
    const auth = useAuthStore(pinia);
    auth.token = crearTokenConClaims({ user_id: 1, is_superuser: false });
    auth.tenantId = '2a0f2ada-35cb-4bbf-a054-dc7c39853cf5';
    auth.membresia = {
      tenant: '2a0f2ada-35cb-4bbf-a054-dc7c39853cf5',
      nombre_escuela: 'Escuela Demo Local',
      estado_escuela: 'ACTIVO',
      activo: true,
      es_alumno: false,
      es_administrador: true,
    };

    appInstance = createApp({
      render() {
        return h(App);
      },
    });
    appInstance.use(pinia);
    appInstance.use(router);

    // Capturar errores no manejados
    const errors = [];
    appInstance.config.errorHandler = (err, instance, info) => {
      errors.push({ err, info });
    };

    appInstance.mount(container);
    await router.isReady();

    const rutas = [
      { path: '/admin/dashboard', clase: 'admin-dashboard' },
      { path: '/admin/alumnos', clase: 'alumnos-page' },
      { path: '/admin/grupos', clase: 'grupos-page' },
      { path: '/admin/importar', clase: 'importar-page' },
      { path: '/admin/asignaciones', clase: 'asignaciones-page' },
      { path: '/admin/planes', clase: 'planes-page' },
      { path: '/admin/comercial/planes', clase: 'comercial-planes-page' },
      { path: '/admin/comercial/configurador', clase: 'configurador-page' },
      { path: '/admin/comercial/suscripcion', clase: 'suscripcion-page' },
      { path: '/admin/comercial/licencias', clase: 'licencias-page' },
    ];

    for (const { path, clase } of rutas) {
      console.log('Probando ruta:', path);
      errors.length = 0;
      await router.push(path);
      await nextTick();
      await new Promise((r) => setTimeout(r, 20));

      const contenido = container.querySelector('.admin-content');
      const html = contenido ? contenido.innerHTML.trim() : '';

      // Regresión: una vista que falla en render debe dejar el contenido vacío (pantalla negra)
      expect(contenido, `La ruta ${path} no renderizó dentro de .admin-content`).toBeTruthy();
      expect(html.length, `La ruta ${path} renderizó contenido vacío (posible pantalla negra)`).toBeGreaterThan(0);
      expect(contenido.innerHTML, `La ruta ${path} no encontró su plantilla principal`).toContain(clase);

      expect(errors, `Errores de render en la ruta ${path}`).toHaveLength(0);
    }

    expect(errors).toHaveLength(0);
    appInstance.unmount();
  });
});
