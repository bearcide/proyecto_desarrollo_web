from django.conf import settings
from django.db import models


class MembresiaTenant(models.Model):
    """Acceso explícito de un usuario a una escuela; no implica permisos globales."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='membresias_tenant',
    )
    tenant = models.ForeignKey(
        'core.Tenant', on_delete=models.PROTECT, related_name='membresias',
    )
    activo = models.BooleanField(default=True)
    es_alumno = models.BooleanField(default=False)
    es_administrador = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'membresía de escuela'
        verbose_name_plural = 'membresías de escuelas'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'tenant'], name='uq_membresia_user_tenant',
            ),
        ]
