from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import TokenRefreshView
from apps.core.api.views import MatriculaTokenObtainPairView

urlpatterns = [
    path('admin/', admin.site.urls),

    # La API vive bajo /api/v1/
    path('api/v1/', include('apps.core.api.urls')),

    # Documentación interactiva (OpenAPI 3 / Swagger UI)
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api-docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui-alt'),
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Autenticación JWT (login con matrícula + contraseña)
    path('api/v1/token/', MatriculaTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
