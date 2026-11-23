# ponderada-navegacao-autonoma

Desafio de navegação autônoma em labirinto com ROS 2 e algoritmos de grafos.

## Etapas

- [x] Preparar e compilar o simulador.
- [x] Testar mapa, sensores, movimento e reinício.
- [ ] Parte 1: encontrar e executar uma rota otimizada com mapa conhecido.
- [ ] Parte 2: explorar usando sensores, construir o mapa e validar a rota.
- [ ] Documentar os resultados e as evidências finais.

## Ambiente usado

Ubuntu 24.04, ROS 2 Jazzy, Python 3.12 e colcon previamente instalados.

## Preparação

Na raiz deste repositório:

```bash
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install -r requirements.txt
source scripts/ambiente.bash
cd simulador
colcon build --symlink-install
cd ..
source scripts/ambiente.bash
```

O ambiente virtual reutiliza os pacotes ROS do sistema. O script também inclui
as dependências do ambiente virtual no PYTHONPATH dos executáveis ROS.

## Abrir o simulador

Em um terminal na raiz do repositório:

```bash
source scripts/ambiente.bash
ros2 run cg maze -- --map test.csv
```

Em outro terminal, também na raiz:

```bash
source scripts/ambiente.bash
ros2 run cg_teleop teleop_keyboard
```

Use WASD no terminal de teleoperação para movimentar o robô. A tecla `r`
reinicia o mesmo mapa. Encerre cada processo com Ctrl+C.

## Interfaces para os algoritmos

- `/get_map`: mapa completo para a parte 1.
- `/move_command`: movimentação nas direções up, down, left e right.
- `/culling_games/robot_sensors`: observação das oito células adjacentes.
- `/reset`: reinício do mapa.

O mapa usa `b` para parede, `f` para espaço livre, `r` para robô e `t` para alvo.
As posições retornadas pelo serviço seguem a ordem linha, coluna.
Na parte 2, o mapeamento será construído pelas observações locais.

## Origem do simulador

A pasta `simulador/` contém código do professor, sem alterações, com a licença
MIT original preservada. Consulte [a origem e o commit](simulador/ORIGEM.md).
Os algoritmos próprios ainda serão implementados.

## Registro do desenvolvimento

Veja [DEVLOG.md](DEVLOG.md).
