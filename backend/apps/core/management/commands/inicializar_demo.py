"""Crea únicamente una base de demo nueva, nunca reutiliza un archivo existente."""
import json
import os
from pathlib import Path
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from apps.core.models import MembresiaTenant, Tenant
from apps.core.services.datos_demo import archivos_demo
from apps.core.services.importacion_csv import importar


class Command(BaseCommand):
    requires_system_checks = []
    requires_migrations_checks = False
    help = 'Inicializa una SQLite demo NUEVA con administrador y opcionalmente 100 alumnos ficticios.'

    def add_arguments(self, parser):
        parser.add_argument('--con-datos', action='store_true')

    def handle(self, *args, **options):
        configured=settings.DATABASES['default']
        path=getattr(settings,'DEMO_DATABASE',None)
        if path is None or configured['ENGINE']!='django.db.backends.sqlite3' or str(path)!=str(configured['NAME']):
            raise CommandError('Usa exclusivamente --settings=config.settings_demo.')
        path=Path(path).resolve()
        if path.parent!=Path(settings.BASE_DIR).resolve() or not path.name.startswith('demo_') or path.suffix!='.sqlite3':
            raise CommandError('Ruta demo no permitida: '+str(path))
        self.stdout.write('BASE DEMO ABSOLUTA VERIFICADA: '+str(path))
        # O_EXCL evita carreras y cualquier modificación de archivos preexistentes.
        try:
            fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            os.close(fd)
        except FileExistsError:
            raise CommandError('La base ya existe. No se modifica: '+str(path))
        call_command('migrate',database='default',interactive=False,verbosity=1)
        with transaction.atomic():
            tenant=Tenant.objects.create(nombre_comercial='Escuela Demo Local',plan_suscripcion='DEMO')
            admin=get_user_model().objects.create_user(username='demo_admin',password='DemoLocal2026!')
            MembresiaTenant.objects.create(user=admin,tenant=tenant,es_administrador=True)
            report=importar(tenant,archivos_demo(),confirmar=True) if options['con_datos'] else None
        self.stdout.write(json.dumps({'database':str(path),'tenant':str(tenant.pk),'admin':'demo_admin',
            'password_demo':'DemoLocal2026!','alumno':'D001' if report else None,'importacion':report},ensure_ascii=False))
