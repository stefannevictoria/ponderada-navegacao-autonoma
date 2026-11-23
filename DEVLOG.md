# Registro do desenvolvimento

## 23/11/2026 — Preparação do simulador

- Ambiente identificado: Ubuntu 24.04, ROS 2 Jazzy, Python 3.12 e colcon.
- Copiado o simulador oficial no commit a6c182a74606bcd80d24fc3a20710b55decc863a,
  com licença e origem preservadas, sem um segundo repositório Git dentro deste.
- pygame estava ausente. Instalado pygame 2.6.1 em `.venv`, com acesso aos
  pacotes ROS do sistema por `--system-site-packages`.
- Adicionado `scripts/ambiente.bash` para configurar os terminais.
- Executado `colcon build --symlink-install`: três pacotes compilados com sucesso
  (`cg_interfaces`, `cg`, `cg_teleop`).
- Iniciado o simulador com `ros2 run cg maze -- --map test.csv`.
- Verificação real via cliente ROS temporário:
  - `/get_map` retornou dimensões 29 × 29.
  - Sensores iniciais: cima e esquerda `b`; baixo e direita `f`.
  - Movimento `right`: `success=True`, posição `[1, 2]`, alvo `[13, 14]`.
  - Reinício: `success=True`, mapa `test.csv`.
- Estes testes validam a instalação e a comunicação; os algoritmos das partes
  1 e 2 ainda não foram implementados.

Próximo passo: representar o mapa como grafo e implementar a busca da parte 1,
explicando a escolha do algoritmo e o critério de otimização.
