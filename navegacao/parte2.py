"""Explora pelos sensores, retorna ao início e percorre a rota do mapa construído."""

import argparse
import json
from pathlib import Path
import time

import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from cg_interfaces.msg import RobotSensors
from cg_interfaces.srv import MoveCmd

from .busca import movimentos_da_rota
from .mapeamento import ExploracaoDFS, SENSORES


class RoboExplorador(Node):
    def __init__(self, intervalo):
        super().__init__('navegacao_parte2')
        self.processador = SingleThreadedExecutor()
        self.processador.add_node(self)
        self.cliente = self.create_client(MoveCmd, '/move_command')
        qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT,
                         durability=DurabilityPolicy.VOLATILE)
        self.inscricao = self.create_subscription(RobotSensors, '/culling_games/robot_sensors',
                                                 self.receber_sensores, qos)
        self.leituras = 0
        self.ultima_leitura = None
        self.posicao = (0, 0)
        self.origem_absoluta = None
        self.intervalo = intervalo

    def receber_sensores(self, mensagem):
        self.ultima_leitura = {nome: getattr(mensagem, nome) for nome in SENSORES}
        self.leituras += 1

    def observar(self):
        # A mensagem não traz pose nem timestamp. Com histórico de uma amostra,
        # descartamos leituras já pendentes e esperamos três novas entregas.
        minimo = self.leituras + 3
        limite = time.monotonic() + 10
        while self.leituras < minimo:
            restante = limite - time.monotonic()
            if restante <= 0:
                raise RuntimeError('Não chegaram novas leituras dos sensores em 10 segundos.')
            self.processador.spin_once(timeout_sec=min(restante, 0.1))
        return self.ultima_leitura.copy()

    def mover(self, direcao, destino):
        if not self.cliente.wait_for_service(timeout_sec=10):
            raise RuntimeError('Serviço de movimento indisponível. Abra o simulador.')
        pedido = MoveCmd.Request()
        pedido.direction = direcao
        futuro = self.cliente.call_async(pedido)
        self.processador.spin_until_future_complete(futuro, timeout_sec=10)
        if not futuro.done():
            futuro.cancel()
            # Sem mapa completo, não é seguro repetir nem presumir o movimento.
            raise RuntimeError('Sem resposta de movimento; reinicie o mapa antes de tentar novamente.')
        resposta = futuro.result()
        if not resposta.success:
            raise RuntimeError(f'O simulador recusou o movimento {direcao}.')
        absoluta = tuple(int(v) for v in resposta.robot_pos)
        if self.origem_absoluta is None:
            self.origem_absoluta = (absoluta[0] - destino[0], absoluta[1] - destino[1])
        esperada = (self.origem_absoluta[0] + destino[0], self.origem_absoluta[1] + destino[1])
        if absoluta != esperada:
            raise RuntimeError('Posição diferente da esperada. Não use teleoperação durante a exploração.')
        # target_pos não é usado: o alvo é descoberto exclusivamente pelos sensores.
        self.posicao = destino
        time.sleep(self.intervalo)


def executar(args):
    no = RoboExplorador(args.intervalo)
    exploracao = ExploracaoDFS()
    relatorio = {'status': 'explorando', 'metodo_mapeamento': 'DFS com sensores locais',
                 'algoritmo_rota': 'BFS', 'inicio_relativo': (0, 0),
                 'rota_reproduzida': None, 'passos_rota_planejados': None,
                 'passos_rota_executados': 0}
    codigo = 1

    def mover_exploracao(direcao, destino):
        no.mover(direcao, destino)
        passos = len(exploracao.trajeto)
        if passos % 25 == 0:
            print(f'Exploração: {passos} movimentos; posição relativa {destino}.', flush=True)

    try:
        print('Explorando somente com sensores. A origem relativa é (0, 0).', flush=True)
        rota = exploracao.explorar(no.observar, mover_exploracao)
        if no.posicao != (0, 0):
            raise RuntimeError('A exploração não retornou à origem.')
        if exploracao.mapa.alvo is None:
            relatorio['status'] = 'alvo_nao_observado'
            print('Exploração encerrada: o alvo não foi observado na região acessível.', flush=True)
        elif rota is None:
            relatorio['status'] = 'alvo_inacessivel'
            print('O alvo foi observado, mas não há rota conhecida até ele.', flush=True)
        else:
            movimentos = movimentos_da_rota(rota)
            relatorio.update(status='reproduzindo', rota_reproduzida=rota,
                             passos_rota_planejados=len(movimentos), movimentos_rota=movimentos)
            print(f'Mapeamento encerrado. De volta ao início; rota mínima com {len(movimentos)} movimentos.', flush=True)
            for i, (direcao, destino) in enumerate(zip(movimentos, rota[1:]), 1):
                no.mover(direcao, destino)
                relatorio['passos_rota_executados'] = i
                print(f'Rota [{i}/{len(movimentos)}]: {direcao} -> {destino}', flush=True)
            relatorio['status'] = 'concluido'
            codigo = 0
            print('Alvo alcançado usando a rota do mapa construído.', flush=True)
    except (RuntimeError, ValueError, KeyboardInterrupt) as erro:
        relatorio.update(status='interrompido', erro=str(erro) or 'Interrompido pelo usuário')
        codigo = 130 if isinstance(erro, KeyboardInterrupt) else 1
        print(f'Execução interrompida: {relatorio["erro"]}', flush=True)
    finally:
        matriz, canto = exploracao.mapa.exportar()
        relatorio.update(mapa_descoberto=matriz, canto_relativo=canto,
                         alvo_relativo=exploracao.mapa.alvo, origem_absoluta=no.origem_absoluta,
                         ultima_posicao_confirmada_relativa=no.posicao,
                         celulas_visitadas=len(exploracao.visitadas),
                         passos_exploracao=len(exploracao.trajeto) - 1,
                         trajeto_exploracao=exploracao.trajeto)
        args.saida.parent.mkdir(parents=True, exist_ok=True)
        args.saida.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'Relatório salvo em: {args.saida}', flush=True)
        no.processador.shutdown()
        no.destroy_node()
    return codigo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--intervalo', type=float, default=0.05, help='Segundos entre movimentos.')
    parser.add_argument('--saida', type=Path, default=Path('resultados/parte2.json'))
    args = parser.parse_args()
    if args.intervalo < 0:
        parser.error('--intervalo deve ser maior ou igual a zero.')
    rclpy.init(args=[])
    try:
        return executar(args)
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    raise SystemExit(main())
