from django.db import IntegrityError
from django.db.models import ProtectedError
from rest_framework.exceptions import PermissionDenied

from .exceptions import Conflict
from .permissions import TieneTenant


class TenantScopedMixin:
    """REGLA DE ORO MULTI-TENANT.

    - get_queryset(): solo filas de la escuela del usuario (request.user.tenant).
    - perform_create(): el tenant lo pone el servidor, nunca el cliente.
    - Un objeto de otra escuela responde 404, no 403 (no revela que existe).

    Usar ANTES de ModelViewSet en el MRO.
    """

    permission_classes = [TieneTenant]
    tenant_lookup = 'tenant'  # Campo del modelo que apunta al Tenant ('pk' para Tenant).

    def get_tenant(self):
        tenant = getattr(self.request.user, 'tenant', None)
        if tenant is None:
            raise PermissionDenied(TieneTenant.message)
        return tenant

    def get_queryset(self):
        return super().get_queryset().filter(**{self.tenant_lookup: self.get_tenant()})

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
            serializer.save(**extra)
        except IntegrityError:
            # Respaldo ante carreras: la restricción de la BD ganó a la validación.
            raise Conflict('Ya existe un registro con esos datos en tu escuela.')
