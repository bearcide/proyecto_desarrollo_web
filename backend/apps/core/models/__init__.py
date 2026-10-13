"""Entidades de la app core. Todas las tablas principales cuelgan de Tenant."""
from .alumno import Alumno
from .base import TimeStampedModel
from .nodo import Nodo, NodoEstadistico, Prerrequisito
from .plan_estudios import PlanEstudios
from .tenant import Tenant

__all__ = [
    'Alumno',
    'Nodo',
    'NodoEstadistico',
    'PlanEstudios',
    'Prerrequisito',
    'Tenant',
    'TimeStampedModel',
]
