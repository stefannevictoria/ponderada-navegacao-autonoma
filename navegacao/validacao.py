"""Comparação offline: nenhum dado da referência é enviado ao explorador."""

import argparse
import json
from pathlib import Path

from .busca import bfs


def comparar(parte1, parte2):
    if parte2.get('status') != 'concluido':
        raise ValueError('A parte 2 não concluiu a navegação.')
    origem = parte2['origem_absoluta']
    if origem is None or list(origem) != list(parte1['inicio']):
        raise ValueError('As execuções precisam partir da mesma posição. Reinicie o mesmo mapa.')
    mapa = parte1['mapa_inicial']
    rota_referencia = bfs(mapa, tuple(parte1['inicio']), tuple(parte1['alvo']))
    if rota_referencia is None:
        raise ValueError('Não existe rota na referência da parte 1.')
    rota = [tuple(p) for p in parte2['rota_reproduzida']]
    absoluta = [(l + origem[0], c + origem[1]) for l, c in rota]
    matriz = parte2['mapa_descoberto']
    ml, mc = parte2['canto_relativo']
    for l, linha in enumerate(matriz):
        for c, tipo in enumerate(linha):
            if tipo == '?':
                continue
            la, ca = l + ml + origem[0], c + mc + origem[1]
            if not (0 <= la < len(mapa) and 0 <= ca < len(mapa[0])):
                raise ValueError('O mapa construído contém uma observação fora da referência.')
            real = mapa[la][ca]
            if ('f' if tipo == 'r' else tipo) != ('f' if real == 'r' else real):
                raise ValueError('O mapa construído diverge do mapa de referência.')

    def conhecido(posicao):
        l, c = posicao[0] - origem[0] - ml, posicao[1] - origem[1] - mc
        return 0 <= l < len(matriz) and 0 <= c < len(matriz[0]) and matriz[l][c] in {'f', 'r', 't'}

    rota_valida = bool(absoluta) and absoluta[0] == tuple(parte1['inicio']) and absoluta[-1] == tuple(parte1['alvo'])
    for a, b in zip(absoluta, absoluta[1:]):
        rota_valida = rota_valida and abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1
    rota_valida = rota_valida and all(conhecido(p) for p in absoluta)
    return {
        'mapa_consistente': True,
        'mapa_suficiente_para_rota_parte1': all(conhecido(p) for p in rota_referencia),
        'mesma_rota': absoluta == rota_referencia,
        'mesmo_custo': len(absoluta) == len(rota_referencia),
        'execucao_confirmada': (rota_valida and parte2['passos_rota_executados'] == len(absoluta) - 1
                               and tuple(parte2['ultima_posicao_confirmada_relativa']) == rota[-1]),
        'passos_parte1': len(rota_referencia) - 1,
        'passos_parte2': len(absoluta) - 1,
    }


def aprovada(resultado):
    return all(resultado[chave] for chave in ('mapa_consistente', 'mapa_suficiente_para_rota_parte1',
                                             'mesma_rota', 'mesmo_custo', 'execucao_confirmada'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parte1', type=Path, required=True)
    parser.add_argument('--parte2', type=Path, required=True)
    parser.add_argument('--saida', type=Path, default=Path('resultados/validacao_parte2.json'))
    args = parser.parse_args()
    try:
        resultado = comparar(json.loads(args.parte1.read_text()), json.loads(args.parte2.read_text()))
    except (ValueError, KeyError, TypeError, OSError) as erro:
        print(f'Comparação não concluída: {erro}')
        return 1
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0 if aprovada(resultado) else 1


if __name__ == '__main__':
    raise SystemExit(main())
