/**
 * Capa de acceso a la API REST (Django DRF, /api/v1/).
 *
 * - apiFetch(): ÚNICO punto por el que sale tráfico al backend. Inyecta headers,
 *   serializa JSON y normaliza errores (ApiError).
 * - Session: token + alumno actual (sessionStorage).
 * - API: un método por recurso del backend.
 *
 * Multi-tenant: el backend resuelve la escuela desde request.user.tenant (usuario
 * autenticado). NO lee un header de tenant: el aislamiento no se negocia desde aquí.
 */
(function (root) {
  'use strict';

  let CFG = root.APP_CONFIG;
  if (!CFG) {
    const el = root.document && root.document.getElementById('app-config');
    try { CFG = el ? JSON.parse(el.textContent) : {}; } catch (_) { CFG = {}; }
  }
  const BASE = String(CFG.apiBaseUrl || '/api/v1').replace(/\/+$/, '');
  const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS']);
  const KEYS = { token: 'ime.token', alumno: 'ime.alumno' };

  // ---------- almacenamiento (tolerante a modo privado / SSR) ----------
  const store = {
    get(k) { try { return root.sessionStorage.getItem(k); } catch (_) { return null; } },
    set(k, v) { try { root.sessionStorage.setItem(k, v); } catch (_) { /* noop */ } },
    del(k) { try { root.sessionStorage.removeItem(k); } catch (_) { /* noop */ } },
  };

  const Session = {
    token() { return store.get(KEYS.token) || CFG.devToken || null; },
    setToken(t) { t ? store.set(KEYS.token, t) : store.del(KEYS.token); },
    alumno() { try { return JSON.parse(store.get(KEYS.alumno)); } catch (_) { return null; } },
    setAlumno(a) { store.set(KEYS.alumno, JSON.stringify(a)); },
    clear() { store.del(KEYS.token); store.del(KEYS.alumno); },
    activa() { return Boolean(Session.alumno()); },
  };

  // ---------- errores ----------
  class ApiError extends Error {
    constructor(status, message, fields) {
      super(message);
      this.name = 'ApiError';
      this.status = status;
      this.fields = fields || null;
    }
  }

  function aplanar(data) {
    if (data == null) return '';
    if (typeof data === 'string') return data;
    if (Array.isArray(data)) return data.map(aplanar).filter(Boolean).join(' ');
    return Object.entries(data)
      .map(([campo, v]) => (campo === 'detail' || campo === 'non_field_errors' ? '' : `${campo}: `) + aplanar(v))
      .join(' ');
  }

  const POR_DEFECTO = {
    401: 'Tu sesión expiró. Inicia sesión de nuevo.',
    403: 'No tienes permiso para ver esta información.',
    404: 'No encontramos lo que buscabas.',
    409: 'La operación choca con datos existentes.',
  };

  // ---------- helpers HTTP ----------
  function buildUrl(path, params) {
    const url = /^https?:\/\//i.test(path) ? path : `${BASE}/${String(path).replace(/^\/+/, '')}`;
    if (!params) return url;
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== null && v !== '') qs.append(k, v); });
    const s = qs.toString();
    return s ? url + (url.includes('?') ? '&' : '?') + s : url;
  }

  function csrfCookie() {
    const m = root.document && root.document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/);
    return m ? decodeURIComponent(m[1]) : null;
  }

  async function leer(res) {
    if (res.status === 204) return null;
    const texto = await res.text();
    if (!texto) return null;
    try { return JSON.parse(texto); } catch (_) { return texto; }
  }

  /**
   * apiFetch(path, { method, body, params, headers, auth, signal })
   * Devuelve el JSON ya parseado o lanza ApiError.
   */
  async function apiFetch(path, opts = {}) {
    const { method = 'GET', body, params, headers = {}, auth = true, signal } = opts;
    const h = { Accept: 'application/json', 'Content-Type': 'application/json', ...headers };

    if (auth) {
      const token = Session.token();
      if (token) h.Authorization = `${CFG.authScheme || 'Bearer'} ${token}`;
      // Solo si se configura. OJO: requiere agregar x-tenant-id a CORS_ALLOW_HEADERS en el backend.
      if (CFG.tenantId) h['X-Tenant-ID'] = CFG.tenantId;
    }
    // SessionAuthentication (estado actual del backend) exige CSRF en métodos no seguros.
    if (CFG.withCredentials && !SAFE_METHODS.has(method.toUpperCase())) {
      const csrf = csrfCookie();
      if (csrf) h['X-CSRFToken'] = csrf;
    }

    let res;
    try {
      res = await fetch(buildUrl(path, params), {
        method,
        headers: h,
        body: body === undefined ? undefined : JSON.stringify(body),
        credentials: CFG.withCredentials ? 'include' : 'same-origin',
        signal,
      });
    } catch (e) {
      if (e && e.name === 'AbortError') throw e;
      throw new ApiError(0, 'No se pudo conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.');
    }

    const data = await leer(res);
    if (res.ok) return data;

    if (res.status === 401 && auth) {
      Session.clear();
      root.dispatchEvent && root.dispatchEvent(new root.CustomEvent('ime:unauthorized'));
    }
    const detalle = aplanar(data).trim();
    const mensaje = detalle && typeof data === 'object'
      ? detalle
      : POR_DEFECTO[res.status] || (res.status >= 500 ? 'El servidor tuvo un problema. Inténtalo en unos minutos.' : `Error ${res.status}.`);
    throw new ApiError(res.status, mensaje, data && typeof data === 'object' ? data : null);
  }

  /** Recorre la paginación de DRF ({count, next, results}) y devuelve el arreglo completo. */
  async function apiList(path, params) {
    let data = await apiFetch(path, { params });
    if (Array.isArray(data)) return data;
    const todos = [...(data.results || [])];
    for (let i = 0; data.next && i < 50; i++) {
      data = await apiFetch(data.next); // `next` ya es una URL absoluta con ?page=
      todos.push(...(data.results || []));
    }
    return todos;
  }

  // ---------- recursos del backend ----------
  const API = {
    tenants: { list: () => apiList('tenants/') },
    planes: {
      list: (p) => apiList('planes-estudios/', p),
      get: (id) => apiFetch(`planes-estudios/${id}/`),
    },
    nodos: { list: (p) => apiList('nodos/', p) },
    prerrequisitos: { list: (p) => apiList('prerrequisitos/', p) },
    estadisticas: { list: (p) => apiList('estadisticas-nodos/', p) },
    alumnos: {
      list: (p) => apiList('alumnos/', p),
      get: (id) => apiFetch(`alumnos/${id}/`),
      /** El login usa la matrícula = numero_de_cuenta. El filtro ?search= es "contiene", así que se afina aquí. */
      async porCuenta(cuenta) {
        const lista = await apiList('alumnos/', { search: cuenta });
        return lista.find((a) => a.numero_de_cuenta === String(cuenta).trim()) || null;
      },
    },
    // El backend aún NO expone inscripciones. Cuando exista, definirlo aquí y el botón "Confirmar" lo usará.
    inscripciones: null,
  };

  // ---------- login ----------
  const Auth = {
    async login(matricula, password) {
      if (CFG.loginPath) {
        const r = await apiFetch(CFG.loginPath, { method: 'POST', auth: false, body: { matricula, password } });
        Session.setToken(r.access || r.token || null);
      } else if (CFG.devToken) {
        Session.setToken(CFG.devToken); // modo simulado: la contraseña NO se valida
      }
      const alumno = await API.alumnos.porCuenta(matricula);
      if (!alumno) throw new ApiError(404, 'No encontramos esa matrícula en tu escuela.');
      Session.setAlumno(alumno);
      return alumno;
    },
    logout() { Session.clear(); root.location.assign(CFG.urls.login); },
  };

  /** Protege páginas privadas. Devuelve el alumno o redirige al login (y devuelve null). */
  function requireSesion() {
    const a = Session.alumno();
    if (!a) { root.location.replace(`${CFG.urls.login}?next=${encodeURIComponent(root.location.pathname)}`); return null; }
    return a;
  }

  root.addEventListener && root.addEventListener('ime:unauthorized', () => {
    if (!/login/.test(root.location.pathname)) root.location.replace(CFG.urls.login);
  });

  if (root.document) {
    root.document.addEventListener('DOMContentLoaded', () => {
      const btn = root.document.getElementById('btn-sesion');
      if (btn && Session.activa()) {
        btn.textContent = 'Cerrar sesión';
        btn.setAttribute('href', '#');
        btn.addEventListener('click', (e) => { e.preventDefault(); Auth.logout(); });
      }
    });
  }

  root.IME = Object.assign(root.IME || {}, { CFG, apiFetch, apiList, API, Auth, Session, ApiError, requireSesion });
})(typeof window !== 'undefined' ? window : globalThis);
