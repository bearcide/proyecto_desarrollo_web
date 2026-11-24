<template>
  <div class="admin-shell">
    <!-- Barra lateral (estilo barra lateral de macOS: sigue el tema) -->
    <aside class="admin-sidebar" :class="{ 'sidebar-open': sidebarAbierto }">
      <div class="sidebar-top">
        <div class="sidebar-brand">
          <div class="brand-symbol" aria-hidden="true">
            <AppIcon name="logo" :size="18" :stroke-width="2.5" />
          </div>
          <div class="brand-titles">
            <span class="brand-name">InscripcionMadeEasy</span>
            <span class="brand-env">Administración escolar</span>
          </div>
        </div>

        <div class="school-info-card">
          <div class="school-info-label">Escuela activa</div>
          <div class="school-info-name">{{ authStore.nombreEscuela }}</div>
          <span class="badge badge-success school-badge">
            ● {{ estadoEscuela }}
          </span>
        </div>
      </div>

      <nav class="sidebar-nav" aria-label="Navegación de administración">
        <router-link to="/admin/dashboard" class="nav-item" @click="sidebarAbierto = false">
          <AppIcon name="dashboard" class="nav-icon" :size="18" />
          <span>Dashboard</span>
        </router-link>

        <router-link to="/admin/asignaciones" class="nav-item" @click="sidebarAbierto = false">
          <AppIcon name="zap" class="nav-icon" :size="18" />
          <span>Generar horarios</span>
        </router-link>

        <router-link to="/admin/importar" class="nav-item" @click="sidebarAbierto = false">
          <AppIcon name="upload" class="nav-icon" :size="18" />
          <span>Importación CSV</span>
        </router-link>

        <router-link to="/admin/alumnos" class="nav-item" @click="sidebarAbierto = false">
          <AppIcon name="users" class="nav-icon" :size="18" />
          <span>Alumnos</span>
        </router-link>

        <router-link to="/admin/grupos" class="nav-item" @click="sidebarAbierto = false">
          <AppIcon name="calendar" class="nav-icon" :size="18" />
          <span>Grupos y cupos</span>
        </router-link>

        <router-link to="/admin/planes" class="nav-item" @click="sidebarAbierto = false">
          <AppIcon name="book-open" class="nav-icon" :size="18" />
          <span>Planes de estudio</span>
        </router-link>

        <div class="sidebar-section-label">Contratación y licencias</div>

        <router-link to="/admin/comercial/planes" class="nav-item" @click="sidebarAbierto = false">
          <AppIcon name="award" class="nav-icon" :size="18" />
          <span>Planes comerciales</span>
        </router-link>

        <router-link to="/admin/comercial/configurador" class="nav-item" @click="sidebarAbierto = false">
          <AppIcon name="sliders" class="nav-icon" :size="18" />
          <span>Configurar plan</span>
        </router-link>

        <router-link to="/admin/comercial/suscripcion" class="nav-item" @click="sidebarAbierto = false">
          <AppIcon name="credit-card" class="nav-icon" :size="18" />
          <span>Mi suscripción</span>
        </router-link>

        <router-link to="/admin/comercial/licencias" class="nav-item" @click="sidebarAbierto = false">
          <AppIcon name="shield" class="nav-icon" :size="18" />
          <span>Licencias</span>
        </router-link>

        <template v-if="esPropietario">
          <div class="sidebar-section-label">Plataforma SaaS</div>
          <router-link
            to="/comercial/propietario/dashboard"
            class="nav-item nav-item-propietario"
            @click="sidebarAbierto = false"
          >
            <AppIcon name="zap" class="nav-icon" :size="18" />
            <span>Panel propietario</span>
          </router-link>
        </template>
      </nav>

      <!-- Cuenta y único botón para cerrar sesión (L2) -->
      <div class="sidebar-footer">
        <div class="user-profile-badge">
          <div class="user-avatar" aria-hidden="true">{{ inicialesAdmin }}</div>
          <div class="user-details">
            <span class="user-name">{{ authStore.matriculaOId || 'Admin' }}</span>
            <span class="user-role">Administrador</span>
          </div>
        </div>
        <button type="button" class="btn btn-secondary btn-sm logout-btn" @click="cerrarSesion">
          <AppIcon name="log-out" :size="15" />
          <span>Salir</span>
        </button>
      </div>
    </aside>

    <!-- Fondo para cerrar la barra lateral en pantallas angostas -->
    <div v-if="sidebarAbierto" class="sidebar-backdrop" @click="sidebarAbierto = false"></div>

    <div class="admin-main-wrapper">
      <!-- Barra superior mínima (L3): solo menú en pantallas angostas y acciones globales -->
      <header class="admin-topbar">
        <button
          type="button"
          class="mobile-toggle-btn"
          aria-label="Abrir menú"
          @click="sidebarAbierto = !sidebarAbierto"
        >
          <AppIcon name="menu" :size="22" />
        </button>

        <div class="topbar-actions">
          <router-link
            v-if="esPropietario"
            to="/comercial/propietario/dashboard"
            class="btn btn-secondary btn-sm"
            title="Abrir la consola del propietario SaaS"
          >
            <AppIcon name="zap" :size="14" />
            <span>Panel propietario</span>
          </router-link>
          <ThemeToggle />
        </div>
      </header>

      <main class="admin-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { useNotificationStore } from '../stores/notification';
import { usePermisosComerciales } from '../modules/comercial/propietario/composables/usePermisosComerciales';
import ThemeToggle from '../components/ThemeToggle.vue';
import AppIcon from '../components/AppIcon.vue';

