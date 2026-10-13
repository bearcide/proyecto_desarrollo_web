from rest_framework import serializers

from apps.core.models import Alumno, Nodo, NodoEstadistico, PlanEstudios, Prerrequisito, Tenant


def _tenant_del_contexto(context):
    request = context.get('request')
    return getattr(getattr(request, 'user', None), 'tenant', None)


class TenantPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """FK que solo acepta objetos de la escuela del usuario.

    Evita que un cliente enlace datos propios con IDs de otra escuela.
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        tenant = _tenant_del_contexto(self.context)
        if queryset is None or tenant is None:
            return queryset.none() if queryset is not None else queryset
        return queryset.filter(tenant=tenant)


class TenantScopedSerializer(serializers.ModelSerializer):
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
        return attrs


class TenantSerializer(serializers.ModelSerializer):
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
    unique_per_tenant = (('clave',),)  # La clave es única en toda la escuela.

    class Meta:
        model = Nodo
        fields = [
            'id', 'tenant', 'plan_estudios', 'clave', 'nombre', 'creditos', 'semestre',
            'prerrequisitos', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


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

    class Meta:
        model = Alumno
        fields = [
            'id', 'tenant', 'plan_estudios', 'nombre', 'apellido_paterno', 'apellido_materno',
            'numero_de_cuenta', 'domicilio', 'edad', 'semestre', 'materias_pasadas',
            'materias_cursadas', 'creditos', 'promedio_acumulado', 'indicador_escolar',
            'activo', 'created_at', 'updated_at',
        ]
        # numero_de_cuenta es editable=False en el modelo: DRF lo expone como solo lectura.
        read_only_fields = ['id', 'created_at', 'updated_at']
