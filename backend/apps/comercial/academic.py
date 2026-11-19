"""Política académica: identidad resuelta antes de comprobar la licencia."""
from apps.core.models import Alumno
from .models import Orden
from .services import exigir_capacidad


def exige_licencia(tenant):
    # Una primera orden termina la transición, incluso si aún no se ha pagado.
    return tenant.licencia_requerida or Orden.objects.filter(tenant=tenant).exists()


def exigir_modulo(tenant, funcionalidad, **limites):
    if exige_licencia(tenant):
        return exigir_capacidad(tenant, funcionalidad=funcionalidad, planteles=1, **limites)


def exigir_alumnos(tenant, adicionales=0):
    return exigir_modulo(tenant, 'alumnos',
                         alumnos=Alumno.objects.filter(tenant=tenant).count() + adicionales)