const authStore = useAuthStore();
const notifStore = useNotificationStore();
const router = useRouter();
const { esPropietario } = usePermisosComerciales();

const sidebarAbierto = ref(false);

const inicialesAdmin = computed(() => {
  const identificador = String(authStore.matriculaOId ?? '').trim();
  if (!identificador) return 'AD';

  const [primeraParte, segundaParte] = identificador.split(/\s+/);
  return (segundaParte
    ? primeraParte[0] + segundaParte[0]
    : primeraParte.slice(0, 2)
  ).toUpperCase();
});

// "ACTIVO" → "Activo" (L4: mayúscula solo al inicio)
const estadoEscuela = computed(() => {
  const estado = String(authStore.membresia?.estado_escuela || 'ACTIVO').toLowerCase();
  return estado.charAt(0).toUpperCase() + estado.slice(1);
});

function cerrarSesion() {
  authStore.logout();
  notifStore.info('Sesión cerrada correctamente');
  router.push('/login');
}
</script>

<style scoped>
.admin-shell {
  /* Material de la barra lateral (claro) */
  --sidebar-bg: rgba(242, 242, 247, 0.82);
  --sidebar-border: var(--border);
  --sidebar-card: rgba(255, 255, 255, 0.7);

  display: flex;
  min-height: 100vh;
  background-color: var(--bg-main);
}

:root[data-theme="dark"] .admin-shell {
  --sidebar-bg: rgba(28, 28, 30, 0.82);
  --sidebar-card: rgba(255, 255, 255, 0.05);
}

/* ---------- Barra lateral ---------- */
.admin-sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  width: 264px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background-color: var(--sidebar-bg);
  -webkit-backdrop-filter: blur(30px) saturate(180%);
  backdrop-filter: blur(30px) saturate(180%);
  border-right: 1px solid var(--sidebar-border);
  color: var(--text-main);
  transition: transform 0.25s ease;
  z-index: 100;
}

@media (prefers-reduced-transparency: reduce), (prefers-contrast: more) {
  .admin-sidebar {
    background-color: var(--bg-card);
    -webkit-backdrop-filter: none;
    backdrop-filter: none;
  }
}

.sidebar-top {
  padding: 1.25rem 1rem 0.75rem;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  margin-bottom: 1rem;
  padding: 0 0.25rem;
}

.brand-symbol {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  background-color: var(--accent);
  color: var(--on-accent);
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-titles {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.brand-name {
  font-size: 0.9375rem;
  font-weight: 800;
  letter-spacing: -0.01em;
  color: var(--text-main);
}

.brand-env {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-muted);
}

.school-info-card {
  background-color: var(--sidebar-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 0.7rem 0.85rem;
}

.school-info-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-muted);
}

.school-info-name {
  margin: 0.1rem 0 0.4rem;
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.school-badge {
  font-size: 0.75rem;
  padding: 0.1rem 0.5rem;
  text-transform: none;
  letter-spacing: 0;
}

/* Navegación */
.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0.5rem 0.75rem 1rem;
  overflow-y: auto;
}

.sidebar-section-label {
  margin: 1rem 0 0.3rem;
  padding: 0 0.75rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-light);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  min-height: 36px;
  padding: 0.45rem 0.75rem;
  border-radius: 8px;
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--text-main);
  text-decoration: none;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.nav-icon {
  flex-shrink: 0;
  color: var(--accent-text);
}

.nav-item:hover {
  color: var(--text-main);
  background-color: var(--fill-track);
}

/* Selección: fondo tintado del acento, como en macOS */
.nav-item.router-link-active {
  background-color: var(--primary-light);
  color: var(--accent-text);
  font-weight: 600;
}

.nav-item-propietario .nav-icon {
  color: var(--warning);
}

/* Pie: cuenta y salir */
.sidebar-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.85rem 1rem;
  border-top: 1px solid var(--border-subtle);
}

.user-profile-badge {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  min-width: 0;
}

.user-avatar {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  border-radius: 50%;
  background-color: var(--accent);
  color: var(--on-accent);
  font-size: 0.75rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-details {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.user-name {
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.logout-btn {
  flex-shrink: 0;
}

/* ---------- Área principal ---------- */
.admin-main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.admin-topbar {
  position: sticky;
  top: 0;
  z-index: 50;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  background-color: var(--bar-bg);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  backdrop-filter: blur(20px) saturate(180%);
  border-bottom: 1px solid var(--border);
}

.mobile-toggle-btn {
  display: none;
  background: none;
  border: none;
  color: var(--text-main);
  cursor: pointer;
  padding: 0.25rem;
}

.topbar-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.admin-content {
  flex: 1;
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: 1.75rem 1.5rem 2.5rem;
}

@media (max-width: 991px) {
  .admin-sidebar {
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
    transform: translateX(-100%);
    background-color: var(--bg-card);
  }

  .admin-sidebar.sidebar-open {
    transform: translateX(0);
  }

  .sidebar-backdrop {
    position: fixed;
    inset: 0;
    z-index: 90;
    background-color: rgba(0, 0, 0, 0.4);
  }

  .mobile-toggle-btn {
    display: block;
  }
}
</style>

<style>
/* T3 / T4 · En las vistas académicas del administrador no se fuerzan MAYÚSCULAS */
.admin-view .badge,
.admin-view .stat-label,
.admin-view .data-table th {
  text-transform: none;
  letter-spacing: 0;
}

.admin-view .badge {
  font-size: 0.8125rem;
}

.admin-view .data-table th {
  font-size: 0.8125rem;
}
</style>
