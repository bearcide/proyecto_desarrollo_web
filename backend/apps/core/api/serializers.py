from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.models import Alumno, Nodo, NodoEstadistico, PlanEstudios, Prerrequisito, Tenant, MembresiaTenant


def _tenant_del_contexto(context):
    identidad = context.get('identidad')
    return identidad.tenant if identidad else None


class MatriculaTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Login con **matrícula** (número de cuenta) + contraseña.

    Hereda de TokenObtainPairSerializer (SimpleJWT) pero acepta el campo
    `matricula` en lugar de `username`, y autentica contra el usuario cuyo
    username sea la matrícula del alumno.
    """

    matricula = serializers.CharField(write_only=True, required=True, help_text='Matrícula del alumno.')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El DTO usa `matricula`; el campo heredado de SimpleJWT (`username`) pasa a opcional.
        self.fields['username'].required = False
        self.fields['username'].write_only = True

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get('request'),
            username=attrs.get('matricula') or attrs.get('username'),
            password=attrs.get('password'),
        )
        if user is None or not user.is_active:
            raise AuthenticationFailed('No se pudo iniciar sesión con esas credenciales.')
        refresh = RefreshToken.for_user(user)
        data = {'refresh': str(refresh), 'access': str(refresh.access_token)}
        return data


class TenantPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """FK que solo acepta objetos de la escuela del usuario.

    Evita que un cliente enlace datos propios con IDs de otra escuela.
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        tenant = _tenant_del_contexto(self.context)
        if tenant is None:
            return queryset.none()
        return queryset.filter(tenant=tenant)


class EscrituraEstrictaMixin:
    def to_internal_value(self, data):
        if hasattr(data, 'keys'):
            invalidos = set(data) - {name for name, field in self.fields.items() if not field.read_only}
            if invalidos:
                raise serializers.ValidationError({name: 'Campo no editable o desconocido.' for name in sorted(invalidos)})
        return super().to_internal_value(data)


class TenantScopedSerializer(EscrituraEstrictaMixin, serializers.ModelSerializer):
    """Base: `tenant` es de solo lectura y valida unicidad dentro de la escuela.

    unique_per_tenant: tuplas de campos que deben ser únicos por escuela. Se valida aquí
    para responder 400 con detalle en vez de un 500 por IntegrityError.
    """

    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    unique_per_tenant = ()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        tenant = _tenant_del_contexto(self.context)
        for campos in self.unique_per_tenant:
            self._validar_unicidad(campos, attrs, tenant)
        return attrs

    def _validar_unicidad(self, campos, attrs, tenant):
        """Valida que el valor sea único dentro del tenant (excluyendo el propio registro al editar)."""
        filtro = {}
        for campo in campos:
            if campo in attrs:
                filtro[campo] = attrs[campo]
            elif self.instance is not None:
                filtro[campo] = getattr(self.instance, campo)
            else:
                break
        else:
            existentes = self.Meta.model.objects.filter(tenant=tenant, **filtro)
            if self.instance is not None:
                existentes = existentes.exclude(pk=self.instance.pk)
            if existentes.exists():
                raise serializers.ValidationError(
                    {campos[-1]: 'Ya existe un registro con este valor en tu escuela.'}
                )


class TenantSerializer(EscrituraEstrictaMixin, serializers.ModelSerializer):
    """El cliente solo puede editar el nombre comercial.

    plan_suscripcion y estado los gestiona la plataforma (facturación), no la escuela.
    """

    class Meta:
        model = Tenant
        fields = ['id', 'nombre_comercial', 'plan_suscripcion', 'estado', 'created_at', 'updated_at']
        read_only_fields = ['id', 'plan_suscripcion', 'estado', 'created_at', 'updated_at']


