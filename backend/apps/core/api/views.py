from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter

from apps.core.models import Alumno, Nodo, NodoEstadistico, PlanEstudios, Prerrequisito, Tenant
from apps.core.services.errors import ReglaDeNegocioError
from apps.core.services.prerrequisitos import crear_prerrequisito

from .mixins import TenantScopedMixin
from .serializers import (
    AlumnoSerializer,
    NodoEstadisticoSerializer,
    NodoSerializer,
    PlanEstudiosSerializer,
    PrerrequisitoSerializer,
    TenantSerializer,
)


def _filtrar_por_id(queryset, request, parametro, campo):
    """Filtra por ?parametro=<id numérico>; ignora valores no numéricos."""
    valor = request.query_params.get(parametro)
    if valor and valor.isdigit():
        return queryset.filter(**{campo: int(valor)})
    return queryset


class TenantViewSet(
    TenantScopedMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """La escuela del usuario. Sin crear ni borrar: el alta/baja es de la plataforma."""

    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    tenant_lookup = 'pk'


class PlanEstudiosViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = PlanEstudios.objects.all()
    serializer_class = PlanEstudiosSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nombre']
    ordering_fields = ['nombre', 'created_at']


class NodoViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = Nodo.objects.select_related('plan_estudios').prefetch_related('prerrequisitos')
    serializer_class = NodoSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['clave', 'nombre']
    ordering_fields = ['clave', 'nombre', 'semestre', 'creditos', 'created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        return _filtrar_por_id(queryset, self.request, 'plan_estudios', 'plan_estudios_id')


class PrerrequisitoViewSet(
    TenantScopedMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Aristas del grafo. Sin PUT/PATCH: cambiar una arista es borrarla y crear otra."""

    queryset = Prerrequisito.objects.select_related('nodo', 'prerrequisito')
    serializer_class = PrerrequisitoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        return _filtrar_por_id(queryset, self.request, 'nodo', 'nodo_id')

    def perform_create(self, serializer):
        try:
            # La lógica (mismo plan, duplicados, ciclos) vive en la capa de servicios.
            serializer.instance = crear_prerrequisito(
                tenant=self.get_tenant(), **serializer.validated_data,
            )
        except ReglaDeNegocioError as exc:
            raise ValidationError({'detail': str(exc)})


class NodoEstadisticoViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = NodoEstadistico.objects.select_related('nodo')
    serializer_class = NodoEstadisticoSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['alumnos_inscritos', 'alumnos_pasados', 'promedio_acumulado']

    def get_queryset(self):
        queryset = super().get_queryset()
        return _filtrar_por_id(queryset, self.request, 'nodo', 'nodo_id')


class AlumnoViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = Alumno.objects.select_related('plan_estudios')
    serializer_class = AlumnoSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['numero_de_cuenta', 'nombre', 'apellido_paterno', 'apellido_materno']
    ordering_fields = ['apellido_paterno', 'nombre', 'numero_de_cuenta', 'semestre', 'created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        return _filtrar_por_id(queryset, self.request, 'plan_estudios', 'plan_estudios_id')
