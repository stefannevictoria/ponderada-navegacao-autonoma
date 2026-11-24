# Atividade ponderada — Navegação autônoma

O objetivo desta ponderada é aplicar algoritmos de grafos para fazer um robô encontrar o caminho até um alvo em um labirinto. O projeto usa Python e um simulador em pygame, com comunicação pelo ROS 2.

A atividade tem duas partes:

1. **Navegação com mapa:** o robô tem acesso ao labirinto completo e deve encontrar uma rota otimizada até o alvo.
2. **Mapeamento do labirinto:** o robô deve explorar o ambiente e construir um mapa durante a navegação. Depois, é preciso demonstrar que esse mapa permite reproduzir a rota da primeira parte.

Até o momento, a parte 1 está implementada e foi testada em três mapas. A parte 2 ainda será desenvolvida.

## Simulador

Foi utilizado o [Culling Games](https://github.com/rmnicola/culling_games), indicado no enunciado. O labirinto é uma matriz em que cada célula representa uma posição do ambiente:

| Cor | Elemento | Símbolo no mapa |
| --- | --- | --- |
| Azul | Robô | `r` |
| Vermelho | Alvo | `t` |
| Branco | Espaço livre | `f` |
| Preto | Parede | `b` |

O robô pode se mover para cima, para baixo, para a esquerda e para a direita. Os comandos são enviados por serviços ROS.

O código original está na pasta [`simulador/`](simulador/), com a licença MIT preservada. A referência ao repositório e ao commit utilizado está em [`simulador/ORIGEM.md`](simulador/ORIGEM.md). A solução da atividade fica separada, na pasta [`navegacao/`](navegacao/).

## Preparação do ambiente

O ambiente utilizado foi Ubuntu 24.04, Python 3.12 e ROS 2 Jazzy, com `colcon` instalado. A comunicação foi testada com Cyclone DDS. Caso ele não esteja instalado em outro ambiente Jazzy:

```bash
sudo apt install ros-jazzy-rmw-cyclonedds-cpp
```

Na raiz do repositório, crie o ambiente Python, instale as dependências e compile os pacotes do simulador:

```bash
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install -r requirements.txt
source scripts/ambiente.bash
cd simulador
colcon build --symlink-install
cd ..
source scripts/ambiente.bash
```

O arquivo `scripts/ambiente.bash` carrega o ROS, o ambiente Python e os pacotes compilados. Ele deve ser carregado em cada terminal usado para executar o projeto. Também seleciona Cyclone DDS por padrão, pois houve perdas intermitentes de respostas nos testes com a configuração anterior.

## Parte 1 — Encontrando o menor caminho

A solução começa consultando o serviço `/get_map`, que retorna o mapa completo. Com esses dados, o programa monta a matriz e identifica as posições do robô, do alvo e das paredes. As coordenadas seguem a ordem `(linha, coluna)`.

Para calcular a rota, foi utilizada a **busca em largura (BFS)**. Cada célula livre funciona como um vértice do grafo, e cada movimento permitido entre células vizinhas funciona como uma aresta. Como todos os movimentos custam um passo, a BFS encontra um caminho com o menor número de movimentos.

A busca usa uma fila: primeiro verifica as posições a um passo do início, depois as posições a dois passos, e assim por diante. As células visitadas são registradas para evitar repetições. O programa também guarda de qual célula chegou a cada posição, permitindo reconstruir o caminho quando encontra o alvo.

Depois do planejamento, a rota é convertida em comandos enviados ao serviço `/move_command`. O programa confere a posição retornada após cada movimento e salva um relatório com a rota planejada e o que foi executado. Se não houver caminho até o alvo, informa isso sem mover o robô.

Os arquivos principais são:

- [`navegacao/busca.py`](navegacao/busca.py): busca em largura e conversão da rota em movimentos.
- [`navegacao/parte1.py`](navegacao/parte1.py): leitura do mapa, comunicação com o simulador e execução da rota.

### Resultados

A navegação foi testada com o simulador em três mapas:

| Mapa | Movimentos planejados | Movimentos executados | Resultado |
| --- | ---: | ---: | --- |
| `test.csv` | 25 | 25 | Alvo alcançado |
| `1.csv` | 102 | 102 | Alvo alcançado |
| `2.csv` | 102 | 102 | Alvo alcançado |

As rotas também foram comparadas com uma implementação independente de Dijkstra para conferir o custo mínimo. Dijkstra foi usado apenas nessa verificação; o algoritmo de navegação é a BFS.

Os relatórios estão na pasta [`resultados/`](resultados/). Eles contêm o mapa inicial, a rota, os comandos, a quantidade de movimentos e a posição final. Os testes de integração foram executados com o simulador sem janela, em domínios ROS separados.

### Demonstração

Execução da parte 1, com o robô seguindo automaticamente a rota calculada com BFS até o alvo.

![Robô percorrendo automaticamente a rota calculada com BFS](assets/parte1.gif)

### Como executar

#### Abrir o labirinto

Em um terminal na raiz do repositório:

```bash
source scripts/ambiente.bash
ros2 run cg maze -- --map test.csv
```

#### Executar a rota

Com o simulador aberto, use outro terminal na raiz do repositório:

```bash
source scripts/ambiente.bash
python -m navegacao.parte1
```

O robô deve percorrer a rota até o alvo. Para apenas calcular a rota, sem movimentá-lo:

```bash
python -m navegacao.parte1 --planejar
```

O resultado é salvo em `resultados/parte1.json`. Para repetir a execução desde o início, reinicie o mapa e aguarde o robô voltar à posição inicial:

```bash
ros2 service call /reset cg_interfaces/srv/Reset "{is_random: false}"
```

Mantenha apenas um simulador ativo no mesmo domínio ROS e não envie comandos manuais durante a navegação automática. Se o simulador já estava aberto antes de atualizar a configuração do projeto, encerre com `Ctrl+C` e abra novamente após carregar `scripts/ambiente.bash`.

### Testes

Foram criados dez testes automatizados: seis para a busca e quatro para a confirmação dos movimentos. Eles verificam situações como desvio de paredes, alvo inacessível e posição diferente da esperada.

Para executá-los:

```bash
source scripts/ambiente.bash
python -m unittest discover -s tests -v
```

Para repetir a navegação nos três mapas e a comparação com Dijkstra:

```bash
python scripts/verificar_parte1_ros.py
```

Se uma resposta de movimento não chegar em dez segundos, o cliente não repete o comando, pois o robô pode já ter se movido. Na parte 1, ele consulta o mapa para confirmar a posição esperada antes de continuar. Se não conseguir confirmar, interrompe a execução. Os testes finais com Cyclone DDS concluíram os três mapas sem precisar dessa recuperação.

## Parte 2 — Construindo o mapa

Nesta etapa, o mapa deverá ser construído a partir das observações do robô durante a exploração. O simulador disponibiliza as informações das células ao redor pelo tópico `/culling_games/robot_sensors`.

Após o mapeamento, será necessário usar o mapa construído para reproduzir a rota da parte 1. Essa etapa ainda não foi implementada.
