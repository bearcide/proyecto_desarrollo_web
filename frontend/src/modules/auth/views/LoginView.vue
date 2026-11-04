<template>
  <div class="auth-page">
    <div class="auth-card">
      <!-- Header con Identidad Visual SaaS -->
      <div class="auth-header">
        <div class="brand-badge">
          <div class="brand-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/>
              <path d="M6 6h10"/>
              <path d="M6 10h10"/>
            </svg>
          </div>
          <span class="brand-text">InscripcionMadeEasy</span>
        </div>
        <h1 class="auth-title">Iniciar Sesión</h1>
        <p class="auth-subtitle">Accede a tu portal institucional de horarios e inscripciones</p>
      </div>

      <!-- Alerta de Error -->
      <div v-if="errorMsg" class="alert alert-danger" role="alert">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <div>{{ errorMsg }}</div>
      </div>

      <!-- Formulario de Autenticación Real -->
      <form class="auth-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="matricula" class="form-label">Matrícula o Usuario Institucional</label>
          <div class="input-with-icon">
            <svg class="input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            <input
              id="matricula"
              v-model="matricula"
              type="text"
              class="form-input"
              placeholder="Ej. demo_admin o D001"
              autocomplete="username"
              required
              :disabled="cargando"
            />
          </div>
        </div>

        <div class="form-group">
          <label for="password" class="form-label">Contraseña</label>
          <div class="input-with-icon">
            <svg class="input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            <input
              id="password"
              v-model="password"
              :type="mostrarPassword ? 'text' : 'password'"
              class="form-input"
              placeholder="••••••••••••"
              autocomplete="current-password"
              required
              :disabled="cargando"
            />
            <button
              type="button"
              class="toggle-pass-btn"
              @click="mostrarPassword = !mostrarPassword"
              tabindex="-1"
            >
              {{ mostrarPassword ? 'Ocultar' : 'Ver' }}
            </button>
          </div>
        </div>

        <button
          type="submit"
          class="btn btn-primary btn-lg auth-submit-btn"
          :disabled="cargando || !matricula.trim() || !password"
        >
          <span v-if="cargando" class="spinner"></span>
          <span>{{ cargando ? 'Verificando credenciales…' : 'Ingresar al Portal' }}</span>
        </button>
      </form>

      <!-- Accesos Rápidos de Demostración Local -->
      <div class="demo-helpers">
        <div class="demo-helpers-title">Cuentas de demostración rápida:</div>
        <div class="demo-pills">
          <button
            type="button"
            class="demo-pill"
            @click="cargarCredenciales('demo_admin', 'DemoLocal2026!')"
          >
            <span class="badge badge-indigo">Admin</span>
            <span>demo_admin</span>
          </button>
          <button
            type="button"
            class="demo-pill"
            @click="cargarCredenciales('D001', 'DemoLocal2026!')"
          >
            <span class="badge badge-success">Alumno</span>
            <span>D001</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../../../stores/auth';
import { useNotificationStore } from '../../../stores/notification';
import { obtenerMensajeError } from '../../../api';

const authStore = useAuthStore();
const notifStore = useNotificationStore();
const router = useRouter();

const matricula = ref('');
const password = ref('');
const cargando = ref(false);
const errorMsg = ref(null);
const mostrarPassword = ref(false);

function cargarCredenciales(u, p) {
  matricula.value = u;
  password.value = p;
  errorMsg.value = null;
}

async function handleLogin() {
  errorMsg.value = null;
  cargando.value = true;

  try {
    const res = await authStore.login(matricula.value.trim(), password.value);
    notifStore.success(`Bienvenido a ${authStore.nombreEscuela}`);

    // Redirección condicionada por el rol verificado en Django
    if (res.es_administrador) {
      router.push('/admin/dashboard');
    } else if (res.es_alumno) {
      router.push('/alumno/horario');
    } else {
      router.push(authStore.rutaInicio);
    }
  } catch (err) {
    errorMsg.value = obtenerMensajeError(err);
  } finally {
    cargando.value = false;
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  background: radial-gradient(circle at 10% 20%, rgba(79, 70, 229, 0.08) 0%, transparent 40%),
              radial-gradient(circle at 90% 80%, rgba(124, 58, 237, 0.08) 0%, transparent 40%),
              var(--bg-main);
}

.auth-card {
  width: 100%;
  max-width: 440px;
  background-color: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 2.25rem 2rem;
  box-shadow: var(--shadow-xl);
}

.auth-header {
  text-align: center;
  margin-bottom: 1.75rem;
}

.brand-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 1rem;
}

.brand-icon {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--primary) 0%, var(--violet) 100%);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 10px rgba(79, 70, 229, 0.3);
}

.brand-text {
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, var(--primary-dark) 0%, var(--violet) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.auth-title {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--text-main);
  margin-bottom: 0.35rem;
}

.auth-subtitle {
  font-size: 0.875rem;
  color: var(--text-muted);
}

.auth-form {
  display: flex;
  flex-direction: column;
}

.input-with-icon {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 0.85rem;
  color: var(--text-light);
  pointer-events: none;
}

.input-with-icon .form-input {
  padding-left: 2.5rem;
  padding-right: 3.5rem;
}

.toggle-pass-btn {
  position: absolute;
  right: 0.75rem;
  background: none;
  border: none;
  font-size: 0.775rem;
  font-weight: 600;
  color: var(--primary);
  cursor: pointer;
  padding: 0.2rem 0.4rem;
}

.toggle-pass-btn:hover {
  color: var(--primary-hover);
}

.auth-submit-btn {
  width: 100%;
  margin-top: 0.75rem;
}

.demo-helpers {
  margin-top: 2rem;
  padding-top: 1.25rem;
  border-top: 1px dashed var(--border);
  text-align: center;
}

.demo-helpers-title {
  font-size: 0.775rem;
  color: var(--text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 0.65rem;
}

.demo-pills {
  display: flex;
  gap: 0.65rem;
  justify-content: center;
}

.demo-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.65rem;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-main);
  cursor: pointer;
  transition: all 0.15s ease;
}

.demo-pill:hover {
  background-color: var(--primary-light);
  border-color: var(--primary-border);
}
</style>
