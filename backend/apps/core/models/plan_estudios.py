from django.db import models

from .base import TimeStampedModel
from .tenant import Tenant


class PlanEstudios(TimeStampedModel):
    """Plan de estudios de una escuela. Contiene el grafo de materias (Nodo)."""

    tenant = models.ForeignKey(
        Tenant, on_delete=models.PROTECT, related_name='planes_estudios',
        verbose_name='escuela',
    )
    nombre = models.CharField('nombre', max_length=150)
    descripcion = models.TextField('descripción', blank=True)
    activo = models.BooleanField('activo', default=True)

    class Meta:
        verbose_name = 'plan de estudios'
        verbose_name_plural = 'planes de estudios'
        ordering = ['tenant', 'nombre']
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'nombre'], name='uq_plan_tenant_nombre'),
        ]

    def __str__(self):
        return f'{self.nombre} ({self.tenant})'
