"""Oferta por grupos y resultados persistentes del motor local de asignación."""
from django.core.exceptions import ValidationError
from django.db import models


class Grupo(models.Model):
    tenant = models.ForeignKey('core.Tenant', on_delete=models.PROTECT, related_name='grupos')
    nodo = models.ForeignKey('core.Nodo', on_delete=models.PROTECT, related_name='grupos')
    clave = models.CharField(max_length=50)
    profesor = models.CharField(max_length=150)
    cupo = models.PositiveIntegerField()
    horarios = models.JSONField(default=list)

    class Meta:
        ordering = ['clave', 'pk']
        constraints = [models.UniqueConstraint(fields=['tenant', 'nodo', 'clave'], name='uq_grupo_tenant_nodo_clave')]

    def clean(self):
        super().clean()
        if self.tenant_id and self.nodo_id and self.nodo.tenant_id != self.tenant_id:
            raise ValidationError({'nodo': 'La materia pertenece a otra escuela.'})


class SolicitudMateria(models.Model):
    tenant = models.ForeignKey('core.Tenant', on_delete=models.PROTECT, related_name='solicitudes_materia')
    alumno = models.ForeignKey('core.Alumno', on_delete=models.PROTECT, related_name='solicitudes_materia')
    nodo = models.ForeignKey('core.Nodo', on_delete=models.PROTECT, related_name='solicitudes_materia')
    preferencia = models.PositiveIntegerField(default=1)
    prioridad_institucional = models.PositiveIntegerField(default=100)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['tenant', 'alumno', 'nodo'], name='uq_solicitud_tenant_alumno_nodo')]

    def clean(self):
        super().clean()
        if self.tenant_id:
            for campo in ('alumno', 'nodo'):
                if getattr(self, campo + '_id') and getattr(self, campo).tenant_id != self.tenant_id:
                    raise ValidationError({campo: 'La referencia pertenece a otra escuela.'})


class EjecucionAsignacion(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = 'BORRADOR', 'Borrador'
        PUBLICADO = 'PUBLICADO', 'Publicado'
        ARCHIVADO = 'ARCHIVADO', 'Archivado'

    tenant = models.ForeignKey('core.Tenant', on_delete=models.PROTECT, related_name='ejecuciones_asignacion')
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.BORRADOR)
    politica = models.JSONField(default=dict)
    resumen = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-pk']
        constraints = [models.UniqueConstraint(fields=['tenant'], condition=models.Q(estado='PUBLICADO'), name='uq_publicacion_vigente_tenant')]


class ResultadoAsignacion(models.Model):
    class Estado(models.TextChoices):
        ASIGNADA = 'ASIGNADA', 'Asignada'
        PENDIENTE = 'PENDIENTE', 'Pendiente'

    ejecucion = models.ForeignKey('core.EjecucionAsignacion', on_delete=models.CASCADE, related_name='resultados')
    alumno = models.ForeignKey('core.Alumno', on_delete=models.PROTECT, related_name='resultados_asignacion')
    nodo = models.ForeignKey('core.Nodo', on_delete=models.PROTECT, related_name='resultados_asignacion')
    grupo = models.ForeignKey('core.Grupo', on_delete=models.PROTECT, null=True, blank=True, related_name='resultados_asignacion')
    estado = models.CharField(max_length=10, choices=Estado.choices)
    motivo = models.CharField(max_length=50, blank=True, default='')
    detalle = models.JSONField(default=dict)

    class Meta:
        ordering = ['alumno_id', 'nodo_id']
        constraints = [models.UniqueConstraint(fields=['ejecucion', 'alumno', 'nodo'], name='uq_resultado_ejec_alumno_nodo')]

    def clean(self):
        super().clean()
        if self.ejecucion_id:
            tenant_id = self.ejecucion.tenant_id
            for campo in ('alumno', 'nodo', 'grupo'):
                if getattr(self, campo + '_id') and getattr(self, campo).tenant_id != tenant_id:
                    raise ValidationError({campo: 'La referencia pertenece a otra escuela.'})
        if self.grupo_id and self.nodo_id and self.grupo.nodo_id != self.nodo_id:
            raise ValidationError({'grupo': 'El grupo pertenece a otra materia.'})
