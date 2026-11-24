import hashlib
from collections.abc import Mapping
import re
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from drf_spectacular.utils import extend_schema, inline_serializer
from apps.core.models import Tenant
from apps.core.services.identidad import resolver_identidad
from . import models as m
from . import services as s


def propietario(user):
    return user.is_authenticated and user.is_active and user.is_superuser


def tenant_actual(request):
    if propietario(request.user):
        valor = request.headers.get('X-Tenant-ID')
        campo = serializers.UUIDField()
        ident = campo.run_validation(valor)
        try: return Tenant.objects.get(pk=ident)
        except Tenant.DoesNotExist: raise ValidationError('Institución inexistente.')
    identidad = resolver_identidad(request)
    if not identidad.membresia.es_administrador:
        raise PermissionDenied('Se requiere administrador escolar.')
    return identidad.tenant


class Estricto(serializers.ModelSerializer):
    def to_internal_value(self, data):
        extra = set(data) - set(self.fields)
        readonly = {k for k in data if k in self.fields and self.fields[k].read_only}
        if extra or readonly:
            raise ValidationError({k:'Campo no editable.' for k in extra | readonly})
        return super().to_internal_value(data)


def serializador(modelo):
    class S(Estricto):
        class Meta:
            model = modelo
            fields = '__all__'
            read_only_fields = ['id','creado']
    S.__name__ = modelo.__name__ + 'ComercialSerializer'
    return S


class FacturaSerializer(Estricto):
    class Meta:
        model = m.SolicitudFactura
        fields = '__all__'
        read_only_fields = ['id','creado','estado']

    def validate(self, attrs):
        request = self.context['request']
        orden = attrs['orden']
        if orden.estado != 'paid': raise ValidationError('La orden debe estar pagada.')
        if not propietario(request.user) and orden.tenant_id != tenant_actual(request).id:
            raise PermissionDenied()
        for field, pattern in [('rfc',r'[A-ZÑ&]{3,4}[0-9]{6}[A-Z0-9]{3}'),('regimen',r'[0-9]{3}'),('codigo_postal',r'[0-9]{5}'),('uso_cfdi',r'[A-Z][0-9]{2}')]:
            if not re.fullmatch(pattern,attrs.get(field,'')):
                raise ValidationError({field:'Formato inválido.'})
        return attrs


