import pygame

from res.color import Color
from res.font.font import fonts
from src.module.Tetris import TetrisMap
from src.module.TetrisInterface import TI

keys = (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_SPACE)


def game_loop(screen: pygame.Surface, interface: TI, fps: int = 60) -> None:
    """
    테트리스 게임 루프
    :param screen: Pygame 스크린 객체
    :param interface: TetrisInterface 객체
    :param fps: 주사율
    """
    clock = pygame.time.Clock()
    width, height = screen.get_width(), screen.get_height()
    unit = height // TetrisMap.height

    done = False
    
    interface.start()

    while not done:
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
                if event.key == pygame.K_RETURN and interface.get_state() == 2:
                    done = True

        interface.update()

        screen.fill(Color.black.value)

        pygame.draw.rect(screen, Color.white.value, (0, 0, unit * 10, unit * 30), 1)
        for color, pos in [
            (Color.my_egde.value, interface.get_position(interface.get_name())),
            (Color.peer_edge.value, interface.get_position(interface.get_opposite()))
        ]:
            for i, j in pos:
                pygame.draw.rect(screen, color, (j * unit - 2, i * unit - 2, unit + 4, unit + 4))

        tetris_map = interface.get_map()
        for i in range(len(tetris_map)):
            for j in range(len(tetris_map[i])):
                if tetris_map[i][j]:
                    pygame.draw.rect(
                        screen,
                        Color.blocks.value[tetris_map[i][j]],
                        (j * unit, i * unit, unit, unit)
                    )

        offset = height // 2 - 30
        for index, (content, font_size) in enumerate([
            ("Peer: " + interface.get_opposite(), 4),
            ("Score: " + str(interface.get_score()), 5),
            ("Game Over", 6),
            ("Press enter to exit.", 4),
        ]):
            if interface.get_state() != 2 and 2 <= index:
                break
            text = fonts[font_size].render(content, True, Color.white.value)
            screen.blit(
                text,
                (unit * (TetrisMap.width + 3), offset)
            )
            offset += text.get_height() + 10

        offset = TetrisMap.width + 1
        for index, block in enumerate(interface.get_queue()[:3]):
            last = 0
            for i in range(5):
                for j in range(5):
                    if j < len(block) and i < len(block[j]) and block[j][i]:
                        last = i
                        pygame.draw.rect(
                            screen,
                            Color.lightgrey.value,
                            ((offset + i) * unit, (1 + j) * unit, unit, unit)
                        )
            offset += last + 2

        pygame.display.update()

        clock.tick(fps)


if __name__ == "__main__":
    from src.network.PairSocket import PairClientSocket, PairServerSocket
    from src.network.protocol import tetris_port
    from src.network.ServerScanner import ServerScanner
    from src.module.TetrisInterface import TetrisServerInterface, TetrisClientInterface
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
        game_loop(screen, client_system)
    else:
        Thread(target=pseudo_loop, args=(client_system,), daemon=True).start()
        game_loop(screen, server_system)
