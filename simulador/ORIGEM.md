# Origem do simulador

Código de https://github.com/rmnicola/culling_games

Commit: `a6c182a74606bcd80d24fc3a20710b55decc863a`

Código baseado no commit acima, com licença MIT preservada em LICENSE.
Os algoritmos da atividade ficam separados, na pasta `navegacao/` da raiz do projeto.

## Alteração local

Em `src/cg/cg/Game.py`, o laço de renderização passou a usar `pygame.time.Clock().tick(60)`. O limite de 60 FPS evita redesenhar continuamente sem pausa e libera CPU para o processamento ROS. Os serviços, sensores e regras do labirinto foram mantidos.
