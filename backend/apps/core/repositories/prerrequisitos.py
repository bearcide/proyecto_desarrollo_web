"""Acceso a datos de prerrequisitos. Único lugar de esta funcionalidad que toca el ORM."""
from apps.core.models import PlanEstudios, Prerrequisito


def bloquear_plan(plan_id):
    """Bloquea la fila del plan hasta el fin de la transacción: serializa los cambios
    al grafo de un mismo plan y evita que dos altas simultáneas formen un ciclo."""
    return PlanEstudios.objects.select_for_update().get(pk=plan_id)


def existe(tenant, nodo_id, prerrequisito_id):
    return Prerrequisito.objects.filter(
        tenant=tenant, nodo_id=nodo_id, prerrequisito_id=prerrequisito_id,
    ).exists()


def aristas_del_plan(tenant, plan_id):
    """Todas las aristas (nodo_id, prerrequisito_id) del plan, en una sola consulta."""
    return list(
        Prerrequisito.objects.filter(tenant=tenant, nodo__plan_estudios_id=plan_id)
        .values_list('nodo_id', 'prerrequisito_id')
    )


def crear(tenant, nodo, prerrequisito):
    return Prerrequisito.objects.create(tenant=tenant, nodo=nodo, prerrequisito=prerrequisito)
