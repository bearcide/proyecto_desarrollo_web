import uuid

from django.db import models

from .base import TimeStampedModel


class Tenant(TimeStampedModel):
    """Escuela / academia cliente del SaaS. Raíz del aislamiento multi-tenant."""

    class Estado(models.TextChoices):
        ACTIVO = 'ACTIVO', 'Activo'
        SUSPENDIDO = 'SUSPENDIDO', 'Suspendido'
        CANCELADO = 'CANCELADO', 'Cancelado'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre_comercial = models.CharField('nombre comercial', max_length=150)
    # TODO(negocio): el catálogo de tiers aún no está definido; cuando lo esté,
    # convertir a TextChoices o a FK hacia una tabla de planes.
    plan_suscripcion = models.CharField('plan de suscripción', max_length=50, db_index=True)
    estado = models.CharField(
        'estado', max_length=12, choices=Estado.choices, default=Estado.ACTIVO, db_index=True,
    )

    class Meta:
        verbose_name = 'escuela (tenant)'
        verbose_name_plural = 'escuelas (tenants)'
        ordering = ['nombre_comercial']

    def __str__(self):
        return self.nombre_comercial
