import { beforeEach, afterEach, expect, it, vi } from 'vitest';
import axios, { AxiosError } from 'axios';

let api;
beforeEach(async () => {
  vi.resetModules();
  localStorage.clear();
  localStorage.setItem('ime_token', 'viejo');
  localStorage.setItem('ime_refresh', 'refresh');
  api = (await import('./index')).default;
});
afterEach(() => vi.restoreAllMocks());

function unauthorized(config) {
  throw new AxiosError('Unauthorized', '', config, null, { status: 401, config, data: {} });
}

it('comparte una renovación entre peticiones simultáneas y limita cada una a un reintento', async () => {
  let finishRefresh;
  const refresh = vi.spyOn(axios, 'post').mockImplementation(() => new Promise((resolve) => {
    finishRefresh = resolve;
  }));
  const attempts = {};
  api.defaults.adapter = async (config) => {
    attempts[config.url] = (attempts[config.url] || 0) + 1;
    return unauthorized(config);
  };
  const requests = Promise.allSettled([api.get('/alumnos/'), api.get('/planes-estudios/')]);
  await vi.waitFor(() => expect(finishRefresh).toBeTypeOf('function'));
  finishRefresh({ data: { access: 'nuevo' } });
  expect((await requests).map((r) => r.status)).toEqual(['rejected', 'rejected']);
  expect(refresh).toHaveBeenCalledTimes(1);
  expect(attempts).toEqual({ '/alumnos/': 2, '/planes-estudios/': 2 });
  expect(localStorage.getItem('ime_token')).toBeNull();
  expect(api.defaults.headers.common.Authorization).toBeUndefined();
});

it('rechaza toda la cola cuando falla la renovación y permite una sesión posterior', async () => {
  const refresh = vi.spyOn(axios, 'post').mockRejectedValue(new Error('Refresh inválido'));
  api.defaults.adapter = async (config) => unauthorized(config);
  const result = await Promise.allSettled([api.get('/alumnos/'), api.get('/nodos/')]);
  expect(result.every((r) => r.status === 'rejected')).toBe(true);
  expect(refresh).toHaveBeenCalledTimes(1);
  localStorage.setItem('ime_token', 'otra-sesion');
  api.defaults.adapter = async (config) => ({ config, status: 200, data: [] });
  const response = await api.get('/alumnos/');
  expect(response.config.headers.Authorization).toBe('Bearer otra-sesion');
});

it('elimina Authorization heredado al salir y no renueva un login rechazado', async () => {
  const refresh = vi.spyOn(axios, 'post');
  api.defaults.headers.common.Authorization = 'Bearer obsoleto';
  localStorage.clear();
  let headers;
  api.defaults.adapter = async (config) => {
    headers = config.headers;
    return unauthorized(config);
  };
  await expect(api.post('/token/', {})).rejects.toBeInstanceOf(AxiosError);
  expect(headers.Authorization).toBeUndefined();
  expect(refresh).not.toHaveBeenCalled();
});
