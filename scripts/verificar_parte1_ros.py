"""Execute na raiz do projeto, após source scripts/ambiente.bash.

Verifica três mapas com simuladores sem janela em domínios ROS 89, 90 e 91.
Compara o custo das rotas com Dijkstra, usado somente para validação.
"""
import heapq
import json
import os
from pathlib import Path
import signal
import subprocess

root = Path.cwd()
env = os.environ.copy()
env['RMW_IMPLEMENTATION'] = 'rmw_cyclonedds_cpp'
env.update(ROS_DOMAIN_ID='83', SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', ROS_LOG_DIR='/tmp/ponderada-parte1-ros-logs')
(root / 'resultados').mkdir(exist_ok=True)

def distancia_dijkstra(mapa, inicio, alvo):
    fila = [(0, inicio)]
    visitados = set()
    while fila:
        custo, pos = heapq.heappop(fila)
        if pos in visitados:
            continue
        visitados.add(pos)
        if pos == alvo:
            return custo
        for dl, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            l, c = pos[0] + dl, pos[1] + dc
            if 0 <= l < len(mapa) and 0 <= c < len(mapa[0]) and mapa[l][c] != 'b':
                heapq.heappush(fila, (custo + 1, (l, c)))
    return None

for dominio, nome in enumerate(['test', '1', '2'], 89):
    env['ROS_DOMAIN_ID'] = str(dominio)
    with open(f'/tmp/parte1-simulador-{nome}.log', 'w') as log:
        sim = subprocess.Popen(['ros2', 'run', 'cg', 'maze', '--', '--map', f'{nome}.csv'],
                               env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            saida = f'resultados/parte1_mapa_{nome}.json'
            teste = subprocess.run(['python', '-m', 'navegacao.parte1', '--intervalo', '0.02', '--saida', saida],
                                   env=env, text=True, stderr=subprocess.STDOUT, timeout=300)
            if teste.returncode:
                raise RuntimeError(f'Falha no mapa {nome}; consulte /tmp/parte1-simulador-{nome}.log')
            relatorio = json.loads(Path(saida).read_text())
            minimo = distancia_dijkstra(relatorio['mapa_inicial'], tuple(relatorio['inicio']), tuple(relatorio['alvo']))
            assert relatorio['status'] == 'concluido'
            assert relatorio['posicao_final'] == relatorio['alvo']
            assert relatorio['passos_planejados'] == relatorio['passos_executados'] == minimo
            rota = relatorio['rota']
            for a, b in zip(rota, rota[1:]):
                assert abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1
                assert relatorio['mapa_inicial'][b[0]][b[1]] != 'b'
            print(f'{nome}.csv: alvo alcançado em {minimo} movimentos; mínimo confirmado com Dijkstra.', flush=True)
        finally:
            if sim.poll() is None:
                os.killpg(sim.pid, signal.SIGINT)
                try:
                    sim.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(sim.pid, signal.SIGKILL)
                    sim.wait()
