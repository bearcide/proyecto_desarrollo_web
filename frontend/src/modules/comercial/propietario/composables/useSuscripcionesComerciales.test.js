import { beforeEach, describe, expect, it, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import api from '../../../../api';
import { useSuscripcionesComerciales } from './useSuscripcionesComerciales';
import { useAuthStore } from '../../../../stores/auth';

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

describe('useSuscripcionesComerciales — acciones y autorización del propietario', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('permite cancelar suscripciones activas cuando la sesión es del propietario SaaS', async () => {
    const authStore = useAuthStore();
    authStore.token = tokenConClaims({ is_superuser: true });

    const { cancelar, puedeActuar, cancelando } = useSuscripcionesComerciales();

    expect(puedeActuar({ id: 'sub-1', estado: 'ACTIVE' })).toBe(true);
    expect(puedeActuar({ id: 'sub-1', estado: 'CANCELED' })).toBe(false);
    expect(puedeActuar({ id: 'sub-1', estado: 'ACTIVE', cancelacionProgramada: true })).toBe(false);

    api.post.mockResolvedValueOnce({
      data: { id: 'sub-1', estado: 'active', cancel_at_period_end: true },
    });
    api.get.mockResolvedValueOnce({ data: { count: 0, next: null, previous: null, results: [] } });

    const resultado = await cancelar('sub-1');

    expect(api.post).toHaveBeenCalledWith('/comercial/suscripciones/sub-1/cancelar/', {});
    expect(resultado.ok).toBe(true);
    expect(cancelando.value).toBe(false);
  });

  it('no expone ni ejecuta la cancelación cuando el usuario no es propietario SaaS', async () => {
    const authStore = useAuthStore();
    authStore.token = tokenConClaims({ is_superuser: false });

    const { cancelar, puedeActuar, errorCancelar } = useSuscripcionesComerciales();

    expect(puedeActuar({ id: 'sub-1', estado: 'ACTIVE' })).toBe(false);

    const resultado = await cancelar('sub-1');

    expect(resultado.ok).toBe(false);
    expect(api.post).not.toHaveBeenCalled();
    expect(errorCancelar.value).toBeTruthy();
  });

  it('cierra la cancelación con estado de error cuando el backend responde con conflicto', async () => {
    const authStore = useAuthStore();
    authStore.token = tokenConClaims({ is_superuser: true });

    const { cancelar, errorCancelar } = useSuscripcionesComerciales();

    api.post.mockRejectedValueOnce(new Error('La suscripción ya se encuentra cancelada.'));

    const resultado = await cancelar('sub-1');

    expect(resultado.ok).toBe(false);
    expect(errorCancelar.value).toBe('La suscripción ya se encuentra cancelada.');
  });
});