class Lectura(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    tenant_path = 'tenant'
    solo_propietario = False
    catalogo = False

    def get_queryset(self):
        qs = self.queryset.all()
        if propietario(self.request.user): return qs
        if self.solo_propietario: raise PermissionDenied()
        tenant = tenant_actual(self.request)
        if self.catalogo: return qs.filter(activo=True)
        return qs.filter(**{self.tenant_path:tenant})


class Catalogo(Lectura, viewsets.ModelViewSet):
    http_method_names = ['get','post','patch','head','options']
    catalogo = True

    def create(self, request, *args, **kwargs):
        if not propietario(request.user): raise PermissionDenied()
        return super().create(request,*args,**kwargs)

    def partial_update(self, request,*args,**kwargs):
        if not propietario(request.user): raise PermissionDenied()
        return super().partial_update(request,*args,**kwargs)


class PlanView(Catalogo):
    queryset = m.Plan.objects.all()
    serializer_class = serializador(m.Plan)

    def perform_create(self, serializer):
        if not isinstance(serializer.validated_data.get('funcionalidades',{}),dict): raise ValidationError('funcionalidades debe ser un objeto.')
        serializer.save()

    def perform_update(self, serializer):
        if not isinstance(serializer.validated_data.get('funcionalidades',{}),dict): raise ValidationError('funcionalidades debe ser un objeto.')
        serializer.save()


class PrecioView(Catalogo):
    queryset = m.Precio.objects.all()
    serializer_class = serializador(m.Precio)
    http_method_names = ['get','post','head','options']


class InstitucionView(Catalogo):
    queryset = Tenant.objects.all()
    serializer_class = serializador(Tenant)
    solo_propietario = True


class ContratoView(Catalogo):
    queryset = m.Contrato.objects.all()
    serializer_class = serializador(m.Contrato)
    catalogo = False

    def perform_create(self, serializer):
        self.validar_fechas(serializer)
        serializer.save()

    def validar_fechas(self, serializer):
        data = serializer.validated_data
        inicio = data.get('inicio',getattr(serializer.instance,'inicio',None))
        fin = data.get('fin',getattr(serializer.instance,'fin',None))
        if fin is not None and inicio is not None and fin <= inicio:
            raise ValidationError({'fin':'Debe ser posterior al inicio.'})

    def perform_update(self, serializer):
        if {'tenant','precio'} & set(serializer.validated_data):
            raise ValidationError('Institución y precio del contrato son inmutables.')
        self.validar_fechas(serializer)
        serializer.save()


class OrdenView(Lectura):
    queryset = m.Orden.objects.all()
    serializer_class = serializador(m.Orden)


class SuscripcionSerializer(serializador(m.Suscripcion)):
    plan_nombre = serializers.CharField(source='orden.condiciones.nombre', read_only=True)
    modalidad = serializers.CharField(source='orden.condiciones.modalidad', read_only=True)
    importe = serializers.DecimalField(source='orden.importe', max_digits=12, decimal_places=2, read_only=True)
    moneda = serializers.CharField(source='orden.moneda', read_only=True)
    tenant = serializers.UUIDField(source='orden.tenant_id', read_only=True)


class SuscripcionView(Lectura):
    queryset = m.Suscripcion.objects.select_related('orden')
    serializer_class = SuscripcionSerializer
    tenant_path = 'orden__tenant'

    @action(detail=True,methods=['post'])
    def cancelar(self, request, pk=None):
        with transaction.atomic():
            sub = self.get_queryset().select_related(None).select_for_update().get(pk=self.get_object().pk)
            if sub.estado == 'canceled': return Response(self.get_serializer(sub).data)
            if sub.orden.proveedor == 'stripe':
                stripe = s.stripe_api()
                try: stripe.Subscription.modify(sub.referencia,cancel_at_period_end=True,idempotency_key='cancel-'+str(sub.id))
                except stripe.StripeError as exc: raise s.ProveedorNoDisponible() from exc
            sub.cancel_at_period_end = True
            sub.save(update_fields=['cancel_at_period_end'])
        return Response(self.get_serializer(sub).data)


class LicenciaView(Lectura):
    queryset = m.Licencia.objects.all()
    serializer_class = serializador(m.Licencia)
    tenant_path = 'orden__tenant'

    @action(detail=True,methods=['post'])
    def revocar(self,request,pk=None):
        if not propietario(request.user): raise PermissionDenied()
        obj = self.get_object()
        with transaction.atomic():
            obj.estado = 'revoked'
            obj.save(update_fields=['estado'])
            m.Evento.objects.get_or_create(referencia='revoke-'+str(obj.id),defaults={
                'tipo':'internal.license.revoked','hash':hashlib.sha256(str(request.user.pk).encode()).hexdigest(),'resultado':'processed'})
        return Response(self.get_serializer(obj).data)


class TransaccionSerializer(serializador(m.Transaccion)):
    comprobante_id = serializers.UUIDField(source='comprobante.pk', allow_null=True, read_only=True)
    institucion = serializers.CharField(source='orden.tenant.nombre_comercial', read_only=True)


class TransaccionView(Lectura):
    queryset = m.Transaccion.objects.select_related('orden__tenant', 'comprobante')
    serializer_class = TransaccionSerializer
    tenant_path = 'orden__tenant'


def pdf_interno(comprobante):
    tx = comprobante.transaccion
    lines = ['INSCRIPCIONMADEEASY - COMPROBANTE INTERNO', 'SIN VALIDEZ FISCAL - NO ES CFDI',
             'Proveedor: '+tx.proveedor, 'Folio: '+str(comprobante.id),
             'Orden: '+str(tx.orden_id), 'Importe: '+str(tx.importe)+' '+tx.moneda,
             'Fecha: '+comprobante.creado.isoformat()]
    def escape(text): return text.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
    stream = ('BT /F1 11 Tf 45 790 Td '+' 0 -25 Td '.join('('+escape(line)+') Tj' for line in lines)+' ET').encode('ascii')
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>', b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
               b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
               b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'\nendstream']
    result = b'%PDF-1.4\n'
    offsets = [0]
    for i,obj in enumerate(objects,1):
        offsets.append(len(result)); result += str(i).encode()+b' 0 obj\n'+obj+b'\nendobj\n'
    xref = len(result)
    result += b'xref\n0 6\n0000000000 65535 f \n'
    result += b''.join(f'{offset:010} 00000 n \n'.encode() for offset in offsets[1:])
    return result + f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode()


