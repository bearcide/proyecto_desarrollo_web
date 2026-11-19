<template>
  <div class="propietario-shell">
    <!-- Sidebar Navegación Propietario SaaS -->
    <aside class="propietario-sidebar" :class="{ 'sidebar-open': sidebarAbierto }">
      <div class="sidebar-top">
        <div class="sidebar-brand">
          <div class="brand-symbol">
            <AppIcon name="zap" size="20" />
          </div>
          <div class="brand-titles">
            <span class="brand-name">InscripcionMadeEasy</span>
            <span class="brand-env">Propietario SaaS</span>
          </div>
        </div>

        <div class="platform-info-card">
          <div class="platform-info-label">Consola de Control</div>
          <div class="platform-info-name">Superusuario Plataforma</div>
          <span class="badge badge-warning platform-badge">
            ● ACCESO GLOBAL B2B
          </span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <div class="sidebar-section-label">Comercialización SaaS</div>

        <router-link
          to="/comercial/propietario/dashboard"
          class="nav-item"
          @click="sidebarAbierto = false"
        >
          <AppIcon name="grid" class="nav-icon" size="18" />
          <span>Dashboard Comercial</span>
        </router-link>

        <router-link
          to="/comercial/propietario/clientes"
          class="nav-item"
          @click="sidebarAbierto = false"
        >
          <AppIcon name="building" class="nav-icon" size="18" />
          <span>Clientes & Escuelas</span>
        </router-link>

        <router-link
          to="/comercial/propietario/planes"
          class="nav-item"
          @click="sidebarAbierto = false"
        >
          <AppIcon name="award" class="nav-icon" size="18" />
          <span>Catálogo de Planes</span>
        </router-link>

        <router-link
          to="/comercial/propietario/suscripciones"
          class="nav-item"
          @click="sidebarAbierto = false"
        >
          <AppIcon name="credit-card" class="nav-icon" size="18" />
          <span>Suscripciones SaaS</span>
        </router-link>

        <router-link
          to="/comercial/propietario/licencias"
          class="nav-item"
          @click="sidebarAbierto = false"
        >
          <AppIcon name="shield" class="nav-icon" size="18" />
          <span>Licencias Emitidas</span>
        </router-link>

        <router-link
          to="/comercial/propietario/facturacion"
          class="nav-item"
          @click="sidebarAbierto = false"
        >
          <AppIcon name="file-text" class="nav-icon" size="18" />
          <span>Facturación & Pagos</span>
        </router-link>

        <div class="sidebar-section-divider"></div>
        <div class="sidebar-section-label">Gestión Institucional</div>

        <router-link
          to="/admin/dashboard"
          class="nav-item"
          @click="sidebarAbierto = false"
        >
          <AppIcon name="external-link" class="nav-icon" size="18" />
          <span>Panel Escolar</span>
        </router-link>

        <router-link
          to="/admin/comercial/planes"
          class="nav-item"
          @click="sidebarAbierto = false"
        >
          <AppIcon name="sliders" class="nav-icon" size="18" />
          <span>Vista Comercial Cliente</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="user-profile-badge">
          <div class="user-avatar">SU</div>
          <div class="user-details">
            <span class="user-name">{{ authStore.matriculaOId || 'Propietario' }}</span>
            <span class="user-role">Superusuario SaaS</span>
          </div>
        </div>
        <button
          type="button"
          class="btn btn-outline btn-sm logout-btn"
          @click="cerrarSesion"
          title="Cerrar sesión"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          <span>Salir</span>
        </button>
      </div>
    </aside>

    <!-- Overlay móvil para cerrar sidebar -->
    <div
      v-if="sidebarAbierto"
      class="sidebar-backdrop"
      @click="sidebarAbierto = false"
    ></div>

    <!-- Contenido Principal -->
    <div class="propietario-main-wrapper">
      <header class="propietario-topbar">
        <button
          type="button"
          class="mobile-toggle-btn"
          @click="sidebarAbierto = !sidebarAbierto"
          aria-label="Abrir menú"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
        </button>

        <div class="topbar-context">
          <span class="context-badge">Consola del Propietario SaaS — Multi-Tenant</span>
        </div>

        <div class="topbar-actions">
          <router-link
            to="/admin/dashboard"
            class="btn btn-secondary btn-sm"
            title="Ir al panel administrativo de escuela"
          >
            <AppIcon name="external-link" size="14" />
            <span>Gestión Escolar</span>
          </router-link>
          <button
            type="button"
            class="btn btn-secondary btn-sm"
            @click="cerrarSesion"
          >
            Cerrar sesión
          </button>
          <ThemeToggle />
        </div>
      </header>

      <main class="propietario-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { useNotificationStore } from '../stores/notification';
