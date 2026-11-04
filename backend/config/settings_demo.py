"""Demo Ubuntu exclusivamente local; DATABASE_URL nunca selecciona esta base."""
import os
from pathlib import Path
from .settings import *  # noqa: F403

DEMO_DATABASE = Path(os.environ.get('IME_DEMO_DATABASE', str(BASE_DIR / 'demo_backend_20261105.sqlite3'))).expanduser().resolve()
if DEMO_DATABASE.parent != BASE_DIR.resolve() or not DEMO_DATABASE.name.startswith('demo_') or DEMO_DATABASE.suffix != '.sqlite3':
    raise RuntimeError('La base demo debe ser backend/demo_*.sqlite3; ruta absoluta: ' + str(DEMO_DATABASE))
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': str(DEMO_DATABASE), 'OPTIONS': {'timeout': 30}}}
DEBUG = False
SECRET_KEY = 'inscripcionmadeeasy-demo-local-20261105-sin-datos-reales'
SIMPLE_JWT = {**SIMPLE_JWT, 'SIGNING_KEY': SECRET_KEY}
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']
CORS_ALLOWED_ORIGINS = ['http://127.0.0.1:5173', 'http://localhost:5173']
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
