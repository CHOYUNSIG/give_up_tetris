import pygame

from src.game_loop import game_loop
from src.lobby_loop import lobby_loop
from src.module.LobbyInterface import LobbyInterface
from src.module.TetrisInterface import TetrisServerInterface, TetrisClientInterface
from src.network.PairSocket import PS


def main_loop(screen: pygame.Surface, name: str, fps: int = 60) -> None:
    socket: PS | None = None

    while True:
        if socket is None:
            lobby = LobbyInterface(name)
        else:
            lobby = LobbyInterface(socket)

        lobby_loop(screen, lobby, fps)

        socket, is_server = lobby.get_socket()
        if is_server:
            tetris = TetrisServerInterface(socket)
        else:
            tetris = TetrisClientInterface(socket)

        game_loop(screen, tetris, fps)


if __name__ == "__main__":
    pygame.init()
    size = (600, 600)
    name = input("enter your name: ")
    main_loop(pygame.display.set_mode(size), name)
