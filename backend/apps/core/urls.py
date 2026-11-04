"""Rutas de la app core. Se montan en /api/v1/ desde config/urls.py."""
from django.urls import include, path

app_name = 'core'

urlpatterns = [
    path('', include('apps.core.api.urls')),
]
