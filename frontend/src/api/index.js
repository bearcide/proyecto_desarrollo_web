/**
 * Instancia de Axios para la API REST del backend SaaS B2B InscripcionMadeEasy.
 * Base URL: /api/v1/ (configurable por VITE_API_BASE_URL)
 */
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

/** Decodifica el payload (claims) de un JWT para leer user_id u otros datos si se requiere */
export function decodificarToken(token) {
  try {
    const partes = token.split('.');
    return JSON.parse(atob(partes[1].replace(/-/g, '+').replace(/_/g, '/')));
  } catch (_) {
    return null;
  }
}

/** Extrae un mensaje de error legible para el usuario a partir de respuestas Problem Details o DRF */
export function obtenerMensajeError(error) {
  if (!error) return 'Ha ocurrido un error inesperado.';
  // Sin respuesta del servidor (caído, sin red, CORS, timeout): mensaje entendible
  if (error.request && !error.response) {
    if (error.code === 'ECONNABORTED') {
      return 'El servidor tardó demasiado en responder. Inténtalo de nuevo.';
    }
    return 'No pudimos conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.';
  }
  const status = error.response?.status;
  if (status >= 500) {
    return 'El servidor tuvo un problema al procesar la solicitud. Inténtalo de nuevo en unos minutos.';
  }
  const data = error.response?.data;
  if (!data) return error.message || 'No pudimos completar la operación. Inténtalo de nuevo.';

  if (typeof data === 'string') return data;
  if (data.detail) return data.detail;
  if (data.mensaje) return data.mensaje;
  if (data.title) return data.title;

  if (Array.isArray(data.invalid_params) && data.invalid_params.length > 0) {
    return data.invalid_params.map((p) => `${p.name}: ${p.reason}`).join(' | ');
  }

  if (Array.isArray(data.errores) && data.errores.length > 0) {
    const primerError = data.errores[0];
    return `Error en ${primerError.archivo || 'archivo'} (fila ${primerError.fila || '?'}): ${primerError.mensaje || primerError.campo}`;
  }

  if (typeof data === 'object') {
    const firstKey = Object.keys(data)[0];
    const val = data[firstKey];
    if (Array.isArray(val)) return `${firstKey}: ${val[0]}`;
    if (typeof val === 'string') return `${firstKey}: ${val}`;
  }

  return 'No se pudo completar la operación.';
}

// Interceptor de REQUEST: inyecta token Bearer y cabecera de aislamiento escolar X-Tenant-ID
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('ime_token');
    const tenantId = localStorage.getItem('ime_tenant_id');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    if (tenantId) {
      config.headers['X-Tenant-ID'] = tenantId;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

let refrescando = false;
let peticionesEnEspera = [];

function ejecutarEspera(nuevoToken, err = null) {
  peticionesEnEspera.forEach((p) => {
    if (err) p.reject(err);
    else p.resolve(nuevoToken);
  });
  peticionesEnEspera = [];
}

// Interceptor de RESPONSE: manejo de 401 y refresco transparente con JWT
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const peticionOriginal = error.config;
    if (error.response?.status === 401 && peticionOriginal && !peticionOriginal._reintento) {
      // Si la petición original era de login o refresco, no reintentar
      if (peticionOriginal.url?.includes('/token/')) {
        return Promise.reject(error);
      }

      const refreshToken = localStorage.getItem('ime_refresh');
      if (!refreshToken) {
        localStorage.removeItem('ime_token');
        localStorage.removeItem('ime_refresh');
        localStorage.removeItem('ime_tenant_id');
        localStorage.removeItem('ime_alumno');
        localStorage.removeItem('ime_admin');
        return Promise.reject(error);
      }

      if (refrescando) {
        return new Promise((resolve, reject) => {
          peticionesEnEspera.push({ resolve, reject });
        })
          .then((nuevoToken) => {
            peticionOriginal.headers.Authorization = `Bearer ${nuevoToken}`;
            return api(peticionOriginal);
          })
          .catch((err) => Promise.reject(err));
      }

      peticionOriginal._reintento = true;
      refrescando = true;

      try {
        const { data } = await axios.post(
          `${api.defaults.baseURL}/token/refresh/`,
          { refresh: refreshToken },
          { headers: { 'Content-Type': 'application/json' } },
        );
        const nuevoToken = data.access;
        localStorage.setItem('ime_token', nuevoToken);
        api.defaults.headers.common.Authorization = `Bearer ${nuevoToken}`;
        peticionOriginal.headers.Authorization = `Bearer ${nuevoToken}`;
        ejecutarEspera(nuevoToken, null);
        return api(peticionOriginal);
      } catch (errRefresco) {
        ejecutarEspera(null, errRefresco);
        localStorage.removeItem('ime_token');
        localStorage.removeItem('ime_refresh');
        localStorage.removeItem('ime_tenant_id');
        localStorage.removeItem('ime_alumno');
        localStorage.removeItem('ime_admin');
        return Promise.reject(errRefresco);
      } finally {
        refrescando = false;
      }
    }
    return Promise.reject(error);
  },
);

export default api;
