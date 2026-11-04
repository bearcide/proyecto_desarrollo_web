"""Operación explícita de plataforma; nunca inferir roles globales."""
import getpass
import json
import logging
from uuid import UUID

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models import MembresiaTenant, Tenant

logger = logging.getLogger('apps.core.auditoria')


class Command(BaseCommand):
    help = 'Asigna administración escolar a un usuario existente. Requiere acceso operativo autorizado.'

    def add_arguments(self, parser):
        parser.add_argument('--user-id', type=int, required=True)
        parser.add_argument('--tenant-id', required=True)
        parser.add_argument('--referencia', required=True)
        parser.add_argument('--simular', action='store_true')
        parser.add_argument('--reactivar', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        reference = options['referencia'].strip()
        if not reference or len(reference) > 255:
            raise CommandError('Referencia requerida, máximo 255 caracteres.')
        try:
            tenant_id = UUID(options['tenant_id'])
            user = get_user_model().objects.select_for_update().get(pk=options['user_id'], is_active=True)
            tenant = Tenant.objects.select_for_update().get(pk=tenant_id, estado=Tenant.Estado.ACTIVO)
        except (ValueError, TypeError, get_user_model().DoesNotExist, Tenant.DoesNotExist):
            raise CommandError('Usuario o escuela inválidos o inactivos.')
        membership = MembresiaTenant.objects.select_for_update().filter(user=user, tenant=tenant).first()
        if membership and not membership.activo and not options['reactivar']:
            raise CommandError('Membresía inactiva: requiere --reactivar explícito.')
        before = None if membership is None else {
            'activo': membership.activo, 'es_alumno': membership.es_alumno,
            'es_administrador': membership.es_administrador,
        }
        if not options['simular']:
            if membership is None:
                membership = MembresiaTenant.objects.create(user=user, tenant=tenant, es_administrador=True)
            else:
                membership.activo = True
                membership.es_administrador = True
                membership.save(update_fields=['activo', 'es_administrador'])
        event = {'operador': getpass.getuser(), 'operacion': 'aprovisionar_admin_escolar', 'user_id': user.pk,
                 'tenant_id': str(tenant.pk), 'referencia': reference,
                 'simulacion': options['simular'], 'antes': before,
                 'despues': {'activo': True, 'es_administrador': True,
                             'es_alumno': before['es_alumno'] if before else False}}
        line = json.dumps(event, ensure_ascii=False)
        self.stdout.write(line)
        transaction.on_commit(lambda: logger.info(line))
