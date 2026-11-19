import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import router from './index';
import { useAuthStore } from '../stores/auth';

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

describe('Vue Router — Integración comercial institucional y propietario SaaS', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('Registro de rutas comerciales', () => {
    it('registra todas las rutas del cliente institucional bajo /admin/comercial/', () => {
      const rutas = router.getRoutes().map((r) => r.path);

      expect(rutas).toContain('/admin/comercial/planes');
      expect(rutas).toContain('/admin/comercial/configurador');
      expect(rutas).toContain('/admin/comercial/checkout');
      expect(rutas).toContain('/admin/comercial/checkout/resultado');
      expect(rutas).toContain('/admin/comercial/suscripcion');
      expect(rutas).toContain('/admin/comercial/licencias');
    });

    it('registra todas las rutas del propietario SaaS bajo /comercial/propietario/', () => {
      const rutas = router.getRoutes().map((r) => r.path);

      expect(rutas).toContain('/comercial/propietario/dashboard');
      expect(rutas).toContain('/comercial/propietario/clientes');
      expect(rutas).toContain('/comercial/propietario/planes');
      expect(rutas).toContain('/comercial/propietario/suscripciones');
      expect(rutas).toContain('/comercial/propietario/licencias');
      expect(rutas).toContain('/comercial/propietario/facturacion');
    });

    it('incluye alias y redirecciones de conveniencia comercial', () => {
      const rutas = router.getRoutes().map((r) => r.path);

      expect(rutas).toContain('/planes');
      expect(rutas).toContain('/precios');
      expect(rutas).toContain('/propietario');
    });
  });

  describe('Guards de navegación — Control de acceso por rol', () => {
    it('bloquea el panel del propietario a usuarios no autenticados y redirige a /login', async () => {
      const auth = useAuthStore();
      auth.token = null;
      auth.tenantId = null;

      await router.push('/comercial/propietario/dashboard');

      expect(router.currentRoute.value.path).toBe('/login');
      expect(router.currentRoute.value.query.redirect).toBe('/comercial/propietario/dashboard');
    });

    it('impide a un administrador escolar sin rol propietario entrar al panel propietario', async () => {
      const auth = useAuthStore();
      auth.token = crearTokenConClaims({ user_id: 10, is_superuser: false });
      auth.tenantId = '11111111-1111-4000-8000-111111111111';
      auth.membresia = {
        es_administrador: true,
        es_alumno: false,
        es_propietario: false,
        activo: true,
        estado_escuela: 'ACTIVO',
      };

      await router.push('/comercial/propietario/dashboard');

      expect(router.currentRoute.value.path).toBe('/admin/dashboard');
    });

    it('impide a un alumno entrar al panel del propietario SaaS', async () => {
      const auth = useAuthStore();
      auth.token = crearTokenConClaims({ user_id: 20, is_superuser: false });
      auth.tenantId = '11111111-1111-4000-8000-111111111111';
      auth.membresia = {
        es_administrador: false,
        es_alumno: true,
        es_propietario: false,
        activo: true,
        estado_escuela: 'ACTIVO',
      };

      await router.push('/comercial/propietario/dashboard');

      expect(router.currentRoute.value.path).toBe('/alumno/horario');
    });

    it('permite el acceso al propietario SaaS cuando el claim is_superuser es true', async () => {
      const auth = useAuthStore();
      auth.token = crearTokenConClaims({ user_id: 1, is_superuser: true });
      auth.tenantId = '00000000-0000-4000-8000-000000000000';
      auth.membresia = {
        es_administrador: false,
        es_alumno: false,
        es_propietario: true,
        activo: true,
        estado_escuela: 'ACTIVO',
      };

      await router.push('/comercial/propietario/dashboard');
      expect(router.currentRoute.value.path).toBe('/comercial/propietario/dashboard');

      await router.push('/comercial/propietario/clientes');
      expect(router.currentRoute.value.path).toBe('/comercial/propietario/clientes');

      await router.push('/comercial/propietario/planes');
      expect(router.currentRoute.value.path).toBe('/comercial/propietario/planes');

      await router.push('/comercial/propietario/facturacion');
      expect(router.currentRoute.value.path).toBe('/comercial/propietario/facturacion');
    });

    it('permite al administrador escolar acceder a las vistas comerciales institucionales', async () => {
      const auth = useAuthStore();
      auth.token = crearTokenConClaims({ user_id: 15, is_superuser: false });
      auth.tenantId = '22222222-2222-4000-8000-222222222222';
      auth.membresia = {
        es_administrador: true,
        es_alumno: false,
        activo: true,
        estado_escuela: 'ACTIVO',
      };

      await router.push('/admin/comercial/planes');
      expect(router.currentRoute.value.path).toBe('/admin/comercial/planes');

      await router.push('/admin/comercial/configurador');
      expect(router.currentRoute.value.path).toBe('/admin/comercial/configurador');

      await router.push('/admin/comercial/suscripcion');
      expect(router.currentRoute.value.path).toBe('/admin/comercial/suscripcion');
    });

    it('permite a un superusuario/propietario navegar también a las pantallas de gestión institucional', async () => {
      const auth = useAuthStore();
      auth.token = crearTokenConClaims({ user_id: 1, is_superuser: true });
      auth.tenantId = '00000000-0000-4000-8000-000000000000';
      auth.membresia = {
        es_administrador: false,
        es_propietario: true,
        activo: true,
        estado_escuela: 'ACTIVO',
      };

      await router.push('/admin/dashboard');
      expect(router.currentRoute.value.path).toBe('/admin/dashboard');

      await router.push('/admin/comercial/planes');
      expect(router.currentRoute.value.path).toBe('/admin/comercial/planes');
    });
  });
});
