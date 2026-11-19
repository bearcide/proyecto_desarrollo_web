import { beforeEach, describe, expect, it } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useAuthStore } from '../../../../stores/auth';
import { usePermisosComerciales } from './usePermisosComerciales';

vi.mock('../../../../api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    default: {
      get: vi.fn(),
      post: vi.fn(),
    },
    obtenerMensajeError: (err) => err?.message || 'Error mock',
  };
});

function tokenConClaims(claims) {
  const encode = (valor) => btoa(JSON.stringify(valor)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  const header = encode({ alg: 'HS256', typ: 'JWT' });
  const payload = encode(claims);
  return `${header}.${payload}.firma-demo`;
}

describe('usePermisosComerciales — control de autorización del propietario SaaS', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('expone el permiso de propietario SaaS cuando el claim is_superuser es verdadero', () => {
    const authStore = useAuthStore();
    authStore.token = tokenConClaims({ is_superuser: true });

    const permisos = usePermisosComerciales();

    expect(permisos.esPropietario.value).toBe(true);
    expect(permisos.puedeGestionarComercial.value).toBe(true);
  });

  it('niega el permiso de propietario SaaS cuando el claim is_superuser es falso', () => {
    const authStore = useAuthStore();
    authStore.token = tokenConClaims({ is_superuser: false });

    const permisos = usePermisosComerciales();

    expect(permisos.esPropietario.value).toBe(false);
  });

  it('niega el permiso sin sesión activa', () => {
    const permisos = usePermisosComerciales();

    expect(permisos.esPropietario.value).toBe(false);
    expect(permisos.puedeGestionarComercial.value).toBe(false);
  });

  it('deriva el permiso del perfil de membresía cuando el claim no está presente', () => {
    const authStore = useAuthStore();
    authStore.membresia = { es_propietario: true, es_administrador: false };

    const permisos = usePermisosComerciales();

    expect(permisos.esPropietario.value).toBe(true);
  });
});
