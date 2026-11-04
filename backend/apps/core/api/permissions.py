from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.core.services.identidad import obtener_alumno, resolver_identidad


class TieneTenant(BasePermission):
    """Membresía verificada y capacidad explícita; sin bypass global."""

    message = 'No tienes permiso para esta operación.'

    def has_permission(self, request, view):
        identidad = resolver_identidad(request)
        if request.method not in view.allowed_methods:
            return True  # DRF responde 405 sin ejecutar una operación.
        if getattr(view, 'action', None) == 'me':
            obtener_alumno(identidad)
            return request.method in SAFE_METHODS
        if identidad.membresia.es_administrador:
            return True
        if not identidad.membresia.es_alumno:
            return False
        obtener_alumno(identidad)
        return request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        identidad = resolver_identidad(request)
        tenant_id = obj.pk if view.tenant_lookup == 'pk' else obj.tenant_id
        if tenant_id != identidad.tenant.pk:
            return False
        if identidad.membresia.es_administrador:
            return True
        if getattr(view, 'alumnos_por_propietario', False):
            return obj.pk == obtener_alumno(identidad).pk
        return request.method in SAFE_METHODS
