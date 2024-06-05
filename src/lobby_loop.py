import pygame
from src.module.LobbyInterface import LobbyInterface
from src.util.Button import Button, EdgeButton
from src.util.keymap import keymap
from res.string import String
from res.color import Color
from typing import Final
from time import monotonic_ns

disconnect_check_gap_ns: Final[int] = 10 ** 9


def lobby_loop(screen: pygame.Surface, interface: LobbyInterface, fps: int = 60):
    clock = pygame.time.Clock()
    width, height = screen.get_width(), screen.get_height()
    fonts = [pygame.font.SysFont(None, 10 * i) for i in range(10)]
    
    # 상태
    done = False
    chating = ""
    scanning = False
    selected_ip: str | None = None
    last_disconnect_check_time = monotonic_ns()
    
    # 버튼
    ready_btn: EdgeButton
    scan_btn: EdgeButton
    connect_btn: EdgeButton
    server_btn_list: list[EdgeButton] = []
    
    # 콜백
    def toggle_ready() -> None:
        ready = interface.toggle_ready()
        if ready:
            ready_btn.change_color(Color.green.value)
        else:
            ready_btn.change_color(Color.white.value)

    def scan() -> None:
        nonlocal scanning
        if scanning:
            return
        interface.scan_server()
        scanning = True
        scan_btn.change_text(String.scanning.value + "...")
        scan_btn.change_color(Color.lightgrey.value)

    def connect() -> None:
        if selected_ip is None:
            return
        interface.connect_server(selected_ip)

    def select_server(index: int) -> None:
        nonlocal selected_ip
        new_ip = interface.get_serverlist()[index]
        if new_ip == selected_ip:
            selected_ip = None
            server_btn_list[index].change_color(Color.white.value)
        else:
            selected_ip = new_ip
            server_btn_list[index].change_color(Color.green.value)

    # 선언
    ready_btn = EdgeButton(
        (width // 2, height - 100),
        (width // 2, 100),
        toggle_ready,
        String.ready.value,
        fonts[4],
        Color.white.value,
        3
    )

    scan_btn = EdgeButton(
        (0, 0),
        (width // 2, 100),
        scan,
        String.scan.value,
        fonts[4],
        Color.white.value,
        3
    )

    connect_btn = EdgeButton(
        (0, height - 100),
        (width // 2, 100),
        connect,
        String.connect.value,
        fonts[4],
        Color.white.value,
        3
    )

    ready_btn.activate()
    scan_btn.activate()
    connect_btn.activate()

    interface.start()

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                Button.spread_click(pygame.mouse.get_pos())
            if event.type == pygame.KEYDOWN:
                if event.key in keymap:
                    chating += keymap[event.key]
                if event.key == pygame.K_BACKSPACE and len(chating) > 0:
                    chating = chating[:-1]
                if event.key == pygame.K_RETURN:
                    interface.send_chat(chating)
                    chating = ""

        chat_list = interface.get_chatlist()
        server_list = interface.get_serverlist()

        if server_list is not None and scanning:
            scanning = False
            scan_btn.change_text(String.scan.value)
            scan_btn.change_color(Color.white.value)
            for server_btn in server_btn_list:
                server_btn.kill()
            server_btn_list = []
            for index, (name, ip) in enumerate(server_list):

                def callback() -> None:
                    nonlocal selected_ip
                    if ip == selected_ip:
                        selected_ip = None
                        server_btn_list[index].change_color(Color.white.value)
                    else:
                        selected_ip = ip
                        server_btn_list[index].change_color(Color.green.value)

                server_btn_list.append(EdgeButton(
                    (0, 100 + 50 * index),
                    (width // 2, 50),
                    callback,
                    name + "\n" + ip,
                    fonts[4],
                    Color.white.value,
                    2
                ))
                server_btn_list[-1].activate()

        screen.fill((0, 0, 0))
        Button.spread_draw(screen)
        screen.blit(
            fonts[3].render(chating, True, Color.white.value),
            (width // 2, height - 200)
        )
        text_high = 10
        for index, (name, chat) in enumerate(chat_list[-10:]):
            text = fonts[3].render(name + ": " + chat, True, Color.white.value)
            screen.blit(
                text,
                (width // 2, text_high)
            )
            text_high += text.get_height() + 10
        pygame.display.update()

        if interface.check_ready():
            break

        now = monotonic_ns()
        if now - last_disconnect_check_time > disconnect_check_gap_ns:
            interface.check_disconnect()
            last_disconnect_check_time = now

        clock.tick(fps)


if __name__ == "__main__":
    pygame.init()
    interface = LobbyInterface("me")
    screen = pygame.display.set_mode((600, 600))
    lobby_loop(screen, interface)
