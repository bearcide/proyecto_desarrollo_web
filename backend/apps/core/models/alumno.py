from django.core.exceptions import ValidationError
from django.db import models

from .base import TimeStampedModel
from .plan_estudios import PlanEstudios
from .tenant import Tenant


class Alumno(TimeStampedModel):
    """Alumno de una escuela, inscrito en un plan de estudios.

    Equivale a la clase Java Alumno. "Alumnado" (la colección del Java) es en BD
    simplemente esta tabla; su lógica irá en repositories/.
    """

    tenant = models.ForeignKey(
        Tenant, on_delete=models.PROTECT, related_name='alumnos', verbose_name='escuela',
    )
    plan_estudios = models.ForeignKey(
        PlanEstudios, on_delete=models.PROTECT, related_name='alumnos',
        verbose_name='plan de estudios',
    )
    nombre = models.CharField('nombre', max_length=100)
    apellido_paterno = models.CharField('apellido paterno', max_length=100)
    apellido_materno = models.CharField('apellido materno', max_length=100, blank=True)
    # Se asigna desde services/ (generación automática). Nulo hasta entonces; PostgreSQL
    # permite varios NULL bajo la restricción de unicidad. Solo lectura en la API.
    numero_de_cuenta = models.CharField(
        'número de cuenta', max_length=32, null=True, blank=True, editable=False,
    )
    domicilio = models.CharField('domicilio', max_length=255, blank=True)
    edad = models.PositiveIntegerField('edad', default=0)
    semestre = models.PositiveIntegerField('semestre', default=0)
    materias_pasadas = models.PositiveIntegerField('materias pasadas', default=0)
    materias_cursadas = models.PositiveIntegerField('materias cursadas', default=0)
    creditos = models.PositiveIntegerField('créditos', default=0)
    promedio_acumulado = models.FloatField('promedio acumulado', default=0.0)
    indicador_escolar = models.FloatField('indicador escolar', default=0.0)
    activo = models.BooleanField('activo', default=True)

    class Meta:
        verbose_name = 'alumno'
        verbose_name_plural = 'alumnos'
        ordering = ['tenant', 'apellido_paterno', 'apellido_materno', 'nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'numero_de_cuenta'], name='uq_alumno_tenant_numcuenta',
            ),
        ]
        indexes = [
            models.Index(fields=['tenant', 'plan_estudios'], name='ix_alumno_tenant_plan'),
        ]

    def __str__(self):
        cuenta = self.numero_de_cuenta or 'sin cuenta'
        return f'{self.nombre} {self.apellido_paterno} {self.apellido_materno} ({cuenta})'.replace('  ', ' ')

    def clean(self):
        super().clean()
        if self.plan_estudios_id and self.tenant_id and self.plan_estudios.tenant_id != self.tenant_id:
            raise ValidationError('El plan de estudios pertenece a otra escuela.')