import ThemeToggle from '../components/ThemeToggle.vue';
import AppIcon from '../components/AppIcon.vue';

const authStore = useAuthStore();
const notifStore = useNotificationStore();
const router = useRouter();

const sidebarAbierto = ref(false);

function cerrarSesion() {
  authStore.logout();
  notifStore.info('Sesión cerrada correctamente');
  router.push('/login');
}
</script>

<style scoped>
.propietario-shell {
  display: flex;
  min-height: 100vh;
  background-color: var(--bg-main);
}

/* Sidebar */
.propietario-sidebar {
  width: 260px;
  background-color: var(--bg-sidebar);
  color: #ffffff;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: transform 0.25s ease;
  z-index: 100;
}

.sidebar-top {
  padding: 1.5rem 1.25rem 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.brand-symbol {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--violet) 0%, var(--primary) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(124, 58, 237, 0.35);
}

.brand-titles {
  display: flex;
  flex-direction: column;
}

.brand-name {
  font-size: 0.95rem;
  font-weight: 800;
  letter-spacing: -0.01em;
  color: #ffffff;
}

.brand-env {
  font-size: 0.7rem;
  font-weight: 600;
  color: #ddd6fe;
  text-transform: uppercase;
}

.platform-info-card {
  background: rgba(124, 58, 237, 0.08);
  border: 1px solid rgba(124, 58, 237, 0.25);
  border-radius: var(--radius-sm);
  padding: 0.65rem 0.85rem;
}

.platform-info-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  color: #c4b5fd;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.platform-info-name {
  font-size: 0.85rem;
  font-weight: 700;
  color: #ffffff;
  margin: 0.15rem 0 0.35rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.platform-badge {
  font-size: 0.65rem;
  padding: 0.1rem 0.45rem;
}

/* Sidebar Nav */
.sidebar-nav {
  padding: 1rem 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  flex: 1;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.65rem 0.85rem;
  color: #94a3b8;
  font-size: 0.875rem;
  font-weight: 600;
  border-radius: var(--radius-sm);
  transition: all 0.15s ease;
  text-decoration: none;
}

.nav-item:hover {
  color: #ffffff;
  background-color: var(--bg-sidebar-hover);
}

.nav-item.router-link-active {
  background: rgba(124, 58, 237, 0.25);
  color: #ffffff;
  border-left: 3px solid #a78bfa;
}

.nav-icon {
  flex-shrink: 0;
}

.sidebar-section-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.08);
  margin: 0.75rem 0.5rem 0.35rem;
}

.sidebar-section-label {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #64748b;
  font-weight: 700;
  padding: 0.2rem 0.85rem;
}

/* Sidebar Footer */
.sidebar-footer {
  padding: 1rem 1.25rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.user-profile-badge {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  min-width: 0;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--violet) 0%, var(--primary) 100%);
  color: #ffffff;
  font-size: 0.75rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-details {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.user-name {
  font-size: 0.8125rem;
  font-weight: 700;
  color: #ffffff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: 0.7rem;
  color: #c4b5fd;
}

.logout-btn {
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.2);
  padding: 0.35rem 0.6rem;
}

.logout-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.4);
}

/* Main Area */
.propietario-main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.propietario-topbar {
  height: 64px;
  background-color: var(--bar-bg);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  backdrop-filter: blur(20px) saturate(180%);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  position: sticky;
  top: 0;
  z-index: 50;
}

.mobile-toggle-btn {
  display: none;
  background: none;
  border: none;
  color: var(--text-main);
  cursor: pointer;
  padding: 0.25rem;
}

.context-badge {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--violet);
  background: var(--violet-light);
  border: 1px solid var(--violet-border);
  padding: 0.25rem 0.75rem;
  border-radius: var(--radius-sm);
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.propietario-content {
  flex: 1;
  padding: 1.5rem;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
}

/* Responsivo */
@media (max-width: 991px) {
  .propietario-sidebar {
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
    transform: translateX(-100%);
  }

  .propietario-sidebar.sidebar-open {
    transform: translateX(0);
  }

  .sidebar-backdrop {
    position: fixed;
    inset: 0;
    background-color: rgba(15, 23, 42, 0.5);
    z-index: 90;
  }

  .mobile-toggle-btn {
    display: block;
  }
}
</style>
