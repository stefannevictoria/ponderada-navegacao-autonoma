"""Mapeamento por observações locais e exploração DFS, sem dependência de ROS."""

from .busca import DIRECOES, bfs

SENSORES = {**DIRECOES, 'up_left': (-1, -1), 'up_right': (-1, 1),
            'down_left': (1, -1), 'down_right': (1, 1)}


class MapaDescoberto:
    def __init__(self):
        self.celulas = {(0, 0): 'f'}
        self.alvo = None

    def observar(self, posicao, leitura):
        self.celulas[posicao] = 'f'
        for nome, (dl, dc) in SENSORES.items():
            tipo = leitura[nome]
            if tipo not in {'f', 'b', 't', 'r'}:
                raise ValueError(f'Leitura de sensor inválida: {nome}={tipo!r}.')
            tipo = 'f' if tipo == 'r' else tipo
            vizinho = (posicao[0] + dl, posicao[1] + dc)
            anterior = self.celulas.get(vizinho)
            if anterior is not None and anterior != tipo:
                raise ValueError('Observação incompatível com o mapa. Reinicie sem controle manual.')
            self.celulas[vizinho] = tipo
            if tipo == 't':
                if self.alvo is not None and self.alvo != vizinho:
                    raise ValueError('Foram observados dois alvos diferentes.')
                self.alvo = vizinho

    def exportar(self):
        minimo_l = min(l for l, c in self.celulas)
        minimo_c = min(c for l, c in self.celulas)
        maximo_l = max(l for l, c in self.celulas)
        maximo_c = max(c for l, c in self.celulas)
        matriz = [[self.celulas.get((l, c), '?')
                   for c in range(minimo_c, maximo_c + 1)]
                  for l in range(minimo_l, maximo_l + 1)]
        matriz[-minimo_l][-minimo_c] = 'r'
        return matriz, (minimo_l, minimo_c)

    def rota_minima(self):
        if self.alvo is None:
            return None
        matriz, (ml, mc) = self.exportar()
        # Desconhecido não é parede: apenas não é autorizado para o planejamento.
        planejamento = [['b' if celula == '?' else celula for celula in linha]
                        for linha in matriz]
        inicio = (-ml, -mc)
        alvo = (self.alvo[0] - ml, self.alvo[1] - mc)
        rota = bfs(planejamento, inicio, alvo)
        return None if rota is None else [(l + ml, c + mc) for l, c in rota]


class ExploracaoDFS:
    def __init__(self):
        self.mapa = MapaDescoberto()
        self.visitadas = {(0, 0)}
        self.trajeto = [(0, 0)]
        self.pilha = [(0, 0)]

    def explorar(self, observar, mover):
        """Callbacks de sensores e movimento; não recebe o mapa real nem o alvo."""
        while self.pilha:
            atual = self.pilha[-1]
            self.mapa.observar(atual, observar())
            proxima = None
            for nome, (dl, dc) in DIRECOES.items():
                vizinho = (atual[0] + dl, atual[1] + dc)
                # O alvo fica para a rota final, pois entrar nele encerra o jogo.
                if self.mapa.celulas.get(vizinho) == 'f' and vizinho not in self.visitadas:
                    proxima = (nome, vizinho)
                    break
            if proxima is not None:
                nome, vizinho = proxima
                mover(nome, vizinho)
                self.visitadas.add(vizinho)
                self.pilha.append(vizinho)
                self.trajeto.append(vizinho)
            elif len(self.pilha) > 1:
                anterior = self.pilha[-2]
                delta = (anterior[0] - atual[0], anterior[1] - atual[1])
                nome = next(nome for nome, deslocamento in DIRECOES.items() if deslocamento == delta)
                mover(nome, anterior)
                self.pilha.pop()
                self.trajeto.append(anterior)
            else:
                self.pilha.pop()
        return self.mapa.rota_minima()
