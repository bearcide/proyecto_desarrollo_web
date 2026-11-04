"""Identidad escolar por petición; ninguna autoridad proviene de un header."""
from dataclasses import dataclass
from uuid import UUID

from apps.core.models import Alumno, MembresiaTenant, Tenant


class ErrorIdentidad(Exception):
    def __init__(self, code, detail, status=403):
        self.code, self.detail, self.status = code, detail, status
        super().__init__(detail)


@dataclass(frozen=True)
class Identidad:
    user: object
    membresia: object
    tenant: object


def resolver_identidad(request):
    if hasattr(request, '_identidad_escolar'):
        return request._identidad_escolar
    user = request.user
    if not user or not user.is_authenticated or not user.is_active:
        raise ErrorIdentidad('authentication_failed', 'Autenticación requerida.', 401)
    membresias = MembresiaTenant.objects.select_related('tenant').filter(user=user, activo=True)
    seleccionado = request.headers.get('X-Tenant-ID')
    if seleccionado is not None:
        try:
            tenant_id = UUID(seleccionado)
        except (ValueError, TypeError, AttributeError):
            raise ErrorIdentidad('invalid_tenant', 'Identificador de escuela inválido.', 400)
        membresia = membresias.filter(tenant_id=tenant_id).first()
        if membresia is None:
            raise ErrorIdentidad('tenant_access_denied', 'No tienes acceso a esta escuela.')
    else:
        opciones = list(membresias[:2])
        if not opciones:
            raise ErrorIdentidad('tenant_access_denied', 'No tienes acceso a esta escuela.')
        if len(opciones) > 1:
            raise ErrorIdentidad('tenant_required', 'Selecciona una escuela asociada a tu usuario.', 400)
        membresia = opciones[0]
    if membresia.tenant.estado != Tenant.Estado.ACTIVO:
        raise ErrorIdentidad('tenant_unavailable', 'La escuela no está disponible.')
    identidad = Identidad(user, membresia, membresia.tenant)
    request._identidad_escolar = identidad
    return identidad


def obtener_alumno(identidad):
    if not identidad.membresia.es_alumno:
        raise ErrorIdentidad('permission_denied', 'Se requiere capacidad de alumno.')
    perfiles = list(Alumno.objects.filter(user=identidad.user, tenant=identidad.tenant)[:2])
    if not perfiles:
        raise ErrorIdentidad('alumno_not_found', 'Perfil académico no encontrado.', 404)
    if len(perfiles) > 1:
        raise ErrorIdentidad('ambiguous_alumno_identity', 'La identidad académica requiere revisión.', 409)
    if not perfiles[0].activo:
        raise ErrorIdentidad('alumno_inactive', 'El perfil académico está inactivo.')
    return perfiles[0]
