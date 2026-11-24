import { expect, it, vi } from 'vitest';
import { nextTick } from 'vue';
import axios, { AxiosError } from 'axios';
import api from './api';
import router from './router';

const settle = async () => {
  for (let i = 0; i < 8; i++) await new Promise((resolve) => setTimeout(resolve, 0));
  await nextTick();
};

it('mantiene las vistas al navegar, renovar JWT y recibir errores HTTP; expira hacia login', async () => {
  localStorage.clear();
  localStorage.setItem('ime_token', 'anterior');
  localStorage.setItem('ime_refresh', 'refresh');
  localStorage.setItem('ime_tenant_id', 'escuela');
  localStorage.setItem('ime_membresia', JSON.stringify({ es_administrador: true }));
  const root = document.createElement('div');
  root.id = 'app';
  document.body.append(root);
  const originalAdapter = api.defaults.adapter;
  let status = 200;
  api.defaults.adapter = async (config) => {
    const response = { config, status, data: [], headers: {}, statusText: '' };
    if (status !== 200) throw new AxiosError('Fallo simulado', '', config, null, response);
    return response;
  };
  const refresh = vi.spyOn(axios, 'post').mockImplementation(async () => {
    status = 200;
    return { data: { access: 'renovado' } };
  });
  const errors = vi.spyOn(console, 'error').mockImplementation(() => {});
  try {
    await import('./main');
    await router.isReady();
    for (const failure of [200, 500, 401, 200]) {
      status = failure;
      for (const name of ['importar', 'alumnos', 'grupos', 'planes']) {
        await router.push(`/admin/${name}`);
        await settle();
        expect(root.querySelector(`.${name}-page`)).not.toBeNull();
        expect(root.querySelector('.error-boundary-card')).toBeNull();
        if (name === 'importar') {
          const textarea = root.querySelector('textarea');
          textarea.value = 'á'.repeat(512);
          textarea.dispatchEvent(new Event('input', { bubbles: true }));
          await nextTick();
          expect(root.querySelector('.csv-meta-info').textContent).toContain('1.0 KB');
        }
      }
    }
    expect(refresh).toHaveBeenCalledTimes(1);
    const { useAuthStore } = await import('./stores/auth');
    expect(useAuthStore().token).toBe('renovado');
    refresh.mockRejectedValue(new Error('Refresh expirado'));
    status = 401;
    await router.push('/admin/alumnos');
    await settle();
    expect(router.currentRoute.value.path).toBe('/login');
    expect(root.querySelector('.admin-content')).toBeNull();
    expect(useAuthStore().estaAutenticado).toBe(false);
    await router.push('/admin/planes');
    expect(router.currentRoute.value.path).toBe('/login');
    expect(errors.mock.calls.filter(([message]) => String(message).includes('[AdminLayout]'))).toEqual([]);
  } finally {
    api.defaults.adapter = originalAdapter;
    refresh.mockRestore();
    errors.mockRestore();
    root.remove();
  }
});
