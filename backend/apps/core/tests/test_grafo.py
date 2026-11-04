from unittest import TestCase

from apps.core.services.grafo import hay_ciclo_al_agregar


class HayCicloAlAgregarTests(TestCase):
    def test_autoreferencia_es_ciclo(self):
        self.assertTrue(hay_ciclo_al_agregar([], 1, 1))

    def test_grafo_vacio_no_hay_ciclo(self):
        self.assertFalse(hay_ciclo_al_agregar([], 1, 2))

    def test_ciclo_directo(self):
        # 1 requiere 2; agregar «2 requiere 1» cierra el ciclo.
        self.assertTrue(hay_ciclo_al_agregar([(1, 2)], 2, 1))

    def test_ciclo_transitivo(self):
        # 1→2→3 (1 requiere 2, 2 requiere 3); agregar «3 requiere 1» cierra el ciclo.
        self.assertTrue(hay_ciclo_al_agregar([(1, 2), (2, 3)], 3, 1))

    def test_diamante_no_es_ciclo(self):
        # 1 requiere 2 y 3; 2 y 3 requieren 4; agregar «1 requiere 4» es válido.
        aristas = [(1, 2), (1, 3), (2, 4), (3, 4)]
        self.assertFalse(hay_ciclo_al_agregar(aristas, 1, 4))

    def test_grafos_disjuntos(self):
        self.assertFalse(hay_ciclo_al_agregar([(1, 2), (3, 4)], 4, 5))

    def test_mismo_sentido_repetido_no_es_ciclo(self):
        self.assertFalse(hay_ciclo_al_agregar([(1, 2), (2, 3)], 1, 3))
