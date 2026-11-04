// Login: resuelve al alumno por matrícula (numero_de_cuenta) vía /alumnos/?search=
(function () {
  'use strict';
  const { Auth, CFG, avisoError, Session } = window.IME;
  const form = document.getElementById('form-login');
  const alertas = document.getElementById('alertas');
  const btn = form.querySelector('button[type=submit]');

  const siguiente = () => {
    const next = new URLSearchParams(location.search).get('next');
    return next && next.startsWith('/') && !next.startsWith('//') ? next : CFG.urls.dashboard; // evita open-redirect
  };

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    alertas.innerHTML = '';
    const matricula = form.matricula.value.trim();
    if (!matricula || !form.password.value) return avisoError(alertas, { message: 'Escribe tu matrícula y tu contraseña.' });
    btn.disabled = true; btn.textContent = 'Entrando…';
    try {
      await Auth.login(matricula, form.password.value);
      location.assign(siguiente());
    } catch (err) {
      Session.clear();
      avisoError(alertas, err);
      btn.disabled = false; btn.textContent = 'Entrar';
    }
  });
})();
