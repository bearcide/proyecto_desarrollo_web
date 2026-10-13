"""Enrutador raíz. La API vive bajo /api/v1/ (prefijo provisional, sujeto al contrato de la API)."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.core.urls')),
]
