"""Enrutador raíz. La API vive bajo /api/v1/ (prefijo provisional, sujeto al contrato de la API)."""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.core.urls')),
    # Documentación interactiva (OpenAPI 3 / Swagger UI)
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api-docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui-alt'),
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
]
