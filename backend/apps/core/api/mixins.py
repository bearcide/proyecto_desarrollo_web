from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from rest_framework.permissions import IsAuthenticated

from apps.core.services.identidad import resolver_identidad
from .exceptions import Conflict
from .permissions import TieneTenant


class TenantScopedMixin:
    """REGLA DE ORO MULTI-TENANT.

    - get_queryset(): solo filas de la escuela del usuario (contexto de identidad validado).
    - perform_create(): el tenant lo pone el servidor, nunca el cliente.
    - Un objeto de otra escuela responde 404, no 403 (no revela que existe).

    Usar ANTES de ModelViewSet en el MRO.
    """

    permission_classes = [IsAuthenticated, TieneTenant]
    tenant_lookup = 'tenant'  # Campo del modelo que apunta al Tenant ('pk' para Tenant).

    def get_identidad(self):
        return resolver_identidad(self.request)

    def get_tenant(self):
        return self.get_identidad().tenant

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if not getattr(self, 'swagger_fake_view', False):
            context['identidad'] = self.get_identidad()
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self, 'swagger_fake_view', False):
            return queryset.none()
        return queryset.filter(**{self.tenant_lookup: self.get_tenant().pk})

    def perform_create(self, serializer):
        self._guardar(serializer, tenant=self.get_tenant())

    def perform_update(self, serializer):
        self._guardar(serializer)

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise Conflict('No se puede eliminar: hay registros que dependen de este.')

    @staticmethod
    def _guardar(serializer, **extra):
        try:
            with transaction.atomic():
                serializer.save(**extra)
        except IntegrityError:
            # Respaldo ante carreras: la restricción de la BD ganó a la validación.
            raise Conflict('Ya existe un registro con esos datos en tu escuela.')
