"""Verifica a confirmação de movimentos sem conectar a um simulador."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

try:
    from navegacao.parte1 import Navegador, RespostaEsgotada
except ImportError as erro:
    raise unittest.SkipTest('Carregue scripts/ambiente.bash para os testes do cliente ROS.') from erro


class ConfirmacaoTests(unittest.TestCase):
    def cliente_sem_resposta(self, mapa):
        return SimpleNamespace(movimento_client=object(),
                               chamar=Mock(side_effect=RespostaEsgotada('sem resposta')),
                               obter_mapa=Mock(return_value=mapa))

    def test_confirma_movimento_sem_reenviar_comando(self):
        cliente = self.cliente_sem_resposta([list('frt')])
        self.assertEqual(Navegador.mover(cliente, 'right', (0, 1), (0, 2)), 'mapa')
        self.assertEqual(cliente.chamar.call_count, 1)

    def test_interrompe_se_movimento_nao_foi_confirmado(self):
        cliente = self.cliente_sem_resposta([list('rft')])
        with self.assertRaises(RuntimeError):
            Navegador.mover(cliente, 'right', (0, 1), (0, 2))
        self.assertEqual(cliente.chamar.call_count, 1)

    def test_confirma_chegada_ao_alvo_sem_simbolo_t(self):
        cliente = self.cliente_sem_resposta([list('ffr')])
        self.assertEqual(Navegador.mover(cliente, 'right', (0, 2), (0, 2)), 'mapa')

    def test_rejeita_posicao_incorreta_mesmo_com_resposta_de_sucesso(self):
        cliente = SimpleNamespace(movimento_client=object(), chamar=Mock(return_value=
            SimpleNamespace(success=True, robot_pos=(0, 0), target_pos=(0, 2))))
        with self.assertRaises(RuntimeError):
            Navegador.mover(cliente, 'right', (0, 1), (0, 2))
