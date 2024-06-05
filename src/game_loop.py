import pygame
from src.module.TetrisInterface import TI
from src.module.Tetris import TetrisMap
from res.color import Color

keys = (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_SPACE)


def game_loop(screen: pygame.Surface, interface: TI, me: str, peer: str, fps: int = 60) -> None:
    """
    테트리스 게임 루프
    :param screen: Pygame 스크린 객체
    :param interface: TetrisInterface 객체
    :param me: 플레이어 이름
    :param peer: 동료 플레이어 이름
    :param fps: 주사율
    """
    clock = pygame.time.Clock()
    width, height = screen.get_width(), screen.get_height()
    unit = height // TetrisMap.height

    interface.start()

    while interface.get_state() != 2:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == keys[0]:
                    interface.move_left()
                if event.key == keys[1]:
                    interface.move_right()
                if event.key == keys[2]:
                    interface.rotate()
                if event.key == keys[3]:
                    interface.move_down()
                if event.key == keys[4]:
                    interface.superdown()

        interface.update()

        tetris_map = interface.get_map()
        my_pos = interface.get_position(me)
        peer_pos = interface.get_position(peer)
        score = interface.get_score()
        queue = interface.get_queue()

        screen.fill(Color.game_bg.value)

        pygame.draw.rect(screen, Color.black.value, (0, 0, unit * 10, unit * 30))
        for color, pos in [(Color.my_egde.value, my_pos), (Color.peer_edge.value, peer_pos)]:
            for i, j in pos:
                pygame.draw.rect(screen, color, (j * unit - 2, i * unit - 2, unit + 4, unit + 4))

        for i in range(len(tetris_map)):
            for j in range(len(tetris_map[i])):
                if tetris_map[i][j]:
                    pygame.draw.rect(
                        screen,
                        Color.blocks.value[tetris_map[i][j]],
                        (j * unit, i * unit, unit, unit)
                    )

        pygame.display.update()

        clock.tick(fps)


if __name__ == "__main__":
    from src.network.PairSocket import *
    from src.network.protocol import tetris_port
    from src.network.ServerScanner import ServerScanner
    from src.module.TetrisInterface import TetrisServerInterface, TetrisClientInterface
    from time import sleep
    import pygame
    from random import choice
    from threading import Thread

    server, client = "kim", "Lee"
    server_sock = PairServerSocket(server)
    client_sock = PairClientSocket(client)
    scanner = ServerScanner()

    server_sock.start("0.0.0.0", tetris_port)
    print("server started.")

    scanner.scan(tetris_port)
    server_list = []
    while not server_list:
        server_list = scanner.get_server_list()
    print(server_list)

    client_sock.start(server_list[0][0], server_list[0][1])
    print("client started.")

    while None in (client_sock.get_opposite(), server_sock.get_opposite()):
        continue
    print("connected.")

    server_system = TetrisServerInterface(server_sock)
    client_system = TetrisClientInterface(client_sock)

    pygame.init()
    screen = pygame.display.set_mode((600, 600))


    def pseudo_loop(system) -> None:
        system.start()
        clock = pygame.time.Clock()

        def nothing() -> None:
            pass

        controls = [nothing] * 30 + [
            system.rotate,
            system.move_left,
            system.move_right,
        ]

        while True:
            system.update()
            choice(controls)()
            clock.tick(60)


    side = True
    if side:
        Thread(target=pseudo_loop, args=(server_system,), daemon=True).start()
        game_loop(screen, client_system, client, server)
    else:
        Thread(target=pseudo_loop, args=(client_system,), daemon=True).start()
        game_loop(screen, server_system, server, client)
