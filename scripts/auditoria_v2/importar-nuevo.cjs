const { chromium } = require(process.env.IME_PLAYWRIGHT || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const evidence = path.resolve(process.argv[2]);
const web = process.env.IME_WEB_URL || 'http://127.0.0.1:15175';
const api = process.env.IME_API_URL || 'http://127.0.0.1:18085/api/v1';
const pword = process.env.IME_AUDIT_PASSWORD;
if (!pword || pword.length < 8) throw new Error('Define IME_AUDIT_PASSWORD para esta ejecución de prueba.');

(async () => {
  const browser = await chromium.launch();
  const metrics = path.join(evidence, 'chromium-importacion-nueva.json');
  const records = fs.existsSync(metrics) ? JSON.parse(fs.readFileSync(metrics)) : {};
  try {
    const page = await browser.newPage();
    page.setDefaultTimeout(12000);
    await page.route('**/api/v1/**', async route => {
      const suffix = route.request().url().split('/api/v1')[1];
      await route.fulfill({ response: await route.fetch({ url: api + suffix, timeout: 305000 }) });
    });
    await page.goto(web + '/login');
    await page.locator('#matricula').fill('auditoria_admin_a');
    await page.locator('#password').fill(pword);
    await page.getByRole('button', { name: 'Iniciar sesión' }).click();
    await page.waitForURL('**/admin/dashboard');
    await page.goto(web + '/admin/alumnos');
    await page.getByText('Estudiantes Registrados (0)').waitFor();
    await page.goto(web + '/admin/importar');
    for (const [file, label] of Object.entries({
      planes: 'Planes de Estudio', materias: 'Materias', alumnos: 'Alumnos',
      grupos: 'Grupos y Horarios', solicitudes: 'Solicitudes',
    })) {
      await page.locator('.tab-btn').filter({hasText: label}).click();
      await page.locator('input[type=file]').setInputFiles(path.join(evidence, 'escuela_A', file + '.csv'));
      await page.locator('.tab-btn.active .tab-badge-filled').waitFor();
    }
    for (const [kind, button] of [['validar', /Validar CSVs/], ['confirmar', /Confirmar e Importar/]]) {
      if (process.env.IME_FASE_IMPORTACION && process.env.IME_FASE_IMPORTACION !== kind) continue;
      const start = performance.now();
      const [response] = await Promise.all([
        page.waitForResponse(r => r.url().endsWith('/demo/importaciones/' + kind + '/') && r.request().method() === 'POST',
          {timeout: 310000}),
        page.getByRole('button', {name: button}).click(),
      ]);
      const time = +((performance.now() - start) / 1000).toFixed(4);
      assert.equal(response.status(), 200);
      const result = await response.json();
      assert.equal(result.filas.alumnos, 200);
      assert.ok(result.valido);
      if (kind === 'confirmar') assert.ok(result.importado);
      assert.ok(time > 15, 'La petición debe haber superado el límite web anterior');
      records[kind] = {segundos: time, status: response.status(), filas: result.filas};
      console.log('OK', kind, time + 's', '200 alumnos');
    }
    if (process.env.IME_FASE_IMPORTACION === 'validar') return;
    await page.getByText(/Importación completada con éxito/).waitFor();
    await page.screenshot({path: path.join(evidence, 'importacion-fresca-200.png')});
    await page.goto(web + '/admin/alumnos');
    await page.getByText('Estudiantes Registrados (200)').waitFor();
  } finally {
    await browser.close();
    fs.writeFileSync(metrics, JSON.stringify(records, null, 2));
  }
})().catch(err => { console.error(err.message); process.exitCode = 1; });
