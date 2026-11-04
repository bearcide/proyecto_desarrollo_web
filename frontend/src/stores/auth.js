import { defineStore } from 'pinia';
import api, { decodificarToken } from '../api';

function obtenerStorage(key, parseJson = false) {
  try {
    const val = localStorage.getItem(key);
    if (!val) return null;
    return parseJson ? JSON.parse(val) : val;
  } catch (_) {
    return null;
  }
}

/**
 * Estado global de sesión, tenant y perfil del usuario en InscripcionMadeEasy.
 */
export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: obtenerStorage('ime_token'),
    refresh: obtenerStorage('ime_refresh'),
    tenantId: obtenerStorage('ime_tenant_id'),
    membresia: obtenerStorage('ime_membresia', true),
    alumno: obtenerStorage('ime_alumno', true),
    usuarioMatricula: obtenerStorage('ime_usuario') || '',
    cargandoSesion: false,
  }),

  getters: {
    estaAutenticado: (state) => Boolean(state.token && state.tenantId),
    esAdministrador: (state) => Boolean(state.membresia?.es_administrador),
    esAlumno: (state) => Boolean(state.membresia?.es_alumno),
    nombreEscuela: (state) => state.membresia?.nombre_escuela || 'Escuela',
    rutaInicio: (state) => {
      if (state.membresia?.es_administrador) return '/admin/dashboard';
      if (state.membresia?.es_alumno) return '/alumno/horario';
      return '/login';
    },
    nombreCompleto: (state) => {
      if (state.alumno) {
        return [state.alumno.nombre, state.alumno.apellido_paterno, state.alumno.apellido_materno]
          .filter(Boolean)
          .join(' ') || state.alumno.numero_de_cuenta;
      }
      return state.usuarioMatricula || 'Usuario';
    },
    matriculaOId: (state) => state.alumno?.numero_de_cuenta || state.usuarioMatricula || '',
  },

  actions: {
    /**
     * Autenticación con JWT (POST /token/) y resolución de membresía escolar.
     */
    async login(matricula, password) {
      // 1. Obtención de tokens
      const { data } = await api.post('/token/', { matricula, password });
      this.token = data.access;
      this.refresh = data.refresh;
      this.usuarioMatricula = matricula;

      localStorage.setItem('ime_token', data.access);
      localStorage.setItem('ime_refresh', data.refresh);
      localStorage.setItem('ime_usuario', matricula);

      // 2. Consulta de membresías para resolver escuela (tenant) y roles
      const respMem = await api.get('/membresias/me/');
      const membresias = Array.isArray(respMem.data) ? respMem.data : [];

      if (!membresias.length) {
        throw new Error('Tu usuario no cuenta con ninguna membresía escolar registrada.');
      }

      const activa = membresias.find((m) => m.activo && m.estado_escuela === 'ACTIVO') || membresias[0];

      if (!activa || !activa.activo) {
        throw new Error('Tu membresía escolar se encuentra inactiva o la escuela no está disponible.');
      }

      this.tenantId = activa.tenant;
      this.membresia = activa;
      localStorage.setItem('ime_tenant_id', activa.tenant);
      localStorage.setItem('ime_membresia', JSON.stringify(activa));

      // 3. Si el usuario es alumno, cargar su perfil institucional
      if (activa.es_alumno) {
        try {
          const rAlumno = await api.get('/alumnos/me/');
          this.alumno = rAlumno.data;
          localStorage.setItem('ime_alumno', JSON.stringify(rAlumno.data));
        } catch (e) {
          console.warn('No se pudo cargar el perfil detallado del alumno:', e);
        }
      } else {
        this.alumno = null;
        localStorage.removeItem('ime_alumno');
      }

      return {
        tenant: activa.tenant,
        es_administrador: activa.es_administrador,
        es_alumno: activa.es_alumno,
      };
    },

    /**
     * Actualiza el perfil del alumno en sesión si es necesario
     */
    async recargarPerfilAlumno() {
      if (this.esAlumno) {
        try {
          const r = await api.get('/alumnos/me/');
          this.alumno = r.data;
          localStorage.setItem('ime_alumno', JSON.stringify(r.data));
          return r.data;
        } catch (_) {
          // Ignorar error si no está disponible
        }
      }
      return null;
    },

    /**
     * Cierre total de sesión y limpieza de almacenamiento local
     */
    logout() {
      this.token = null;
      this.refresh = null;
      this.tenantId = null;
      this.membresia = null;
      this.alumno = null;
      this.usuarioMatricula = '';

      localStorage.removeItem('ime_token');
      localStorage.removeItem('ime_refresh');
      localStorage.removeItem('ime_tenant_id');
      localStorage.removeItem('ime_membresia');
      localStorage.removeItem('ime_alumno');
      localStorage.removeItem('ime_usuario');
    },
  },
});
