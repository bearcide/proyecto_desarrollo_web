"""Base explícita de pagos; nunca utiliza DATABASE_URL ni la demo anterior."""
import os
from pathlib import Path
from .settings_demo import *  # noqa: F403

_path = Path(os.environ['PAGOS_DEMO_DATABASE']).expanduser()
if not _path.is_absolute() or _path.is_symlink():
    raise RuntimeError('PAGOS_DEMO_DATABASE debe ser una ruta absoluta sin symlink.')
_path = _path.resolve()
if _path.parent != BASE_DIR.resolve() or not _path.name.startswith('demo_pagos_') or _path.suffix != '.sqlite3':
    raise RuntimeError('Solo se admite backend/demo_pagos_*.sqlite3.')
if not _path.is_file():
    raise RuntimeError('Crear primero la base con demo_pagos.py; no se abre una ruta inexistente.')
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': str(_path),
                         'TEST': {'NAME': ':memory:'}}}
COMMERCIAL_PROVIDER = 'DEMO'
STRIPE_SECRET_KEY = ''
STRIPE_WEBHOOK_SECRET = ''
SECRET_KEY = 'ime-pagos-demo-local-aislada-no-produccion-20261112'
SIMPLE_JWT = {**SIMPLE_JWT, 'SIGNING_KEY': SECRET_KEY}
CORS_ALLOWED_ORIGINS = [*CORS_ALLOWED_ORIGINS, 'http://127.0.0.1:5174', 'http://localhost:5174']
