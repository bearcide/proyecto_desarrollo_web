import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import { useNotificationStore } from './stores/notification'
import './infrastructure/static/css/main.css'

const app = createApp(App)

const pinia = createPinia()
app.use(pinia)
app.use(router)

if (typeof window !== 'undefined') {
  window.addEventListener('ime:sesion-expirada', () => {
    const authStore = useAuthStore();
    const notifStore = useNotificationStore();
    authStore.logout();
    notifStore.warning('Tu sesión ha expirado. Por favor ingresa nuevamente.');
    if (router.currentRoute.value.path !== '/login') {
      router.push('/login');
    }
  });

  window.addEventListener('ime:token-renovado', (e) => {
    const authStore = useAuthStore();
    if (e.detail) {
      authStore.token = e.detail;
    }
  });
}

app.mount('#app')