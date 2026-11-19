<template>
  <div class="auth-page">
    <!-- Fondo animado: ondas en el agua (decorativo) -->
    <div class="water" aria-hidden="true">
      <div class="water-glow water-glow--a"></div>
      <div class="water-glow water-glow--b"></div>
      <span
        v-for="(r, i) in ondas"
        :key="i"
        class="ripple"
        :style="{ '--x': r.x, '--y': r.y, '--delay': r.delay, '--s': r.s }"
      ></span>
    </div>

    <!-- Cambio de tema: discreto, arriba a la derecha -->
    <ThemeToggle class="theme-fab" />

    <main class="auth-card">
      <!-- Encabezado -->
      <header class="auth-header">
        <div class="brand-badge">
          <div class="brand-icon" aria-hidden="true">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/>
              <path d="M6 6h10"/>
              <path d="M6 10h10"/>
            </svg>
          </div>
          <span class="brand-text">InscripcionMadeEasy</span>
        </div>
        <h1 class="auth-title">Iniciar sesión</h1>
        <p class="auth-subtitle">Accede a tu portal institucional de horarios e inscripciones</p>
      </header>

      <!-- Error: recibe el foco para que el lector de pantalla lo anuncie -->
      <div
        v-if="errorMsg"
        id="login-error"
        ref="errorRef"
        class="alert alert-danger auth-alert"
        tabindex="-1"
      >
        <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <div>{{ errorMsg }}</div>
      </div>

      <form class="auth-form" novalidate @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="matricula" class="form-label">Matrícula o usuario institucional</label>
          <div class="input-with-icon">
            <svg class="input-icon" aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            <input
              id="matricula"
              v-model="matricula"
              type="text"
              class="form-input"
              placeholder="Ej. demo_admin o D001"
              autocomplete="username"
              autocapitalize="none"
              spellcheck="false"
              required
              :disabled="cargando"
              :aria-invalid="errorMsg ? 'true' : undefined"
              :aria-describedby="errorMsg ? 'login-error' : undefined"
            />
          </div>
        </div>

        <div class="form-group">
          <label for="password" class="form-label">Contraseña</label>
          <div class="input-with-icon">
            <svg class="input-icon" aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            <input
              id="password"
              v-model="password"
              :type="mostrarPassword ? 'text' : 'password'"
              class="form-input has-toggle"
              autocomplete="current-password"
              required
              :disabled="cargando"
              :aria-invalid="errorMsg ? 'true' : undefined"
              :aria-describedby="errorMsg ? 'login-error' : undefined"
            />
            <button
              type="button"
              class="toggle-pass-btn"
              aria-controls="password"
              :aria-pressed="mostrarPassword ? 'true' : 'false'"
              :aria-label="mostrarPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'"
              :disabled="cargando"
              @click="mostrarPassword = !mostrarPassword"
            >
              <!-- Ojo tachado (ocultar) -->
              <svg v-if="mostrarPassword" aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.53 13.53 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" y1="2" x2="22" y2="22"/></svg>
              <!-- Ojo (mostrar) -->
              <svg v-else aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
            </button>
          </div>
        </div>

        <button
          type="submit"
          class="btn btn-primary auth-submit-btn"
          :aria-busy="cargando ? 'true' : 'false'"
          :disabled="cargando || !matricula.trim() || !password"
        >
          <span v-if="cargando" class="spinner" aria-hidden="true"></span>
          <span>{{ cargando ? 'Iniciando sesión…' : 'Iniciar sesión' }}</span>
        </button>
      </form>

      <!-- Accesos rápidos de demostración local -->
      <div class="demo-helpers">
        <div class="demo-helpers-title" id="demo-title">Cuentas de demostración rápida</div>
        <div class="demo-pills" role="group" aria-labelledby="demo-title">
          <button
            type="button"
            class="demo-pill"
            aria-label="Usar cuenta de demostración de administrador, demo_admin"
            @click="cargarCredenciales('demo_admin', 'DemoLocal2026!')"
          >
            <span class="badge badge-indigo">Admin</span>
            <span>demo_admin</span>
          </button>
          <button
            type="button"
            class="demo-pill"
            aria-label="Usar cuenta de demostración de alumno, D001"
            @click="cargarCredenciales('D001', 'DemoLocal2026!')"
          >
            <span class="badge badge-success">Alumno</span>
            <span>D001</span>
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../../../stores/auth';
import { useNotificationStore } from '../../../stores/notification';
import { obtenerMensajeError } from '../../../api';
import ThemeToggle from '../../../components/ThemeToggle.vue';

