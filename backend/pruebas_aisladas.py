"""Ejecutar: backend/venv/bin/python -B backend/pruebas_aisladas.py.

No admite SQLite a disco. No instala dependencias ni modifica bases existentes.
"""
import os
import sys


def bloquear_sqlite_disco(event, args):
    if event == 'sqlite3.connect':
        name = str(args[0])
        if name != ':memory:' and not (name.startswith('file:memorydb_') and 'mode=memory' in name):
            raise RuntimeError('Conexión SQLite fuera de memoria rechazada: ' + name)


sys.addaudithook(bloquear_sqlite_disco)
os.environ['DJANGO_SETTINGS_MODULE'] = 'apps.core.tests.settings_aislados'
import django
from django.conf import settings

django.setup()
assert set(settings.DATABASES) == {'default'}
assert settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3'
assert settings.DATABASES['default']['NAME'] == ':memory:'
assert settings.DATABASES['default']['TEST']['NAME'] == ':memory:'
from django.core.management import call_command
from django.test.runner import DiscoverRunner

call_command('makemigrations', check=True, dry_run=True, verbosity=1)
raise SystemExit(DiscoverRunner(verbosity=2, interactive=False).run_tests(['apps.core.tests']))
