"""Comercialización del SaaS; deliberadamente separada de cobranza escolar."""
import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator


class Base(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['-creado']


class Plan(Base):
    codigo = models.SlugField(unique=True)
    nombre = models.CharField(max_length=150)
    funcionalidades = models.JSONField(default=dict)
    max_alumnos = models.PositiveIntegerField(default=100)
    max_planteles = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    activo = models.BooleanField(default=True)


class Precio(Base):
    MODALIDADES = [(x, x) for x in ('monthly', 'annual', 'process', 'institutional', 'perpetual', 'hybrid', 'enterprise', 'maintenance')]
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    modalidad = models.CharField(max_length=20, choices=MODALIDADES)
    importe = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    por_alumno = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    moneda = models.CharField(max_length=3, default='MXN', choices=[('MXN', 'MXN')])
    dias = models.PositiveIntegerField(default=365, validators=[MinValueValidator(1)])
    activo = models.BooleanField(default=True)

    @property
    def recurrente(self):
        return self.modalidad in ('monthly', 'annual', 'hybrid', 'maintenance')

    class Meta(Base.Meta):
        constraints = [models.CheckConstraint(condition=models.Q(importe__gt=0, por_alumno__gte=0, dias__gt=0), name='com_precio_positivo')]


class Contrato(Base):
    tenant = models.ForeignKey('core.Tenant', on_delete=models.PROTECT)
    precio = models.ForeignKey(Precio, on_delete=models.PROTECT)
    inicio = models.DateTimeField()
    fin = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=12, choices=[(x,x) for x in ('draft','active','canceled')], default='draft')
    condiciones = models.TextField(blank=True)

    class Meta(Base.Meta):
        constraints = [models.CheckConstraint(condition=models.Q(fin__isnull=True) | models.Q(fin__gt=models.F('inicio')), name='com_contrato_fechas')]


class Orden(Base):
    tenant = models.ForeignKey('core.Tenant', on_delete=models.PROTECT)
    precio = models.ForeignKey(Precio, on_delete=models.PROTECT)
    contrato = models.ForeignKey(Contrato, null=True, on_delete=models.PROTECT)
    alumnos = models.PositiveIntegerField(default=1)
    importe = models.DecimalField(max_digits=12, decimal_places=2)
    moneda = models.CharField(max_length=3)
    condiciones = models.JSONField(default=dict)
    proveedor = models.CharField(max_length=10, choices=[('DEMO','DEMO'),('stripe','stripe')])
    clave = models.CharField(max_length=100)
    estado = models.CharField(max_length=12, choices=[(x,x) for x in ('pending','paid','failed')], default='pending')
    sesion = models.CharField(max_length=200, blank=True)
    url = models.URLField(max_length=2048, blank=True)

    class Meta(Base.Meta):
        constraints = [models.UniqueConstraint(fields=['tenant','clave'], name='com_orden_idempotente')]


class Suscripcion(Base):
    orden = models.OneToOneField(Orden, on_delete=models.PROTECT)
    referencia = models.CharField(max_length=200, unique=True)
    estado = models.CharField(max_length=12, choices=[(x,x) for x in ('pending','active','past_due','canceled')], default='pending')
    fin_periodo = models.DateTimeField(null=True)
    cancel_at_period_end = models.BooleanField(default=False)


class Licencia(Base):
    orden = models.OneToOneField(Orden, on_delete=models.PROTECT)
    estado = models.CharField(max_length=12, choices=[('active','active'),('revoked','revoked')], default='active')
    inicio = models.DateTimeField()
    fin = models.DateTimeField(null=True)
    funcionalidades = models.JSONField(default=dict)
    max_alumnos = models.PositiveIntegerField()
    max_planteles = models.PositiveIntegerField()


class Transaccion(Base):
    orden = models.ForeignKey(Orden, on_delete=models.PROTECT)
    referencia = models.CharField(max_length=200)
    proveedor = models.CharField(max_length=10)
    importe = models.DecimalField(max_digits=12, decimal_places=2)
    moneda = models.CharField(max_length=3)
    estado = models.CharField(max_length=12, choices=[(x,x) for x in ('paid','failed','pending')])

    class Meta(Base.Meta):
        constraints = [models.UniqueConstraint(fields=['proveedor','referencia'], name='com_transaccion_unica')]


class Evento(Base):
    referencia = models.CharField(max_length=200, unique=True)
    tipo = models.CharField(max_length=100)
    hash = models.CharField(max_length=64)
    resultado = models.CharField(max_length=30, default='received')


class Comprobante(Base):
    transaccion = models.OneToOneField(Transaccion, on_delete=models.PROTECT)


class SolicitudFactura(Base):
    orden = models.OneToOneField(Orden, on_delete=models.PROTECT)
    rfc = models.CharField(max_length=13)
    razon_social = models.CharField(max_length=250)
    regimen = models.CharField(max_length=3)
    codigo_postal = models.CharField(max_length=5)
    uso_cfdi = models.CharField(max_length=3)
    estado = models.CharField(max_length=12, choices=[(x,x) for x in ('requested','processing','rejected')], default='requested')
