<template>
  <div class="alumno-shell">
    <!-- Navbar Superior del Estudiante -->
    <header class="alumno-navbar">
      <div class="navbar-container">
        <!-- Logo y Marca -->
        <div class="navbar-left">
          <router-link to="/alumno/horario" class="brand-link">
            <div class="brand-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/><path d="M6 6h10"/><path d="M6 10h10"/></svg>
            </div>
            <div class="brand-text-wrap">
              <span class="brand-title">InscripcionMadeEasy</span>
              <span class="brand-sub">Portal del Estudiante</span>
            </div>
          </router-link>

          <!-- Navegación de Escritorio -->
          <nav class="nav-links desktop-nav">
            <router-link to="/alumno/horario" class="nav-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              <span>Mi Horario</span>
            </router-link>

            <router-link to="/alumno/perfil" class="nav-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              <span>Perfil Académico</span>
            </router-link>

            <router-link to="/alumno/inscripcion" class="nav-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
              <span>Pre-inscripción</span>
            </router-link>
          </nav>
        </div>

        <!-- Usuario y Acciones -->
        <div class="navbar-right">
          <div class="student-user-pill">
            <div class="user-avatar-sm">
              {{ iniciales }}
            </div>
            <div class="user-info-text">
              <span class="user-fullname">{{ authStore.nombreCompleto }}</span>
              <span class="user-matricula font-mono">{{ authStore.matriculaOId }}</span>
            </div>
          </div>

          <button
            type="button"
            class="btn btn-secondary btn-sm logout-nav-btn"
            @click="cerrarSesion"
          >
            Salir
          </button>

          <!-- Toggle Móvil -->
          <button
            type="button"
            class="mobile-menu-btn"
            @click="menuMovilAbierto = !menuMovilAbierto"
            aria-label="Menú"
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
          </button>
        </div>
      </div>

      <!-- Menú Desplegable Móvil -->
      <div v-if="menuMovilAbierto" class="mobile-nav-drawer">
        <router-link
          to="/alumno/horario"
          class="mobile-nav-item"
          @click="menuMovilAbierto = false"
        >
          Mi Horario
        </router-link>
        <router-link
          to="/alumno/perfil"
          class="mobile-nav-item"
          @click="menuMovilAbierto = false"
        >
          Perfil Académico
        </router-link>
        <router-link
          to="/alumno/inscripcion"
          class="mobile-nav-item"
          @click="menuMovilAbierto = false"
        >
          Pre-inscripción
        </router-link>
        <button
          type="button"
          class="btn btn-danger btn-sm mobile-logout-btn"
          @click="cerrarSesion"
        >
          Cerrar sesión
        </button>
      </div>
    </header>

    <!-- Contenido Alumno -->
    <main class="alumno-main-content">
      <div class="content-container">
        <router-view />
      </div>
    </main>

    <!-- Footer Discreto -->
    <footer class="alumno-footer">
      <div class="footer-container">
        <span>InscripcionMadeEasy · {{ authStore.nombreEscuela }}</span>
        <span class="text-xs text-muted">Portal seguro para alumnos</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { useNotificationStore } from '../stores/notification';

const authStore = useAuthStore();
const notifStore = useNotificationStore();
const router = useRouter();

const menuMovilAbierto = ref(false);

const iniciales = computed(() => {
  const al = authStore.alumno;
  if (!al) return 'AL';
  const n = al.nombre ? al.nombre[0] : '';
  const p = al.apellido_paterno ? al.apellido_paterno[0] : '';
  return (n + p).toUpperCase() || 'AL';
});

function cerrarSesion() {
  authStore.logout();
  notifStore.info('Sesión cerrada correctamente');
  router.push('/login');
}

onMounted(() => {
  // Asegurar que el perfil del alumno esté cargado
  if (!authStore.alumno && authStore.esAlumno) {
    authStore.recargarPerfilAlumno();
  }
});
</script>

<style scoped>
.alumno-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-main);
}

.alumno-navbar {
  background-color: #ffffff;
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: var(--shadow-xs);
}

.navbar-container {
  max-width: 1300px;
  margin: 0 auto;
  padding: 0 1.5rem;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.navbar-left {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.brand-link {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  text-decoration: none;
}

.brand-icon {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--primary) 0%, var(--violet) 100%);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-text-wrap {
  display: flex;
  flex-direction: column;
}

.brand-title {
  font-size: 0.95rem;
  font-weight: 800;
  color: var(--text-main);
  line-height: 1.15;
}

.brand-sub {
  font-size: 0.7rem;
  color: var(--primary);
  font-weight: 600;
}

.desktop-nav {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.45rem 0.85rem;
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-muted);
  text-decoration: none;
  transition: all 0.15s ease;
}

.nav-item:hover {
  color: var(--primary);
  background-color: var(--primary-light);
}

.nav-item.router-link-active {
  color: var(--primary-dark);
  background-color: var(--primary-light);
  border: 1px solid var(--primary-border);
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.student-user-pill {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  padding: 0.3rem 0.75rem 0.3rem 0.4rem;
  border-radius: var(--radius-full);
}

.user-avatar-sm {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary) 0%, var(--violet) 100%);
  color: #ffffff;
  font-size: 0.75rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-info-text {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}

.user-fullname {
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--text-main);
  max-width: 160px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-matricula {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.mobile-menu-btn {
  display: none;
  background: none;
  border: none;
  color: var(--text-main);
  cursor: pointer;
  padding: 0.25rem;
}

.mobile-nav-drawer {
  display: none;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem 1.5rem;
  background-color: #ffffff;
  border-bottom: 1px solid var(--border);
}

.mobile-nav-item {
  padding: 0.5rem 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-main);
  text-decoration: none;
}

.mobile-logout-btn {
  margin-top: 0.5rem;
  align-self: flex-start;
}

.alumno-main-content {
  flex: 1;
  padding: 1.75rem 1.5rem;
}

.content-container {
  max-width: 1300px;
  margin: 0 auto;
}

.alumno-footer {
  background: #ffffff;
  border-top: 1px solid var(--border);
  padding: 1rem 1.5rem;
}

.footer-container {
  max-width: 1300px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.font-mono {
  font-family: 'JetBrains Mono', monospace;
}

.text-xs {
  font-size: 0.75rem;
}

.text-muted {
  color: var(--text-muted);
}

@media (max-width: 850px) {
  .desktop-nav {
    display: none;
  }
  .logout-nav-btn {
    display: none;
  }
  .mobile-menu-btn {
    display: block;
  }
  .mobile-nav-drawer {
    display: flex;
  }
}
</style>
