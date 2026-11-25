"""Teste das duas partes em mapas pequenos, com comparação após a exploração.

Execute na raiz: source scripts/ambiente.bash && python scripts/verificar_parte2_ros.py
As instâncias de teste usam Cyclone DDS, SDL sem janela e domínios ROS 94 a 99.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import textwrap

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from navegacao.validacao import aprovada, comparar

MAPAS = {
    'exploracao': ROOT / 'tests/mapas/exploracao.csv',
    'alvo_passagem': ROOT / 'tests/mapas/alvo_passagem.csv',
    'mapa1': ROOT / 'simulador/src/cg/maps/1.csv',
}

# O bloqueio só atua no processo do explorador, sem alterar o simulador.
# Falha se o código tentar consultar o mapa completo ou abrir um CSV.
EXECUCAO_PROTEGIDA = textwrap.dedent('''
    import os
    import sys
    from rclpy.node import Node
    original = Node.create_client
    def criar_cliente(self, tipo, nome, *args, **kwargs):
        if nome.rstrip('/') == '/get_map':
            raise AssertionError('O explorador não pode consultar /get_map.')
        return original(self, tipo, nome, *args, **kwargs)
    Node.create_client = criar_cliente
    def auditar(evento, argumentos):
        if evento == 'open' and isinstance(argumentos[0], (str, bytes, os.PathLike)):
            if os.fsdecode(argumentos[0]).lower().endswith('.csv'):
                raise AssertionError('O explorador não pode ler mapas CSV.')
    sys.addaudithook(auditar)
    from navegacao.parte2 import main
    raise SystemExit(main())
''')


def executar_fase(nome, parte, dominio, pasta):
    ambiente = os.environ.copy()
    ambiente.update(RMW_IMPLEMENTATION='rmw_cyclonedds_cpp', ROS_DOMAIN_ID=str(dominio),
                    SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
                    ROS_LOG_DIR='/tmp/ponderada-parte2-ros-logs')
    mapa = MAPAS[nome]
    saida = pasta / f'parte{parte}.json'
    log = Path(f'/tmp/parte2-{nome}-fase{parte}.log')
    with log.open('w') as arquivo:
        simulador = subprocess.Popen(['ros2', 'run', 'cg', 'maze', '--', '--map', str(mapa)],
                                     cwd=ROOT, env=ambiente, stdout=arquivo,
                                     stderr=subprocess.STDOUT, start_new_session=True)
        try:
            comando = ([sys.executable, '-m', 'navegacao.parte1'] if parte == 1
                       else [sys.executable, '-c', EXECUCAO_PROTEGIDA])
            resultado = subprocess.run(comando + ['--intervalo', '0', '--saida', str(saida)],
                                       cwd=ROOT, env=ambiente, timeout=300)
            if resultado.returncode:
                raise RuntimeError(f'Falha no mapa {nome}, parte {parte}. Log do simulador: {log}')
        finally:
            if simulador.poll() is None:
                os.killpg(simulador.pid, signal.SIGINT)
                try:
                    simulador.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(simulador.pid, signal.SIGKILL)
                    simulador.wait()
    return json.loads(saida.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mapas', nargs='+', choices=list(MAPAS), default=list(MAPAS))
    args = parser.parse_args()
    for i, nome in enumerate(args.mapas):
        pasta = ROOT / 'resultados' / 'parte2' / nome
        pasta.mkdir(parents=True, exist_ok=True)
        parte1 = executar_fase(nome, 1, 94 + i * 2, pasta)
        parte2 = executar_fase(nome, 2, 95 + i * 2, pasta)
        comparacao = comparar(parte1, parte2)
        (pasta / 'comparacao.json').write_text(json.dumps(comparacao, ensure_ascii=False, indent=2) + '\n')
        if not aprovada(comparacao):
            raise RuntimeError(f'A comparação falhou: {comparacao}')
        print(f'{nome}: {parte2["passos_exploracao"]} movimentos de exploração; '
              f'rota final de {comparacao["passos_parte2"]} movimentos, igual à parte 1.', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
