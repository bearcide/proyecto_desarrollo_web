"""Algoritmos puros sobre el grafo de prerrequisitos. Sin Django, sin base de datos."""
from collections import defaultdict


def hay_ciclo_al_agregar(aristas, nodo, prerrequisito):
    """¿Agregar «nodo requiere prerrequisito» crearía un ciclo?

    aristas: iterable de pares (nodo_id, prerrequisito_id) ya existentes, con el
    significado «nodo requiere prerrequisito». Se crea un ciclo si `nodo` ya es
    alcanzable desde `prerrequisito` siguiendo las aristas existentes.
    """
    if nodo == prerrequisito:
        return True
    requiere = defaultdict(list)
    for origen, destino in aristas:
        requiere[origen].append(destino)

    visitados = set()
    pila = [prerrequisito]
    while pila:
        actual = pila.pop()
        if actual == nodo:
            return True
        if actual in visitados:
            continue
        visitados.add(actual)
        pila.extend(requiere.get(actual, ()))
    return False