const authStore = useAuthStore();
const notifStore = useNotificationStore();
const router = useRouter();

const matricula = ref('');
const password = ref('');
const cargando = ref(false);
const errorMsg = ref(null);
const errorRef = ref(null);
const mostrarPassword = ref(false);

// Ondas del fondo: origen (x, y), desfase y escala para la versión estática (movimiento reducido)
const ondas = [
  { x: '18%', y: '28%', delay: '0s', s: 0.3 },
  { x: '18%', y: '28%', delay: '-3.4s', s: 0.55 },
  { x: '18%', y: '28%', delay: '-6.8s', s: 0.8 },
  { x: '84%', y: '74%', delay: '-1.7s', s: 0.35 },
  { x: '84%', y: '74%', delay: '-5.1s', s: 0.6 },
  { x: '84%', y: '74%', delay: '-8.5s', s: 0.85 },
  { x: '62%', y: '8%', delay: '-2.5s', s: 0.25 },
  { x: '62%', y: '8%', delay: '-7.6s', s: 0.5 },
];

// Al corregir los datos, el error deja de aplicar
watch([matricula, password], () => {
  if (errorMsg.value && !cargando.value) errorMsg.value = null;
});

function cargarCredenciales(u, p) {
  matricula.value = u;
  password.value = p;
  errorMsg.value = null;
}

async function handleLogin() {
  if (!matricula.value.trim() || !password.value) return;
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
    cargando.value = false;
    errorMsg.value = obtenerMensajeError(err);
    await nextTick();
    errorRef.value?.focus();
  } finally {
    cargando.value = false;
  }
}
</script>

<style scoped>
/* ---------- Tokens locales (claro) ---------- */
.auth-page {
  --card-glass-bg: var(--glass-bg);
  --card-glass-border: var(--glass-border);
  --card-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 24px 60px -12px rgba(15, 23, 42, 0.14);
  --ripple-color: rgba(79, 70, 229, 0.22);
  --ripple-glow: rgba(79, 70, 229, 0.06);
  --glow-a: rgba(79, 70, 229, 0.16);
  --glow-b: rgba(124, 58, 237, 0.12);

  position: relative;
  isolation: isolate;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  background-color: var(--bg-main);
  color: var(--text-main);
  overflow: hidden;
}

/* ---------- Tokens locales (oscuro: lo decide <html data-theme>) ---------- */
:root[data-theme="dark"] .auth-page {
  --card-glass-bg: rgba(28, 28, 30, 0.72);
  --card-shadow:
    0 1px 0 rgba(255, 255, 255, 0.04) inset,
    0 30px 70px -12px rgba(0, 0, 0, 0.7);
  --ripple-color: rgba(165, 180, 252, 0.2);
  --ripple-glow: rgba(129, 140, 248, 0.07);
  --glow-a: rgba(79, 70, 229, 0.28);
  --glow-b: rgba(124, 58, 237, 0.2);
}

/* ---------- Botón de tema flotante ---------- */
.theme-fab {
  position: fixed;
  top: calc(env(safe-area-inset-top, 0px) + 1rem);
  right: calc(env(safe-area-inset-right, 0px) + 1rem);
  z-index: 10;
}

/* ---------- Fondo: ondas en el agua ---------- */
.water {
  position: fixed;
  inset: 0;
  z-index: -1;
  overflow: hidden;
  pointer-events: none;
}

.water-glow {
  position: absolute;
  width: 70vmax;
  height: 70vmax;
  border-radius: 50%;
  filter: blur(40px);
  animation: drift 26s ease-in-out infinite alternate;
}

.water-glow--a {
  top: -28vmax;
  left: -22vmax;
  background: radial-gradient(circle, var(--glow-a) 0%, transparent 65%);
}

.water-glow--b {
  bottom: -32vmax;
  right: -22vmax;
  background: radial-gradient(circle, var(--glow-b) 0%, transparent 65%);
  animation-delay: -13s;
}

.ripple {
  --size: 80vmax;
  position: absolute;
  left: var(--x);
  top: var(--y);
  width: var(--size);
  height: var(--size);
  margin: calc(var(--size) / -2) 0 0 calc(var(--size) / -2);
  border-radius: 50%;
  border: 1.5px solid var(--ripple-color);
  box-shadow: 0 0 30px var(--ripple-glow), inset 0 0 30px var(--ripple-glow);
  opacity: 0;
  transform: scale(0.02);
  animation: ripple 10.2s cubic-bezier(0.2, 0.6, 0.35, 1) infinite;
  animation-delay: var(--delay);
  will-change: transform, opacity;
}

