"""Cliente ROS: obtém o mapa, planeja com BFS e executa a rota mínima."""

import argparse
import json
from pathlib import Path
import time

import rclpy
from rclpy.node import Node
from rclpy.executors import SingleThreadedExecutor
from cg_interfaces.srv import GetMap, MoveCmd

from .busca import bfs, localizar, movimentos_da_rota, validar_mapa


class RespostaEsgotada(RuntimeError):
    """O comando pode ter sido executado, mas não houve resposta a tempo."""


class Navegador(Node):
    def __init__(self):
        super().__init__('navegacao_parte1')
        self.processador = SingleThreadedExecutor()
        self.processador.add_node(self)
        self.mapa_client = self.create_client(GetMap, '/get_map')
        self.movimento_client = self.create_client(MoveCmd, '/move_command')

    def chamar(self, cliente, pedido):
        if not cliente.wait_for_service(timeout_sec=10):
            raise RuntimeError(f'Serviço {cliente.srv_name} indisponível. Abra o simulador.')
        futuro = cliente.call_async(pedido)
        self.processador.spin_until_future_complete(futuro, timeout_sec=10)
        if not futuro.done():
            futuro.cancel()
            raise RespostaEsgotada('O simulador não respondeu em 10 segundos.')
        return futuro.result()

    def obter_mapa(self):
        resposta = self.chamar(self.mapa_client, GetMap.Request())
        forma = list(resposta.occupancy_grid_shape)
        dados = list(resposta.occupancy_grid_flattened)
        if len(forma) != 2 or any(n <= 0 for n in forma) or len(dados) != forma[0] * forma[1]:
            raise ValueError('O simulador retornou dimensões incompatíveis com o mapa.')
        linhas, colunas = forma
        mapa = [dados[l * colunas:(l + 1) * colunas] for l in range(linhas)]
        validar_mapa(mapa)
        return mapa

    def mover(self, direcao, destino, alvo):
        pedido = MoveCmd.Request()
        pedido.direction = direcao
        try:
            resposta = self.chamar(self.movimento_client, pedido)
        except RespostaEsgotada:
            # Não repete o comando: ele pode ter sido executado pelo servidor.
            # Na parte 1 temos acesso ao mapa completo para confirmar a posição.
            mapa = self.obter_mapa()
            posicao = localizar(mapa, 'r')
            alvos = [(l, c) for l, linha in enumerate(mapa)
                     for c, celula in enumerate(linha) if celula == 't']
            alvo_correto = (not alvos if destino == alvo else alvos == [alvo])
            if posicao != destino or not alvo_correto:
                raise RuntimeError('Sem resposta e sem confirmação da posição esperada; execução interrompida.')
            print('Resposta de movimento ausente; posição confirmada pela leitura do mapa.', flush=True)
            return 'mapa'
        if not resposta.success:
            raise RuntimeError(f'O simulador recusou o movimento {direcao}.')
        if tuple(resposta.robot_pos) != destino:
            raise RuntimeError('A posição retornada difere da planejada. Reinicie sem teleoperação.')
        if tuple(resposta.target_pos) != alvo:
            raise RuntimeError('O alvo mudou durante a execução. Planeje novamente.')
        return 'servico'


def executar(args):
    no = Navegador()
    try:
        mapa = no.obter_mapa()
        inicio, alvo = localizar(mapa, 'r'), localizar(mapa, 't')
        print(f'Mapa: {len(mapa)} × {len(mapa[0])}. Robô: {inicio}. Alvo: {alvo}.', flush=True)
        rota = bfs(mapa, inicio, alvo)
        relatorio = {
            'algoritmo': 'BFS', 'criterio': 'menor número de movimentos de custo unitário',
            'mapa_inicial': mapa, 'inicio': inicio, 'alvo': alvo,
            'rota': rota, 'movimentos': [], 'passos_planejados': None,
            'passos_executados': 0, 'posicao_final': inicio,
            'status': 'sem_rota', 'confirmacoes_por_mapa': [],
        }
        if rota is None:
            print('O alvo é inacessível a partir da posição atual.', flush=True)
        else:
            movimentos = movimentos_da_rota(rota)
            relatorio.update(movimentos=movimentos, passos_planejados=len(movimentos), status='planejado')
            print(f'BFS: caminho mínimo com {len(movimentos)} movimentos.', flush=True)
            if not args.planejar:
                relatorio['status'] = 'em_execucao'
                try:
                    for i, (direcao, destino) in enumerate(zip(movimentos, rota[1:]), 1):
                        confirmacao = no.mover(direcao, destino, alvo)
                        if confirmacao == 'mapa':
                            relatorio['confirmacoes_por_mapa'].append(i)
                        relatorio.update(passos_executados=i, posicao_final=destino)
                        print(f'[{i}/{len(movimentos)}] {direcao} -> {destino}', flush=True)
                        time.sleep(args.intervalo)
                    relatorio['status'] = 'concluido'
                    print('Alvo alcançado; todos os movimentos foram confirmados pelo simulador.', flush=True)
                except (RuntimeError, KeyboardInterrupt) as erro:
                    relatorio.update(status='interrompido', erro=str(erro) or 'Interrompido pelo usuário')
                    salvar(args.saida, relatorio)
                    raise
        salvar(args.saida, relatorio)
        return 0 if rota is not None else 1
    finally:
        no.processador.shutdown()
        no.destroy_node()


def salvar(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Relatório salvo em: {caminho}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--planejar', action='store_true', help='Calcula a rota sem mover o robô.')
    parser.add_argument('--intervalo', type=float, default=0.15, help='Segundos entre movimentos.')
    parser.add_argument('--saida', type=Path, default=Path('resultados/parte1.json'))
    args = parser.parse_args()
    if args.intervalo < 0:
        parser.error('--intervalo deve ser maior ou igual a zero.')
    rclpy.init(args=[])
    try:
        return executar(args)
    except (RuntimeError, ValueError) as erro:
        print(f'Erro: {erro}')
        return 1
    except KeyboardInterrupt:
        print('Execução interrompida.')
        return 130
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    raise SystemExit(main())
