from rest_framework.routers import DefaultRouter

from .views import (
    AlumnoViewSet,
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

urlpatterns = router.urls