@keyframes ripple {
  0%   { transform: scale(0.02); opacity: 0; }
  12%  { opacity: 1; }
  100% { transform: scale(1); opacity: 0; }
}

@keyframes drift {
  from { transform: translate3d(0, 0, 0) scale(1); }
  to   { transform: translate3d(6vmax, 4vmax, 0) scale(1.08); }
}

/* Movimiento reducido: ondas quietas, sin animación */
@media (prefers-reduced-motion: reduce) {
  .ripple {
    animation: none;
    opacity: 0.45;
    transform: scale(var(--s));
  }
  .water-glow { animation: none; }
}

/* ---------- Tarjeta de vidrio ---------- */
.auth-card {
  width: 100%;
  max-width: 460px;
  background-color: var(--card-glass-bg);
  -webkit-backdrop-filter: blur(28px) saturate(180%);
  backdrop-filter: blur(28px) saturate(180%);
  border: 1px solid var(--card-glass-border);
  border-radius: 22px;
  padding: 2.5rem 2.25rem 2.25rem;
  box-shadow: var(--card-shadow);
}

@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .auth-card { background-color: var(--bg-card); }
}

@media (prefers-reduced-transparency: reduce), (prefers-contrast: more) {
  .auth-card {
    background-color: var(--bg-card);
    -webkit-backdrop-filter: none;
    backdrop-filter: none;
  }
}

/* ---------- Encabezado (escala tipográfica HIG) ---------- */
.auth-header {
  text-align: center;
  margin-bottom: 2rem;
}

.brand-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 1.25rem;
}

.brand-icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background-color: var(--accent);
  color: var(--on-accent);
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-text {
  font-size: 1.0625rem; /* 17px · Headline */
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--accent-text);
}

.auth-title {
  font-size: 2.125rem; /* 34px · Large Title */
  line-height: 1.2;
  font-weight: 700;
  letter-spacing: -0.025em;
  color: var(--text-main);
  margin-bottom: 0.5rem;
}

.auth-subtitle {
  font-size: 0.9375rem; /* 15px · Subheadline */
  line-height: 1.45;
  color: var(--text-muted);
}

.auth-alert {
  margin-bottom: 1.5rem;
}

/* ---------- Formulario ---------- */
.auth-form {
  display: flex;
  flex-direction: column;
}

.auth-form .form-group {
  margin-bottom: 1.25rem;
}

.auth-form .form-label {
  font-size: 0.9375rem; /* 15px */
  margin-bottom: 0.5rem;
  color: var(--text-main);
}

.input-with-icon {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 1rem;
  color: var(--text-light);
  pointer-events: none;
  transition: color 0.15s ease;
}

.input-with-icon:focus-within .input-icon {
  color: var(--accent-text);
}

.auth-form .form-input {
  height: 52px;
  font-size: 1.0625rem; /* 17px · Body */
  border-radius: 12px;
  padding-left: 2.75rem;
  padding-right: 1rem;
}

.auth-form .form-input.has-toggle {
  padding-right: 3.5rem;
}

.auth-form .form-input:disabled {
  opacity: 0.7;
}

.toggle-pass-btn {
  position: absolute;
  right: 4px;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  border-radius: 10px;
  color: var(--text-light);
  cursor: pointer;
  transition: color 0.15s ease, background-color 0.15s ease;
}

.toggle-pass-btn:hover:not(:disabled) {
  color: var(--accent-text);
  background-color: var(--bg-surface);
}

.toggle-pass-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.auth-submit-btn {
  width: 100%;
  min-height: 52px;
  margin-top: 0.75rem;
  font-size: 1.0625rem; /* 17px */
  border-radius: 12px;
}

/* Mientras carga mantiene el acento (no parece "inactivo") */
.auth-submit-btn[aria-busy="true"]:disabled {
  background-color: var(--accent);
  color: var(--on-accent);
  opacity: 0.85;
  cursor: progress;
}

/* ---------- Cuentas demo ---------- */
.demo-helpers {
  margin-top: 2rem;
  padding-top: 1.25rem;
  border-top: 1px dashed var(--border);
  text-align: center;
}

.demo-helpers-title {
  font-size: 0.8125rem; /* 13px · Footnote */
  color: var(--text-muted);
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.demo-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  justify-content: center;
}

.demo-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  min-height: 44px;
  padding: 0.35rem 0.75rem;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  font-family: inherit;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-main);
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.demo-pill:hover {
  background-color: var(--primary-light);
  border-color: var(--primary-border);
}
</style>
