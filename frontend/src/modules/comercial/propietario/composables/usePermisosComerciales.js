import { computed } from 'vue';
import { useAuthStore } from '../../../../stores/auth';
import { decodificarToken } from '../../../../api';

/**
 * Normaliza la bandera de propietario SaaS (`is_superuser`) desde los claims
 * del JWT o desde la membresía resuelta en la sesión.
 */
function aBandera(valor) {
  if (typeof valor === 'boolean') return valor;
  if (typeof valor === 'string') return valor.trim().toLowerCase() === 'true';
  if (typeof valor === 'number') return valor === 1;
  return false;
}

/**
 * Permisos del panel comercial del propietario SaaS.
 *
 * Fuente de verdad backend: `user.is_authenticated and user.is_active and user.is_superuser`.
 * Frontend: bandera `is_superuser` de los claims del access token o, en su defecto,
 * del perfil de membresía resuelto durante el login.
 */
export function usePermisosComerciales() {
  const authStore = useAuthStore();

  const token = computed(() => authStore.token);
  const claims = computed(() => decodificarToken(token.value) || {});

  const esPropietario = computed(() => {
    const candidata = claims.value.is_superuser ?? claims.value.superuser ?? claims.value.es_propietario;
    const valor = candidata === undefined ? Boolean(authStore.membresia?.es_propietario) : candidata;
    return aBandera(valor);
  });

  const puedeGestionarComercial = computed(() => esPropietario.value);

  return {
    esPropietario,
    puedeGestionarComercial,
    token,
    claims,
  };
}
