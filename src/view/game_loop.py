import pygame
from src.module.TetrisSystem import TS
from src.module.Tetris import TetrisMap

keys = (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_SPACE)
my_color, peer_color = (255, 0, 0), (0, 255, 0)
block_color = {
    1: (255, 255, 127),
    2: (127, 255, 127),
    3: (255, 127, 127),
    4: (127, 127, 255),
    5: (255, 191, 127),
    6: (255, 127, 255),
    7: (127, 255, 255),
}


def game_loop(screen: pygame.Surface, system: TS, me: str, peer: str, fps: int = 60) -> None:
    clock = pygame.time.Clock()
    width, height = screen.get_width(), screen.get_height()
    unit = height // TetrisMap.height

    system.start()

    while system.get_state() != 2:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == keys[0]:
                    system.move_left()
                if event.key == keys[1]:
                    system.move_right()
                if event.key == keys[2]:
                    system.rotate()
                if event.key == keys[3]:
                    system.move_down()
                if event.key == keys[4]:
                    system.superdown()

        system.update()

        tetris_map = system.get_map()
        my_pos = system.get_position(me)
        peer_pos = system.get_position(peer)
        score = system.get_score()
        queue = system.get_queue()

        screen.fill((50, 50, 50))
        pygame.draw.rect(screen, (0, 0, 0), (0, 0, unit * 10, unit * 30))
        for color, pos in [(my_color, my_pos), (peer_color, peer_pos)]:
            for i, j in pos:
                pygame.draw.rect(screen, color, (j * unit - 2, i * unit - 2, unit + 4, unit + 4))
        for i in range(len(tetris_map)):
            for j in range(len(tetris_map[i])):
                if tetris_map[i][j]:
                    pygame.draw.rect(screen, block_color[tetris_map[i][j]], (j * unit, i * unit, unit, unit))
        pygame.display.update()

        clock.tick(fps)


if __name__ == "__main__":
    from src.network.PairSocket import *
    from src.network.protocol import tetris_port
    from src.network.ServerScanner import ServerScanner
    from src.module.TetrisSystem import TetrisServerSystem, TetrisClientSystem
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

    server_system = TetrisServerSystem(server_sock)
    client_system = TetrisClientSystem(client_sock)

    pygame.init()
    screen = pygame.display.set_mode((600, 600))

    def client_loop() -> None:
        print("client entered.")
        while True:
            sleep(1)
            choice([
                client_system.rotate,
                client_system.move_left,
                client_system.move_right,
            ])()

    Thread(target=client_loop, daemon=True).start()
    game_loop(screen, server_system, server, client)
