import { beforeEach, describe, expect, it, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import api from '../../../../api';
import { useLicenciasComerciales } from './useLicenciasComerciales';
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

describe('useLicenciasComerciales — acciones y autorización del propietario', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('permite revocar licencias activas cuando la sesión es del propietario SaaS', async () => {
    const authStore = useAuthStore();
    authStore.token = tokenConClaims({ is_superuser: true });

    const { revocar, puedeRevocar, revocando } = useLicenciasComerciales();

    expect(puedeRevocar({ id: 'lic-1', estado: 'ACTIVE' })).toBe(true);
    expect(puedeRevocar({ id: 'lic-1', estado: 'REVOKED' })).toBe(false);

    api.post.mockResolvedValueOnce({ data: { id: 'lic-1', estado: 'revoked' } });
    api.get.mockResolvedValueOnce({ data: { count: 0, next: null, previous: null, results: [] } });

    const resultado = await revocar('lic-1');

    expect(api.post).toHaveBeenCalledWith('/comercial/licencias/lic-1/revocar/', {});
    expect(resultado.ok).toBe(true);
    expect(revocando.value).toBe(false);
  });

  it('no expone ni ejecuta la revocación cuando el usuario no es propietario SaaS', async () => {
    const authStore = useAuthStore();
    authStore.token = tokenConClaims({ is_superuser: false });

    const { revocar, puedeRevocar, errorRevocar } = useLicenciasComerciales();

    expect(puedeRevocar({ id: 'lic-1', estado: 'ACTIVE' })).toBe(false);

    const resultado = await revocar('lic-1');

    expect(resultado.ok).toBe(false);
    expect(api.post).not.toHaveBeenCalled();
    expect(errorRevocar.value).toBeTruthy();
  });

  it('cierra la revocación con estado de error cuando el backend responde con conflicto', async () => {
    const authStore = useAuthStore();
    authStore.token = tokenConClaims({ is_superuser: true });

    const { revocar, errorRevocar } = useLicenciasComerciales();

    api.post.mockRejectedValueOnce(new Error('La licencia ya se encuentra revocada.'));

    const resultado = await revocar('lic-1');

    expect(resultado.ok).toBe(false);
    expect(errorRevocar.value).toBe('La licencia ya se encuentra revocada.');
  });
});
