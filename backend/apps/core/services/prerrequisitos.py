"""Reglas de negocio de los prerrequisitos. No conoce DRF ni request/response."""
from django.db import transaction

from apps.core.repositories import prerrequisitos as repo

from .errors import ReglaDeNegocioError
from .grafo import hay_ciclo_al_agregar


def crear_prerrequisito(*, tenant, nodo, prerrequisito):
    """Crea la arista «nodo requiere prerrequisito» validando las reglas del grafo."""
    if nodo.pk == prerrequisito.pk:
        raise ReglaDeNegocioError('Una materia no puede ser prerrequisito de sí misma.')
    if nodo.tenant_id != tenant.pk or prerrequisito.tenant_id != tenant.pk:
        raise ReglaDeNegocioError('Las materias deben pertenecer a tu escuela.')
    if nodo.plan_estudios_id != prerrequisito.plan_estudios_id:
        raise ReglaDeNegocioError('Las dos materias deben pertenecer al mismo plan de estudios.')

    with transaction.atomic():
        repo.bloquear_plan(nodo.plan_estudios_id)
        if repo.existe(tenant, nodo.pk, prerrequisito.pk):
            raise ReglaDeNegocioError('Ese prerrequisito ya existe.')
        aristas = repo.aristas_del_plan(tenant, nodo.plan_estudios_id)
        if hay_ciclo_al_agregar(aristas, nodo.pk, prerrequisito.pk):
            raise ReglaDeNegocioError(
                'Ese prerrequisito crearía un ciclo: las materias se requerirían entre sí.'
            )
        return repo.crear(tenant, nodo, prerrequisito)
