from rest_framework.routers import DefaultRouter

from .views import (
    AlumnoViewSet,
    MembresiaViewSet,
    NodoEstadisticoViewSet,
    NodoViewSet,
    PlanEstudiosViewSet,
    PrerrequisitoViewSet,
    TenantViewSet,
)

router = DefaultRouter()
router.register('tenants', TenantViewSet, basename='tenant')
router.register('planes-estudios', PlanEstudiosViewSet, basename='plan-estudios')
router.register('nodos', NodoViewSet, basename='nodo')
router.register('prerrequisitos', PrerrequisitoViewSet, basename='prerrequisito')
router.register('estadisticas-nodos', NodoEstadisticoViewSet, basename='nodo-estadistico')
router.register('alumnos', AlumnoViewSet, basename='alumno')

router.register('membresias', MembresiaViewSet, basename='membresia')

from django.urls import path
from .demo import (ImportacionView, GruposView, EstadisticasView, GenerarView,
    EjecucionesView, ResultadoView, PublicarView, CsvResultadosView, HorarioView)

urlpatterns = [
    path('demo/importaciones/validar/', ImportacionView.as_view(), {'accion':'validar'}),
    path('demo/importaciones/confirmar/', ImportacionView.as_view(), {'accion':'confirmar'}),
    path('demo/grupos/', GruposView.as_view()),
    path('demo/estadisticas/', EstadisticasView.as_view()),
    path('demo/asignaciones/generar/', GenerarView.as_view()),
    path('demo/asignaciones/', EjecucionesView.as_view()),
    path('demo/asignaciones/<int:pk>/', ResultadoView.as_view()),
    path('demo/asignaciones/<int:pk>/publicar/', PublicarView.as_view()),
    path('demo/asignaciones/<int:pk>/csv/', CsvResultadosView.as_view()),
    path('demo/horario/me/', HorarioView.as_view()),
] + router.urls
