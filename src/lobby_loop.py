from threading import Semaphore
from typing import Callable

import pygame

from res.color import Color
from res.string import String
from src.module.LobbyInterface import LobbyInterface
from src.util.keymap import keymap
from src.view.Alignment import Alignment
from src.view.Button import EdgeButton
from src.view.TextHolder import TextHolder
from src.view.widget import Drawable, Clickable


def lobby_loop(screen: pygame.Surface, interface: LobbyInterface, fps: int = 60):
    clock = pygame.time.Clock()
    width, height = screen.get_width(), screen.get_height()
    fonts = [pygame.font.Font("./res/font/D2Coding-Ver1.3.2-20180524.ttf", 6 * i) for i in range(10)]
    
    # 상태
    scanning = False
    connecting = False
    selected_ip: str | None = None

    # 위젯
    chat_holder: TextHolder
    ready_btn: EdgeButton
    scan_btn: EdgeButton
    connect_btn: EdgeButton
    server_btn_list: list[EdgeButton] = []
    
    # 콜백
    def toggle_ready() -> None:
        if interface.get_opposite() is None:
            return
        ready = interface.toggle_ready()
        if ready:
            ready_btn.color = Color.green.value
        else:
            ready_btn.color = Color.white.value

    def scan() -> None:
        nonlocal scanning
        if scanning:
            return
        sem = Semaphore()
        sem.acquire()
        scanning = True
        interface.scan_server(sem)
        sem.acquire()
        scan_btn.text = String.scanning.value + "..."
        scan_btn.color = Color.lightgrey.value

    def connect() -> None:
        nonlocal connecting
        if selected_ip is None:
            return
        sem = Semaphore()
        sem.acquire()
        connecting = True
        interface.connect_server(selected_ip, sem)
        sem.acquire()
        connect_btn.text = String.connecting.value + "..."
        connect_btn.color = Color.lightgrey.value

    # 선언
    chat_holder = TextHolder(
        (width // 2, height - 250),
        (width // 2, 50),
        Color.white.value,
        fonts[3],
        align=Alignment.middle_left,
    )

    ready_btn = EdgeButton(
        (width // 2, height - 100),
        (width // 2, 100),
        toggle_ready,
        String.ready.value,
        fonts[4],
        Color.white.value,
        3,
    )

    scan_btn = EdgeButton(
        (0, 0),
        (width // 2, 100),
        scan,
        String.scan.value,
        fonts[4],
        Color.white.value,
        3,
    )

    connect_btn = EdgeButton(
        (0, height - 100),
        (width // 2, 100),
        connect,
        String.connect.value,
        fonts[4],
        Color.white.value,
        3,
    )

    chat_holder.activate()
    ready_btn.activate()
    scan_btn.activate()
    connect_btn.activate()

    interface.start()

    while not interface.check_ready():
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                Clickable.spread_click(pygame.mouse.get_pos())
            if event.type == pygame.KEYDOWN:
                if event.key in keymap:
                    chat_holder.value += keymap[event.key]
                if event.key == pygame.K_BACKSPACE and len(chat_holder.value) > 0:
                    chat_holder.value = chat_holder.value[:-1]
                if event.key == pygame.K_RETURN:
                    interface.send_chat(chat_holder.value)
                    chat_holder.value = ""

        if scanning and not interface.is_scanning():
            scanning = False
            selected_ip = None
            scan_btn.text = String.scan.value
            scan_btn.color = Color.white.value
            for server_btn in server_btn_list:
                server_btn.kill()
            server_btn_list = []
            for index, (name, ip) in enumerate(interface.get_serverlist()):

                def callback(index: int, ip: str) -> Callable[[], None]:
                    def f() -> None:
                        nonlocal selected_ip
                        if ip == selected_ip:
                            selected_ip = None
                            server_btn_list[index].color = Color.white.value
                        else:
                            selected_ip = ip
                            server_btn_list[index].color = Color.green.value

                    return f

                server_btn_list.append(EdgeButton(
                    (0, 100 + 50 * index),
                    (width // 2, 50),
                    callback(index, ip),
                    name + ": " + ip,
                    fonts[3],
                    Color.white.value,
                    5,
                    1,
                ))
                server_btn_list[-1].activate()

        if connecting and not interface.is_connecting():
            connecting = False
            connect_btn.text = String.connect.value
            connect_btn.color = Color.white.value
            if interface.get_opposite() is None:
                for server_btn in server_btn_list:
                    server_btn.kill()
                server_btn_list = []

        if not interface.is_connected():
            ready_btn.color = Color.white.value

        screen.fill((0, 0, 0))
        Drawable.spread_draw(screen)

        screen.blit(
            fonts[3].render("me: " + interface.get_name(), True, Color.white.value),
            (width // 2, height - 170)
        )
        opposite = interface.get_opposite()
        if opposite is None:
            opposite = "Peer is not connected."
        else:
            opposite = "peer: " + opposite
        screen.blit(
            fonts[3].render(opposite, True, Color.white.value),
            (width // 2, height - 140)
        )

        text_high = 10
        for index, (name, chat) in enumerate(interface.get_chatlist()[-10:]):
            text = fonts[3].render(name + ": " + chat, True, Color.white.value)
            screen.blit(
                text,
                (width // 2 + 10, text_high)
            )
            text_high += text.get_height() + 10
        pygame.draw.rect(screen, Color.white.value, (width // 2, 0, width // 2, 350), 1)

        pygame.display.update()

        clock.tick(fps)

    ready_btn.kill()
    connect_btn.kill()
    scan_btn.kill()
    for server_btn in server_btn_list:
        server_btn.kill()


if __name__ == "__main__":
    pygame.init()
    interface = LobbyInterface("me")
    screen = pygame.display.set_mode((600, 600))
    lobby_loop(screen, interface)
