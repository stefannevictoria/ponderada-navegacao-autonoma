"""Busca em largura em um grid; este módulo não depende de ROS."""

from collections import deque

# Coordenadas sempre na ordem (linha, coluna). Não há movimentos diagonais.
DIRECOES = {
    'up': (-1, 0),
    'down': (1, 0),
    'left': (0, -1),
    'right': (0, 1),
}


def validar_mapa(mapa):
    if not mapa or not mapa[0] or any(len(linha) != len(mapa[0]) for linha in mapa):
        raise ValueError('O mapa deve ser uma matriz retangular não vazia.')
    if any(celula not in {'b', 'f', 'r', 't'} for linha in mapa for celula in linha):
        raise ValueError('O mapa contém uma célula desconhecida.')


def localizar(mapa, simbolo):
    posicoes = [(l, c) for l, linha in enumerate(mapa)
                for c, celula in enumerate(linha) if celula == simbolo]
    if len(posicoes) != 1:
        raise ValueError(f'Esperado um único símbolo {simbolo!r}; encontrados {len(posicoes)}.')
    return posicoes[0]


def bfs(mapa, inicio, alvo):
    """Retorna uma rota mínima incluindo início e alvo, ou None se inacessível."""
    validar_mapa(mapa)
    for linha, coluna in (inicio, alvo):
        if not (0 <= linha < len(mapa) and 0 <= coluna < len(mapa[0])):
            raise ValueError('Posição fora do mapa.')
        if mapa[linha][coluna] == 'b':
            raise ValueError('Início e alvo precisam ser transitáveis.')

    fila = deque([inicio])
    # O dicionário serve como conjunto de visitados e guarda os predecessores.
    anterior = {inicio: None}
    while fila:
        atual = fila.popleft()
        if atual == alvo:
            rota = []
            while atual is not None:
                rota.append(atual)
                atual = anterior[atual]
            return list(reversed(rota))

        for dl, dc in DIRECOES.values():
            vizinho = (atual[0] + dl, atual[1] + dc)
            l, c = vizinho
            if (0 <= l < len(mapa) and 0 <= c < len(mapa[0])
                    and mapa[l][c] != 'b' and vizinho not in anterior):
                anterior[vizinho] = atual
                fila.append(vizinho)
    return None


def movimentos_da_rota(rota):
    """Converte pares de células adjacentes em comandos do simulador."""
    nomes = {delta: nome for nome, delta in DIRECOES.items()}
    movimentos = []
    for origem, destino in zip(rota, rota[1:]):
        delta = (destino[0] - origem[0], destino[1] - origem[1])
        if delta not in nomes:
            raise ValueError('A rota contém um movimento inválido.')
        movimentos.append(nomes[delta])
    return movimentos
