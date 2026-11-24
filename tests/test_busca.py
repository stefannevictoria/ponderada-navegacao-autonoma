import unittest

from navegacao.busca import bfs, movimentos_da_rota


class BuscaTests(unittest.TestCase):
    def test_menor_rota_com_desvio_e_ciclos(self):
        mapa = [list('fffff'), list('fbbbf'), list('fffff')]
        rota = bfs(mapa, (0, 2), (2, 2))
        self.assertEqual(len(rota) - 1, 6)
        self.assertEqual(rota[0], (0, 2))
        self.assertEqual(rota[-1], (2, 2))
        for l, c in rota:
            self.assertNotEqual(mapa[l][c], 'b')
        self.assertEqual(len(movimentos_da_rota(rota)), 6)

    def test_alvo_inacessivel(self):
        self.assertIsNone(bfs([list('fbf')], (0, 0), (0, 2)))

    def test_inicio_igual_alvo(self):
        self.assertEqual(bfs([['f']], (0, 0), (0, 0)), [(0, 0)])

    def test_movimentos_nas_quatro_direcoes(self):
        self.assertEqual(movimentos_da_rota([(1, 1), (0, 1), (1, 1), (1, 0), (1, 1)]),
                         ['up', 'down', 'left', 'right'])

    def test_rejeita_diagonal(self):
        with self.assertRaises(ValueError):
            movimentos_da_rota([(0, 0), (1, 1)])

    def test_rejeita_mapa_irregular_e_posicoes_invalidas(self):
        for mapa, inicio, alvo in [([['f'], ['f', 'f']], (0, 0), (1, 0)),
                                  ([['b', 'f']], (0, 0), (0, 1)),
                                  ([['f']], (0, 0), (-1, 0))]:
            with self.assertRaises(ValueError):
                bfs(mapa, inicio, alvo)


if __name__ == '__main__':
    unittest.main()
