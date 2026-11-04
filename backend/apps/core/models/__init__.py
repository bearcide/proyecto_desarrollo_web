"""Entidades de la app core. Todas las tablas principales cuelgan de Tenant."""
from .alumno import Alumno
from .base import TimeStampedModel
from .membresia import MembresiaTenant
from .demo import Grupo, SolicitudMateria, EjecucionAsignacion, ResultadoAsignacion
from .nodo import Nodo, NodoEstadistico, Prerrequisito
from .plan_estudios import PlanEstudios
from .tenant import Tenant

__all__ = [
    'Alumno',
    'MembresiaTenant',
    'Grupo',
    'SolicitudMateria',
    'EjecucionAsignacion',
    'ResultadoAsignacion',
    'Nodo',
    'NodoEstadistico',
    'PlanEstudios',
    'Prerrequisito',
    'Tenant',
    'TimeStampedModel',
]
