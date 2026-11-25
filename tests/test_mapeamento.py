import random
import unittest

from navegacao.busca import DIRECOES, bfs, localizar, movimentos_da_rota
from navegacao.mapeamento import ExploracaoDFS, SENSORES
from navegacao.validacao import aprovada, comparar


class AmbienteLocal:
    """Apenas estes callbacks são entregues ao explorador; não há serviço de mapa."""
    def __init__(self, linhas):
        self.mapa = [list(linha) for linha in linhas]
        self.inicio = localizar(self.mapa, 'r')
        self.alvo = localizar(self.mapa, 't')
        self.posicao = self.inicio
        self.movimentos = 0

    def observar(self):
        l, c = self.posicao
        return {nome: 'f' if self.mapa[l + dl][c + dc] == 'r' else self.mapa[l + dl][c + dc]
                for nome, (dl, dc) in SENSORES.items()}

    def mover(self, nome, destino):
        dl, dc = DIRECOES[nome]
        nova = (self.posicao[0] + dl, self.posicao[1] + dc)
        if nova == self.alvo:
            raise AssertionError('O alvo foi acessado antes de encerrar o mapeamento.')
        if self.mapa[nova[0]][nova[1]] == 'b':
            raise AssertionError('Tentativa de atravessar uma parede.')
        if (nova[0] - self.inicio[0], nova[1] - self.inicio[1]) != destino:
            raise AssertionError('Coordenadas relativas incorretas.')
        self.posicao = nova
        self.movimentos += 1


def executar_local(linhas):
    ambiente = AmbienteLocal(linhas)
    exploracao = ExploracaoDFS()
    rota = exploracao.explorar(ambiente.observar, ambiente.mover)
    return ambiente, exploracao, rota


def relatorios(ambiente, exploracao, rota):
    matriz, canto = exploracao.mapa.exportar()
    referencia = {'mapa_inicial': ambiente.mapa, 'inicio': ambiente.inicio, 'alvo': ambiente.alvo}
    resultado = {'status': 'concluido', 'origem_absoluta': ambiente.inicio,
                 'rota_reproduzida': rota, 'mapa_descoberto': matriz, 'canto_relativo': canto,
                 'passos_rota_executados': len(rota) - 1,
                 'ultima_posicao_confirmada_relativa': rota[-1]}
    return referencia, resultado


class MapeamentoTests(unittest.TestCase):
    def test_ciclos_becos_retorno_e_mesma_rota(self):
        ambiente, exploracao, rota = executar_local([
            'bbbbbbbbb', 'brffbfffb', 'bfbfbfbfb', 'bfbffftfb',
            'bfffbbbfb', 'bfffffffb', 'bbbbbbbbb'])
        self.assertEqual(ambiente.posicao, ambiente.inicio)
        self.assertEqual(exploracao.trajeto[-1], (0, 0))
        self.assertEqual(ambiente.movimentos, 2 * (len(exploracao.visitadas) - 1))
        self.assertTrue(aprovada(comparar(*relatorios(ambiente, exploracao, rota))))
        self.assertEqual(len(movimentos_da_rota(rota)), len(rota) - 1)

    def test_regiao_atras_do_alvo_pode_ficar_desconhecida(self):
        ambiente, exploracao, rota = executar_local([
            'bbbbbbb', 'brftffb', 'bfbbbbb', 'bfffffb', 'bbbbbbb'])
        self.assertEqual(len(rota) - 1, 2)
        # A célula (1, 5) está atrás do alvo e não foi observada pelos sensores.
        self.assertNotIn((0, 4), exploracao.mapa.celulas)
        self.assertTrue(aprovada(comparar(*relatorios(ambiente, exploracao, rota))))

    def test_alvo_visivel_mas_inacessivel(self):
        _, exploracao, rota = executar_local(['bbbbb', 'brbfb', 'bbtbb', 'bbbbb'])
        self.assertIsNotNone(exploracao.mapa.alvo)
        self.assertIsNone(rota)

    def test_alvo_nao_observado(self):
        _, exploracao, rota = executar_local(['bbbbbbb', 'brbfftb', 'bbbbbbb'])
        self.assertIsNone(exploracao.mapa.alvo)
        self.assertIsNone(rota)

    def test_coordenadas_relativas_quando_inicio_nao_e_canto(self):
        ambiente, exploracao, rota = executar_local([
            'bbbbbbb', 'bfffffb', 'bftbfrb', 'bfffffb', 'bbbbbbb'])
        self.assertTrue(any(l < 0 or c < 0 for l, c in exploracao.mapa.celulas))
        self.assertTrue(aprovada(comparar(*relatorios(ambiente, exploracao, rota))))

    def test_comparacao_rejeita_mapa_incorreto(self):
        ambiente, exploracao, rota = executar_local(['bbbbb', 'brftb', 'bbbbb'])
        parte1, parte2 = relatorios(ambiente, exploracao, rota)
        parte2['mapa_descoberto'][0][0] = 'f'
        with self.assertRaises(ValueError):
            comparar(parte1, parte2)

    def test_comparacao_rejeita_inicio_diferente(self):
        ambiente, exploracao, rota = executar_local(['bbbbb', 'brftb', 'bbbbb'])
        parte1, parte2 = relatorios(ambiente, exploracao, rota)
        parte2['origem_absoluta'] = (3, 3)
        with self.assertRaises(ValueError):
            comparar(parte1, parte2)

    def test_50_mapas_aleatorios_reproduzem_bfs_do_mapa_completo(self):
        gerador = random.Random(24)
        for _ in range(50):
            matriz = [['b'] * 8 for _ in range(8)]
            for l in range(1, 7):
                for c in range(1, 7):
                    matriz[l][c] = 'b' if gerador.random() < 0.3 else 'f'
            matriz[1][1], matriz[6][6] = 'r', 't'
            ambiente, exploracao, rota = executar_local([''.join(linha) for linha in matriz])
            referencia = bfs(ambiente.mapa, ambiente.inicio, ambiente.alvo)
            absoluta = None if rota is None else [(l + 1, c + 1) for l, c in rota]
            self.assertEqual(absoluta, referencia)
            self.assertEqual(ambiente.posicao, ambiente.inicio)
