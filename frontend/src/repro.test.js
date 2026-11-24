import { describe, it, expect, beforeEach } from 'vitest';
import { createApp } from 'vue';
import { createPinia, setActivePinia } from 'pinia';
import router from './router';
import App from './App.vue';

describe('Efecto cascada tras fallo en /admin/importar', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
    localStorage.setItem('ime_token', 'token_demo');
    localStorage.setItem('ime_refresh', 'refresh_demo');
    localStorage.setItem('ime_tenant_id', 'tenant-1234');
    localStorage.setItem('ime_membresia', JSON.stringify({
      tenant: 'tenant-1234',
      es_administrador: true,
      es_alumno: false,
      nombre_escuela: 'Escuela Demo',
      activo: true,
      estado_escuela: 'ACTIVO',
    }));
    localStorage.setItem('ime_usuario', 'demo_admin');
  });

  it('Al visitar importar y luego navegar a alumnos/grupos/planes, todo queda en blanco', async () => {
    const app = createApp(App);
    const pinia = createPinia();
    app.use(pinia);
    app.use(router);

    const root = document.createElement('div');
    document.body.appendChild(root);
    app.mount(root);

    // 1. Iniciar en dashboard
    await router.push('/admin/dashboard');
    await router.isReady();
    expect(root.querySelector('.admin-dashboard')).not.toBeNull();
    console.log('1. Dashboard visible:', root.querySelector('.admin-dashboard') !== null);

    // 2. Navegar a importar (lanza TypeError _ctx.Blob is not a constructor)
    try {
      await router.push('/admin/importar');
    } catch (e) {
      console.log('Error al navegar a importar:', e);
    }
    console.log('2. Importar visible:', root.querySelector('.importar-page') !== null);
    console.log('2. Contenido de admin-content tras entrar a importar:', root.querySelector('.admin-content')?.innerHTML);

    // 3. Usuario hace clic en Alumnos en el sidebar
    try {
      await router.push('/admin/alumnos');
    } catch (e) {
      console.log('Error al navegar a alumnos tras importar:', e);
    }
    console.log('3. Alumnos visible tras importar:', root.querySelector('.alumnos-page') !== null);
    console.log('3. Contenido de admin-content tras intentar ir a alumnos:', root.querySelector('.admin-content')?.innerHTML);

    // 4. Usuario hace clic en Grupos en el sidebar
    try {
      await router.push('/admin/grupos');
    } catch (e) {
      console.log('Error al navegar a grupos tras importar:', e);
    }
    console.log('4. Grupos visible tras importar:', root.querySelector('.grupos-page') !== null);
    console.log('4. Contenido de admin-content tras intentar ir a grupos:', root.querySelector('.admin-content')?.innerHTML);

    // 5. Usuario hace clic en Planes en el sidebar
    try {
      await router.push('/admin/planes');
    } catch (e) {
      console.log('Error al navegar a planes tras importar:', e);
    }
    console.log('5. Planes visible tras importar:', root.querySelector('.planes-page') !== null);
    console.log('5. Contenido de admin-content tras intentar ir a planes:', root.querySelector('.admin-content')?.innerHTML);

    app.unmount();
    document.body.removeChild(root);
  });
});