class PlanEstudiosSerializer(TenantScopedSerializer):
    unique_per_tenant = (('nombre',),)

    class Meta:
        model = PlanEstudios
        fields = ['id', 'tenant', 'nombre', 'descripcion', 'activo', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class NodoSerializer(TenantScopedSerializer):
    plan_estudios = TenantPrimaryKeyRelatedField(queryset=PlanEstudios.objects.all())
    # Solo lectura: las aristas se gestionan en /prerrequisitos/ (con detección de ciclos).
    prerrequisitos = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    cupo = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    profesor = serializers.CharField(required=False, allow_blank=True, max_length=150)
    horarios = serializers.JSONField(required=False)
    unique_per_tenant = (('clave',),)  # La clave es única en toda la escuela.

    class Meta:
        model = Nodo
        fields = [
            'id', 'tenant', 'plan_estudios', 'clave', 'nombre', 'creditos', 'semestre',
            'prerrequisitos', 'cupo', 'profesor', 'horarios', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        plan = attrs.get('plan_estudios')
        if self.instance and plan and plan.pk != self.instance.plan_estudios_id:
            if self.instance.aristas_prerrequisito.exists() or self.instance.aristas_dependientes.exists():
                raise serializers.ValidationError({'plan_estudios': 'No se puede cambiar el plan de una materia con prerrequisitos relacionados.'})
        return attrs


class PrerrequisitoSerializer(TenantScopedSerializer):
    """Solo valida la forma de la entrada; las reglas del grafo viven en services/."""

    nodo = TenantPrimaryKeyRelatedField(queryset=Nodo.objects.all())
    prerrequisito = TenantPrimaryKeyRelatedField(queryset=Nodo.objects.all())

    class Meta:
        model = Prerrequisito
        fields = ['id', 'tenant', 'nodo', 'prerrequisito', 'created_at']
        read_only_fields = ['id', 'created_at']


class NodoEstadisticoSerializer(TenantScopedSerializer):
    nodo = TenantPrimaryKeyRelatedField(queryset=Nodo.objects.all())
    unique_per_tenant = (('nodo',),)

    class Meta:
        model = NodoEstadistico
        fields = [
            'id', 'tenant', 'nodo', 'alumnos_inscritos', 'alumnos_pasados',
            'promedio_acumulado', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AlumnoSerializer(TenantScopedSerializer):
    plan_estudios = TenantPrimaryKeyRelatedField(queryset=PlanEstudios.objects.all())
    materias_aprobadas_ids = serializers.JSONField(
        required=False,
        help_text='IDs de materias que el alumno ya aprobó (para validar prerrequisitos).',
    )
    numero_inscripcion = serializers.CharField(
        required=False, allow_blank=True, max_length=32,
    )
    ventana_inicio = serializers.DateTimeField(required=False, allow_null=True)
    ventana_texto = serializers.CharField(
        required=False, allow_blank=True, max_length=255,
    )

    class Meta:
        model = Alumno
        fields = [
            'id', 'tenant', 'plan_estudios', 'nombre', 'apellido_paterno', 'apellido_materno',
            'numero_de_cuenta', 'domicilio', 'edad', 'semestre', 'materias_pasadas',
            'materias_cursadas', 'creditos', 'promedio_acumulado', 'indicador_escolar',
            'activo', 'materias_aprobadas_ids', 'numero_inscripcion', 'ventana_inicio', 'ventana_texto',
            'created_at', 'updated_at',
        ]
        # numero_de_cuenta es editable=False en el modelo: DRF lo expone como solo lectura.
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        ids = attrs.get('materias_aprobadas_ids')
        if ids is not None:
            if not isinstance(ids, list) or any(type(pk) is not int or pk <= 0 for pk in ids):
                raise serializers.ValidationError({'materias_aprobadas_ids': 'Se requiere una lista de identificadores enteros positivos.'})
            tenant = _tenant_del_contexto(self.context)
            if Nodo.objects.filter(tenant=tenant, pk__in=set(ids)).count() != len(set(ids)):
                raise serializers.ValidationError({'materias_aprobadas_ids': 'Referencia académica inválida.'})
        return attrs


class AlumnoPerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alumno
        fields = [
            'id', 'tenant', 'plan_estudios', 'numero_de_cuenta', 'nombre',
            'apellido_paterno', 'apellido_materno', 'semestre', 'materias_pasadas',
            'materias_cursadas', 'creditos', 'promedio_acumulado', 'indicador_escolar',
            'materias_aprobadas_ids', 'numero_inscripcion', 'ventana_inicio', 'ventana_texto',
        ]
        read_only_fields = fields


class MembresiaPerfilSerializer(serializers.ModelSerializer):
    nombre_escuela = serializers.CharField(source='tenant.nombre_comercial', read_only=True)
    estado_escuela = serializers.CharField(source='tenant.estado', read_only=True)

    class Meta:
        model = MembresiaTenant
        fields = ['tenant', 'nombre_escuela', 'estado_escuela', 'activo', 'es_alumno', 'es_administrador']
        read_only_fields = fields


class InvalidParamSerializer(serializers.Serializer):
    name = serializers.CharField()
    reason = serializers.CharField()


class ProblemDetailsSerializer(serializers.Serializer):
    type = serializers.CharField()
    title = serializers.CharField()
    status = serializers.IntegerField()
    detail = serializers.CharField()
    instance = serializers.CharField()
    code = serializers.CharField()
    invalid_params = InvalidParamSerializer(many=True, required=False)
