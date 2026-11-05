<template>
  <div class="admin-shell">
    <!-- Sidebar Navegación Admin -->
    <aside class="admin-sidebar" :class="{ 'sidebar-open': sidebarAbierto }">
      <div class="sidebar-top">
        <div class="sidebar-brand">
          <div class="brand-symbol">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/><path d="M6 6h10"/><path d="M6 10h10"/></svg>
          </div>
          <div class="brand-titles">
            <span class="brand-name">InscripcionMadeEasy</span>
            <span class="brand-env">Admin SaaS</span>
          </div>
        </div>

        <div class="school-info-card">
          <div class="school-info-label">Escuela Activa</div>
          <div class="school-info-name">{{ authStore.nombreEscuela }}</div>
          <span class="badge badge-success school-badge">
            ● {{ authStore.membresia?.estado_escuela || 'ACTIVO' }}
          </span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <router-link
          to="/admin/dashboard"
          class="nav-item"
          @click="sidebarAbierto = false"
        >
          <svg class="nav-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/></svg>
          <span>Dashboard</span>
        </router-link>

        <router-link
          to="/admin/asignaciones"
          class="nav-item"
          @click="sidebarAbierto = false"
        >
          <svg class="nav-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          <span>Generar Horarios</span>
        </router-link>

        <router-link
          to="/admin/importar"
          class="nav-item"
          @click="sidebarAbierto = false"
        >
          <svg class="nav-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          <span>Importación CSV</span>
        </router-link>

        <router-link
          to="/admin/alumnos"
          class="nav-item"
          @click="sidebarAbierto = false"
        >
          <svg class="nav-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          <span>Alumnos</span>
        </router-link>

        <router-link
          to="/admin/grupos"
          class="nav-item"
          @click="sidebarAbierto = false"
        >
          <svg class="nav-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          <span>Grupos y Cupos</span>
        </router-link>

        <router-link
          to="/admin/planes"
          class="nav-item"
          @click="sidebarAbierto = false"
        >
          <svg class="nav-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
          <span>Planes de Estudio</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="user-profile-badge">
          <div class="user-avatar">AD</div>
          <div class="user-details">
            <span class="user-name">{{ authStore.matriculaOId || 'Admin' }}</span>
            <span class="user-role">Administrador</span>
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
    <div class="admin-main-wrapper">
      <header class="admin-topbar">
        <button
          type="button"
          class="mobile-toggle-btn"
          @click="sidebarAbierto = !sidebarAbierto"
          aria-label="Abrir menú"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
        </button>

        <div class="topbar-context">
          <span class="context-badge">Modo Gestión Institucional</span>
        </div>

        <div class="topbar-actions">
          <span class="tenant-uuid-pill" :title="authStore.tenantId">
            Tenant: {{ authStore.tenantId ? authStore.tenantId.substring(0, 8) + '…' : 'N/A' }}
          </span>
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

      <main class="admin-content">
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
.admin-shell {
  display: flex;
  min-height: 100vh;
  background-color: var(--bg-main);
}

/* Sidebar */
.admin-sidebar {
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
  background: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
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
  color: #c7d2fe;
  text-transform: uppercase;
}

.school-info-card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-sm);
  padding: 0.65rem 0.85rem;
}

.school-info-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.school-info-name {
  font-size: 0.85rem;
  font-weight: 700;
  color: #ffffff;
  margin: 0.15rem 0 0.35rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.school-badge {
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
  background: rgba(79, 70, 229, 0.25);
  color: #ffffff;
  border-left: 3px solid #818cf8;
}

.nav-icon {
  flex-shrink: 0;
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
  background: var(--accent);
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
  color: #94a3b8;
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
.admin-main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.admin-topbar {
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
  color: var(--text-muted);
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.tenant-uuid-pill {
  font-size: 0.75rem;
  font-family: 'JetBrains Mono', monospace;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  padding: 0.25rem 0.6rem;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
}

.admin-content {
  flex: 1;
  padding: 1.5rem;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
}

/* Responsivo */
@media (max-width: 991px) {
  .admin-sidebar {
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
    transform: translateX(-100%);
  }

  .admin-sidebar.sidebar-open {
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