class ComprobanteView(Lectura):
    queryset = m.Comprobante.objects.all()
    serializer_class = serializador(m.Comprobante)
    tenant_path = 'transaccion__orden__tenant'

    @action(detail=True,methods=['get'])
    def pdf(self,request,pk=None):
        obj = self.get_object()
        response = HttpResponse(pdf_interno(obj),content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="comprobante-{obj.id}.pdf"'
        response['Cache-Control'] = 'private, no-store'
        return response


class FacturaView(Lectura, viewsets.GenericViewSet):
    from rest_framework.mixins import CreateModelMixin
    queryset = m.SolicitudFactura.objects.all()
    serializer_class = FacturaSerializer
    tenant_path = 'orden__tenant'

    def create(self,request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=201)

    def partial_update(self,request,pk=None):
        if not propietario(request.user): raise PermissionDenied()
        if set(request.data) != {'estado'} or request.data['estado'] not in ('requested','processing','rejected'):
            raise ValidationError('Estado no permitido; emisión fiscal no disponible.')
        obj = self.get_object(); obj.estado = request.data['estado']; obj.save(update_fields=['estado'])
        return Response(self.get_serializer(obj).data)


class EventoView(Lectura):
    queryset = m.Evento.objects.all()
    serializer_class = serializador(m.Evento)
    solo_propietario = True


class CotizacionInput(serializers.Serializer):
    precio = serializers.UUIDField()
    alumnos = serializers.IntegerField(min_value=1,max_value=1000000,default=1)
    contrato = serializers.UUIDField(required=False)

    def to_internal_value(self,data):
        if isinstance(data, Mapping) and set(data) - set(self.fields): raise ValidationError({'non_field_errors':['Campos de compra desconocidos; importe calculado por servidor.']})
        return super().to_internal_value(data)


class CheckoutInput(CotizacionInput):
    importe_esperado = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    moneda_esperada = serializers.CharField(max_length=3, required=False)

    def validate(self, attrs):
        if ('importe_esperado' in attrs) != ('moneda_esperada' in attrs):
            raise ValidationError('Envía importe y moneda juntos.')
        return attrs


@extend_schema(request=CotizacionInput, responses=inline_serializer(name='CotizacionComercial', fields={
    'base': serializers.DecimalField(max_digits=12, decimal_places=2),
    'cuota_alumnos': serializers.DecimalField(max_digits=12, decimal_places=2),
    'total': serializers.DecimalField(max_digits=12, decimal_places=2),
    'moneda': serializers.CharField(),
}))
@api_view(['POST'])
def cotizacion(request):
    input_data = CotizacionInput(data=request.data)
    input_data.is_valid(raise_exception=True)
    datos = input_data.validated_data
    precio, _, importe = s.cotizar(tenant_actual(request), datos['precio'], datos['alumnos'], datos.get('contrato'))
    return Response(dict(base=str(precio.importe), cuota_alumnos=str(importe - precio.importe),
                         total=str(importe), moneda=precio.moneda))


@extend_schema(request=CheckoutInput, responses=inline_serializer(name='CheckoutResultado',fields={
    'orden':serializers.UUIDField(),'proveedor':serializers.CharField(),'url':serializers.URLField(allow_null=True),'estado':serializers.CharField()}))
@api_view(['POST'])
def checkout(request):
    datos = CheckoutInput(data=request.data); datos.is_valid(raise_exception=True)
    clave = request.headers.get('Idempotency-Key','')
    if not re.fullmatch(r'[A-Za-z0-9_-]{8,100}',clave): raise ValidationError('Idempotency-Key requerido (8-100 caracteres).')
    orden = s.checkout(tenant_actual(request),datos.validated_data['precio'],datos.validated_data['alumnos'],datos.validated_data.get('contrato'), clave,
                       datos.validated_data.get('importe_esperado'), datos.validated_data.get('moneda_esperada'))
    return Response(dict(orden=str(orden.id),proveedor=orden.proveedor,url=orden.url or None,estado=orden.estado),status=201)


@extend_schema(responses=inline_serializer(name='AccesoComercial',fields={
    'activo':serializers.BooleanField(),'funcionalidades':serializers.DictField(),'max_alumnos':serializers.IntegerField(),'max_planteles':serializers.IntegerField()}))
@api_view(['GET'])
def acceso(request): return Response(s.acceso(tenant_actual(request)))


class DemoInput(serializers.Serializer):
    orden = serializers.UUIDField()
    resultado = serializers.ChoiceField(choices=['paid','failed','pending'])
    referencia = serializers.RegexField(r'^demo_[A-Za-z0-9_-]{8,150}$')


class OrdenDemoPendienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Orden
        fields = ['id', 'tenant', 'condiciones', 'importe', 'moneda']


@extend_schema(responses=OrdenDemoPendienteSerializer(many=True))
@api_view(['GET'])
def ordenes_demo_pendientes(request):
    if not propietario(request.user):
        raise PermissionDenied()
    ordenes = m.Orden.objects.none()
    if settings.COMMERCIAL_PROVIDER == 'DEMO':
        ordenes = m.Orden.objects.filter(proveedor='DEMO', estado='pending').order_by('-creado')[:30]
    return Response(OrdenDemoPendienteSerializer(ordenes, many=True).data)


@extend_schema(request=DemoInput,responses=inline_serializer(name='DemoConfirmacion',fields={'transaccion':serializers.UUIDField(),'proveedor':serializers.CharField()}))
@api_view(['POST'])
def demo(request):
    if not propietario(request.user) or settings.COMMERCIAL_PROVIDER != 'DEMO': raise PermissionDenied()
    datos = DemoInput(data=request.data); datos.is_valid(raise_exception=True)
    datos = datos.validated_data
    from django.shortcuts import get_object_or_404
    with transaction.atomic():
        orden = get_object_or_404(m.Orden.objects.select_for_update(), pk=datos['orden'], proveedor='DEMO')
        if orden.estado == 'paid':
            tx = m.Transaccion.objects.filter(orden=orden, proveedor='DEMO', referencia=datos['referencia'],
                                              estado=datos['resultado']).first()
            if tx is None:
                raise ValidationError('La orden DEMO ya está pagada.')
        else:
            fin = timezone.now() + timedelta(days=30 if orden.condiciones['modalidad'] in ('monthly', 'hybrid')
                                             else orden.condiciones['dias'])
            tx = s.confirmar(orden.id, datos['referencia'], datos['resultado'], orden.importe, orden.moneda,
                             'DEMO', fin=fin, suscripcion='demo_sub_' + str(orden.id))
    return Response({'transaccion':str(tx.id),'proveedor':'DEMO'})


@extend_schema(responses=inline_serializer(name='IngresosComerciales',many=True,fields={'proveedor':serializers.CharField(),'moneda':serializers.CharField(),'total':serializers.DecimalField(max_digits=20,decimal_places=2)}))
@api_view(['GET'])
def ingresos(request):
    if not propietario(request.user): raise PermissionDenied()
    filas = list(m.Transaccion.objects.filter(estado='paid').values('proveedor','moneda').annotate(total=Sum('importe')))
    for fila in filas: fila['total'] = str(fila['total'])
    return Response(filas)


@extend_schema(request={'application/json':{'type':'object','additionalProperties':True}},responses=inline_serializer(name='WebhookRecibido',fields={'received':serializers.BooleanField()}),auth=[])
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def webhook(request):
    stripe = s.stripe_api()
    if not settings.STRIPE_WEBHOOK_SECRET: raise s.ProveedorNoDisponible()
    raw = request.body
    try:
        event = stripe.Webhook.construct_event(raw,request.headers.get('Stripe-Signature',''),settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError,stripe.SignatureVerificationError) as exc:
        raise ValidationError('Firma webhook inválida.') from exc
    if event.get('livemode'): raise ValidationError('Solo se permiten eventos sandbox.')
    digest = hashlib.sha256(raw).hexdigest()
    with transaction.atomic():
        registro, _ = m.Evento.objects.get_or_create(referencia=event.id,defaults={'tipo':event.type,'hash':digest})
        registro = m.Evento.objects.select_for_update().get(pk=registro.pk)
        if registro.hash != digest: raise ValidationError('Evento incompatible.')
        if registro.resultado == 'received':
            try: registro.resultado = s.procesar_stripe(event)
            except stripe.StripeError as exc: raise s.ProveedorNoDisponible() from exc
            registro.save(update_fields=['resultado'])
    return Response({'received':True})
