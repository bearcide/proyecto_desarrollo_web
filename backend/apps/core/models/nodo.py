from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from .base import TimeStampedModel
from .plan_estudios import PlanEstudios
from .tenant import Tenant


class Nodo(TimeStampedModel):
    """Materia dentro de un plan de estudios. Vértice del grafo de prerrequisitos.

    Equivale a la clase Java Nodo. Los campos `passed` y `calificacionActas` del Java
    son estado por alumno (no de la materia) y NO se portan aquí.
    """

    tenant = models.ForeignKey(
        Tenant, on_delete=models.PROTECT, related_name='nodos', verbose_name='escuela',
    )
    plan_estudios = models.ForeignKey(
        PlanEstudios, on_delete=models.PROTECT, related_name='nodos',
        verbose_name='plan de estudios',
    )
    # Texto (no número): evita pérdidas como el literal octal 0406 del Java.
    clave = models.CharField('clave', max_length=30)
    nombre = models.CharField('nombre', max_length=150)
    creditos = models.PositiveIntegerField('créditos')
    semestre = models.PositiveIntegerField('semestre')
    # Aristas del grafo: "este nodo requiere haber aprobado estos otros".
    prerrequisitos = models.ManyToManyField(
        'self', through='Prerrequisito', through_fields=('nodo', 'prerrequisito'),
        symmetrical=False, related_name='es_prerrequisito_de', blank=True,
        verbose_name='prerrequisitos',
    )

    class Meta:
        verbose_name = 'nodo (materia)'
        verbose_name_plural = 'nodos (materias)'
        ordering = ['plan_estudios', 'semestre', 'clave']
        constraints = [
            # Regla de negocio: la clave es única en toda la escuela (no solo por plan).
            models.UniqueConstraint(fields=['tenant', 'clave'], name='uq_nodo_tenant_clave'),
        ]
        indexes = [
            models.Index(fields=['tenant', 'plan_estudios'], name='ix_nodo_tenant_plan'),
        ]

    def __str__(self):
        return f'{self.clave} {self.nombre}'

    def clean(self):
        super().clean()
        if self.plan_estudios_id and self.tenant_id and self.plan_estudios.tenant_id != self.tenant_id:
            raise ValidationError('El plan de estudios pertenece a otra escuela.')


class Prerrequisito(TimeStampedModel):
    """Arista dirigida del grafo: `nodo` requiere `prerrequisito`.

    La detección de ciclos NO va aquí: es lógica de negocio (capa services/).
    """

    tenant = models.ForeignKey(
        Tenant, on_delete=models.PROTECT, related_name='prerrequisitos', verbose_name='escuela',
    )
    nodo = models.ForeignKey(
        Nodo, on_delete=models.CASCADE, related_name='aristas_prerrequisito',
        verbose_name='materia',
    )
    prerrequisito = models.ForeignKey(
        Nodo, on_delete=models.CASCADE, related_name='aristas_dependientes',
        verbose_name='materia requerida',
    )

    class Meta:
        verbose_name = 'prerrequisito'
        verbose_name_plural = 'prerrequisitos'
        constraints = [
            models.UniqueConstraint(fields=['nodo', 'prerrequisito'], name='uq_prerreq_nodo_prerreq'),
            models.CheckConstraint(
                condition=~Q(nodo=F('prerrequisito')), name='ck_prerreq_no_autociclo',
            ),
        ]
        indexes = [
            models.Index(fields=['tenant', 'nodo'], name='ix_prerreq_tenant_nodo'),
        ]

    def __str__(self):
        return f'{self.nodo} requiere {self.prerrequisito}'

    def clean(self):
        super().clean()
        if self.nodo_id and self.prerrequisito_id:
            if self.nodo_id == self.prerrequisito_id:
                raise ValidationError('Una materia no puede ser prerrequisito de sí misma.')
            if self.nodo.plan_estudios_id != self.prerrequisito.plan_estudios_id:
                raise ValidationError('Los dos nodos deben pertenecer al mismo plan de estudios.')
            if self.tenant_id and (
                self.nodo.tenant_id != self.tenant_id
                or self.prerrequisito.tenant_id != self.tenant_id
            ):
                raise ValidationError('Los nodos pertenecen a otra escuela.')


class NodoEstadistico(TimeStampedModel):
    """Métricas por materia. Equivale a la clase Java NodoEstadistico."""

    tenant = models.ForeignKey(
        Tenant, on_delete=models.PROTECT, related_name='estadisticas_nodo',
        verbose_name='escuela',
    )
    nodo = models.OneToOneField(
        Nodo, on_delete=models.CASCADE, related_name='estadistica', verbose_name='materia',
    )
    alumnos_inscritos = models.PositiveIntegerField('alumnos inscritos', default=0)
    alumnos_pasados = models.PositiveIntegerField('alumnos pasados', default=0)
    # Float, como el double del Java.
    promedio_acumulado = models.FloatField('promedio acumulado', default=0.0)

    class Meta:
        verbose_name = 'estadística de materia'
        verbose_name_plural = 'estadísticas de materias'

    def __str__(self):
        return f'Estadística de {self.nodo}'

    def clean(self):
        super().clean()
        if self.nodo_id and self.tenant_id and self.nodo.tenant_id != self.tenant_id:
            raise ValidationError('La materia pertenece a otra escuela.')
