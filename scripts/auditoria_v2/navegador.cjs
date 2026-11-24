const { chromium } = require(process.env.IME_PLAYWRIGHT || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const evidence = path.resolve(process.argv[2]);
const artifacts = path.resolve(process.argv[3]);
fs.mkdirSync(artifacts, { recursive: false });
const summary = JSON.parse(fs.readFileSync(path.join(evidence, 'resultados.json')));
const web = process.env.IME_WEB_URL || 'http://127.0.0.1:15174';
const api = process.env.IME_API_URL || 'http://127.0.0.1:18084/api/v1';
const password = process.env.IME_AUDIT_PASSWORD;
if (!password || password.length < 8) throw new Error('Define IME_AUDIT_PASSWORD para esta ejecución de prueba.');
const results = { pruebas: [], erroresJS: [], erroresConsola: [], advertencias: [], respuestas: [], fallosRed: [], fallos: [] };
const ownerRoot = '/comercial/propietario';

async function main() {
  const browser = await chromium.launch();
  let phase = 'inicio';
  try {
    async function stage(name, fn) {
      phase = name;
      const start = performance.now();
      try {
        await fn();
        const seconds = +((performance.now() - start) / 1000).toFixed(4);
        results.pruebas.push({ nombre: name, segundos: seconds });
        console.log('OK', name, seconds + 's');
      } catch (error) {
        results.fallos.push({ nombre: name, mensaje: error.message });
        console.error('FALLO', name, error.message);
      }
    }

    async function page() {
      const p = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
      p.setDefaultTimeout(12000);
      p.on('pageerror', err => results.erroresJS.push({ fase: phase, mensaje: err.message }));
      p.on('console', msg => {
        if (!['warning', 'error'].includes(msg.type())) return;
        const list = msg.type() === 'error' ? results.erroresConsola : results.advertencias;
        list.push({ fase: phase, mensaje: msg.text() });
      });
      p.on('response', response => {
        if (response.url().includes('/api/v1/')) {
          results.respuestas.push({ fase: phase, metodo: response.request().method(),
            ruta: new URL(response.url()).pathname, status: response.status() });
        }
      });
      p.on('requestfailed', req => results.fallosRed.push({ fase: phase,
        ruta: new URL(req.url()).pathname, error: req.failure()?.errorText }));
      // Vite usa la ruta relativa. Chromium contacta el backend exclusivo de auditoría por este puente.
      await p.route('**/api/v1/**', async route => {
        const request = route.request();
        const target = api + request.url().split('/api/v1')[1];
        await route.fulfill({ response: await route.fetch({ url: target }) });
      });
      return p;
    }
    async function login(p, user, target) {
      await p.goto(web + '/login');
      await p.locator('#matricula').fill(user);
      await p.locator('#password').fill(password);
      const result = await response(p, '/token/', 'POST',
        () => p.getByRole('button', { name: 'Iniciar sesión' }).click());
      assert.equal(result.status(), 200);
      await p.waitForURL(url => url.pathname === target);
    }
    async function response(p, endpoint, method, action) {
      const [r] = await Promise.all([p.waitForResponse(r =>
        new URL(r.url()).pathname === '/api/v1' + endpoint && r.request().method() === method), action()]);
      return r;
    }
    async function navigate(p, route, selector, endpoint, status = 200) {
      const action = () => p.goto(web + route, { waitUntil: 'domcontentloaded' });
      if (endpoint) assert.equal((await response(p, endpoint, 'GET', action)).status(), status);
      else await action();
      assert.equal(new URL(p.url()).pathname, route);
      await p.locator(selector).first().waitFor();
    }
    const shot = (p, name) => p.screenshot({ path: path.join(artifacts, name + '.png'), animations: 'disabled' });
    const [admin, student, owner] = await Promise.all([page(), page(), page()]);
    await stage('login de administrador, alumno y propietario', async () => {
      await login(admin, summary.usuarios.A.admin, '/admin/dashboard');
      await login(student, summary.usuarios.A.alumno, '/alumno/horario');
      await login(owner, summary.usuarios.propietario, ownerRoot + '/dashboard');
    });

    for (const [name, route, selector, endpoint] of [
      ['dashboard institucional', '/admin/dashboard', '.admin-dashboard', '/demo/estadisticas/'],
      ['catálogo curricular', '/admin/planes', '.planes-page', '/planes-estudios/'],
      ['grupos y cupos', '/admin/grupos', '.grupos-page', '/demo/grupos/'],
      ['alumnos', '/admin/alumnos', '.alumnos-page', '/alumnos/'],
      ['planes comerciales', '/admin/comercial/planes', '.comercial-planes-page', '/comercial/planes/'],
      ['suscripción institucional', '/admin/comercial/suscripcion', '.suscripcion-page', '/comercial/suscripciones/'],
      ['licencias institucionales', '/admin/comercial/licencias', '.licencias-page', '/comercial/licencias/'],
    ]) {
      await stage(name, async () => {
        await navigate(admin, route, selector, endpoint);
        if (name === 'alumnos') await admin.getByText('Estudiantes Registrados (200)').waitFor();
        if (name === 'licencias institucionales') {
          await admin.getByText(summary.escuelas.A.licencia).waitFor();
          const leyenda = await admin.locator('.features-sublist').first().innerText();
          results.presentacion_licencia = leyenda.split('\n');
          if (!process.env.IME_SOLO_OBSERVAR) {
            assert.deepEqual(results.presentacion_licencia.sort(),
              ['alumnos', 'asignaciones', 'horarios', 'importaciones', 'planes estudios', 'reportes'].sort());
          }
          await shot(admin, 'licencia-A');
        }
      });
    }

    await stage('formulario CSV valida, reimporta y presenta filas del archivo', async () => {
      await navigate(admin, '/admin/importar', '.importar-page');
      const items = {
        planes: 'Planes de Estudio', materias: 'Materias', alumnos: 'Alumnos',
        grupos: 'Grupos y Horarios', solicitudes: 'Solicitudes',
      };
      for (const [archivo, tab] of Object.entries(items)) {
        await admin.locator('.tab-btn').filter({ hasText: tab }).click();
        await admin.locator('input[type=file]').setInputFiles(path.join(evidence, 'escuela_A', archivo + '.csv'));
        await admin.locator('.tab-btn.active .tab-badge-filled').waitFor();
      }
      let r = await response(admin, '/demo/importaciones/validar/', 'POST',
        () => admin.getByRole('button', { name: /Validar CSVs/ }).click());
      assert.equal(r.status(), 200);
      r = await response(admin, '/demo/importaciones/confirmar/', 'POST',
        () => admin.getByRole('button', { name: /Confirmar e Importar/ }).click());
      assert.equal(r.status(), 200);
      await admin.getByText(/Importación completada con éxito/).waitFor();
      assert.equal((await r.json()).filas.alumnos, 200);
      await shot(admin, 'importacion-A');
      await admin.locator('.tab-btn').filter({ hasText: 'Planes de Estudio' }).click();
      await admin.locator('input[type=file]').setInputFiles({
        name: 'plan-invalido.csv', mimeType: 'text/csv', buffer: Buffer.from('id,formato\n1,invalido\n'),
      });
      const bad = await response(admin, '/demo/importaciones/confirmar/', 'POST',
        () => admin.getByRole('button', { name: /Confirmar e Importar/ }).click());
      assert.equal(bad.status(), 400);
      await admin.getByText(/Columnas exactas requeridas/).waitFor();
      assert.equal(await admin.getByText(/Importación completada con éxito/).count(), 0);
    });

    await stage('propuesta académica y publicación desde interfaz', async () => {
      await navigate(admin, '/admin/asignaciones', '.asignaciones-page', '/demo/asignaciones/');
      const r = await response(admin, '/demo/asignaciones/generar/', 'POST',
        () => admin.getByRole('button', { name: /Generar Nueva Asignación/ }).first().click());
      assert.equal(r.status(), 201);
      const run = await r.json();
      assert.equal(run.resumen.alumnos, 200);
      assert.equal(run.resumen.asignadas, summary.escuelas.A.resumen.asignadas);
      const publication = await response(admin, '/demo/asignaciones/' + run.id + '/publicar/', 'POST',
        () => admin.getByRole('button', { name: /Publicar Horarios Oficiales/ }).click());
      assert.equal(publication.status(), 200);
      await shot(admin, 'asignacion-A');
    });

    await stage('alumno A consulta perfil, materias y horario propio', async () => {
      await navigate(student, '/alumno/perfil', '.alumno-perfil-page', '/alumnos/me/');
      await student.getByText('Matrícula ' + summary.usuarios.A.alumno, { exact: true }).first().waitFor();
      await navigate(student, '/alumno/inscripcion', '.alumno-inscripcion-page', '/nodos/');
      await student.getByText('Redes', { exact:true }).first().waitFor();
      const target = student.locator('.materia-row:not([aria-disabled="true"])').filter({ hasText: 'Redes' }).first();
      {
        await target.waitFor();
        await target.click();
        await student.getByRole('button', { name: 'Simular inscripción válida' }).click();
        const dialog = student.getByRole('dialog');
        await dialog.getByRole('button', { name: 'Confirmar', exact:true }).click();
        await student.getByText(/Simulación válida/).waitFor();
        results.preinscripcion = 'selección y confirmación simulada';
      }
      await navigate(student, '/alumno/horario', '.alumno-horario-page', '/demo/horario/me/');
      await student.getByText(/Horarios oficiales publicados/).waitFor();
      await shot(student, 'horario-A');
    });

    for (const [name, route, selector, endpoint] of [
      ['panel propietario', 'dashboard', '.comercial-dashboard', '/comercial/ingresos/'],
      ['instituciones propietario', 'clientes', '.clientes-page', '/comercial/instituciones/'],
      ['planes propietario', 'planes', '.planes-comerciales-page', '/comercial/planes/'],
      ['suscripciones propietario', 'suscripciones', '.suscripciones-page', '/comercial/suscripciones/'],
      ['licencias propietario', 'licencias', '.licencias-page', '/comercial/licencias/'],
      ['transacciones propietario', 'facturacion', '.facturacion-page', '/comercial/transacciones/'],
    ]) {
      await stage(name, async () => {
        await navigate(owner, ownerRoot + '/' + route, selector, endpoint);
        const messages = await owner.locator('[role="alert"]').allTextContents();
        assert.deepEqual(messages, []);
        if (name === 'transacciones propietario') {
          const row = owner.getByRole('row').filter({ hasText: 'demo_auditoria_A' });
          await row.getByText('Escuela A · Auditoría ficticia').waitFor();
          const downloadEvent = owner.waitForEvent('download');
          const pdfRequest = response(owner, '/comercial/comprobantes/' + summary.escuelas.A.comprobante + '/pdf/', 'GET',
            () => row.getByRole('button', { name: 'Descargar' }).click());
          const [download, receipt] = await Promise.all([downloadEvent, pdfRequest]);
          assert.equal(receipt.status(), 200);
          assert.match(download.suggestedFilename(), /^comprobante-.*\.pdf$/);
          await download.saveAs(path.join(artifacts, 'comprobante-propietario-A.pdf'));
          await shot(owner, 'transacciones-propietario');
        }
      });
    }

    await stage('alumno C sin licencia y reposición mediante checkout DEMO del propietario', async () => {
      const id = summary.escuelas.C.licencia;
      const token = await owner.evaluate(() => localStorage.getItem('ime_token'));
      const revoke = await owner.request.post(api + '/comercial/licencias/' + id + '/revocar/',
        { data: {}, headers: { Authorization: 'Bearer ' + token } });
      assert.equal(revoke.status(), 200);
      const studentC = await page();
      await login(studentC, summary.usuarios.C.alumno, '/alumno/horario');
      await navigate(studentC, '/alumno/horario', '.alumno-horario-page', '/demo/horario/me/', 403);
      await studentC.getByText(/No pudimos cargar tu horario/).waitFor();
      await shot(studentC, 'horario-C-sin-licencia');
      const adminC = await page();
      await login(adminC, summary.usuarios.C.admin, '/admin/dashboard');
      await navigate(adminC, '/admin/comercial/configurador', '.configurador-page');
      await adminC.locator('#input-alumnos').fill('200');
      await adminC.getByRole('button', { name: /Continuar al Checkout Seguro/ }).click();
      await adminC.locator('.total-price-large').getByText(/600\.00/).waitFor();
      await adminC.locator('.terms-checkbox').check();
      const created = await response(adminC, '/comercial/checkout/', 'POST',
        () => adminC.getByRole('button', { name: /Proceder al Pago Seguro/ }).click());
      assert.equal(created.status(), 201);
      const order = await created.json();
      assert.equal(order.proveedor, 'DEMO');
      results.orden_navegador = order.orden;
      await adminC.getByRole('button', { name: /Verificar Estado de la Orden/ }).click();
      await adminC.getByRole('heading', { name: /Espera de Acreditación/ }).waitFor();
      await navigate(owner, ownerRoot + '/dashboard', '.comercial-dashboard', '/comercial/demo/pendientes/');
      const approval = await response(owner, '/comercial/demo/confirmar/', 'POST',
        () => owner.locator('.prioridad-item').filter({ hasText: order.orden })
          .getByRole('button', { name: 'Aprobar orden DEMO' }).click());
      assert.equal(approval.status(), 200);
      await adminC.getByRole('button', { name: /Volver a Consultar Estado/ }).click();
      await adminC.getByText(/Pago Confirmado por Django/).waitFor();
      await shot(adminC, 'checkout-C-confirmado');
      await navigate(studentC, '/alumno/horario', '.alumno-horario-page', '/demo/horario/me/');
      await studentC.getByText(/Horarios oficiales publicados/).waitFor();
      await shot(studentC, 'horario-C-restablecido');
    });
  } finally {
    await browser.close();
    fs.writeFileSync(path.join(artifacts, 'chromium.json'), JSON.stringify(results, null, 2) + '\n');
  }
  if (results.fallos.length || results.erroresJS.length) process.exitCode = 1;
}
main().catch(err => { console.error(err.message); process.exitCode = 1; });
