from src.network.PairSocket import PS, PairServerSocket, PairClientSocket, Message
from src.network.protocol import tetris_port, TetrisMessageType as Tmt
from src.network.ServerScanner import ServerScanner
from typing import Final
from threading import Lock
from collections import deque


class LobbyInterface:
    def __init__(self, socket_or_name: str | PS, chat_bufsize: int = 100):
        if type(socket_or_name) is str:
            self.__socket: PS = PairServerSocket(socket_or_name)
            self.__name = socket_or_name
        elif type(socket_or_name) is PS:
            self.__socket: PS = socket_or_name
            self.__name = socket_or_name.get_name()
        self.__lock = Lock()
        self.__is_server = isinstance(self.__socket, PairServerSocket)
        self.__chat_bufsize: Final[int] = chat_bufsize
        self.__chatlist: deque[tuple[str, str]] = deque()
        self.__ready = False
        self.__opposite_ready = False
        self.__scanner = ServerScanner()
        self.__set_socket()

    def start(self) -> None:
        self.__socket.start("0.0.0.0", tetris_port)

    def scan_server(self) -> None:
        self.__scanner.scan(tetris_port)

    def get_serverlist(self) -> list[tuple[str, str]] | None:
        serverlist = self.__scanner.get_server_list()
        if serverlist is None:
            return None
        result = []
        for ip, port, name in serverlist:
            if name != self.__name:
                result.append((name, ip))
        return result

    def connect_server(self, ip: str) -> None:
        if self.__is_server:
            self.__is_server = False
            self.__socket = PairClientSocket(self.__name)
            self.__set_socket()
        self.__socket.start(ip, tetris_port)

    def get_opposite(self) -> str | None:
        return self.__socket.get_opposite()

    def get_chatlist(self) -> list[tuple[str, str]]:
        self.__lock.acquire()
        result = list(self.__chatlist)
        self.__lock.release()
        return result

    def send_chat(self, chat: str) -> None:
        self.__add_chat(self.__name, chat)
        if self.__socket.get_opposite() is None:
            return
        self.__socket.request((Tmt.chat, chat), Tmt.chat_r)

    def toggle_ready(self, force: bool | None = None) -> bool:
        pre = self.__ready
        if force is not None:
            self.__ready = force
        else:
            self.__ready = not self.__ready
        if self.__ready and not pre:
            self.__socket.request((Tmt.ready, None), Tmt.ready_r)
        elif not self.__ready and pre:
            self.__socket.request((Tmt.busy, None), Tmt.busy_r)
        return self.__ready

    def check_ready(self) -> bool:
        self.__lock.acquire()
        result = self.__ready and self.__opposite_ready
        self.__lock.release()
        return result

    def check_connect(self) -> bool:
        opposite = self.__socket.get_opposite()
        if opposite is not None:
            return True
        if not self.__is_server and opposite is None:
            self.__is_server = True
            self.__ready = False
            self.__opposite_ready = False
            self.__socket = PairServerSocket(self.__name)
            self.__set_socket()
        return False

    def get_socket(self) -> tuple[PS, bool]:
        return self.__socket, self.__is_server

    def __add_chat(self, name: str, chat: str) -> None:
        self.__lock.acquire()
        self.__chatlist.append((name, chat))
        if len(self.__chatlist) > self.__chat_bufsize:
            self.__chatlist.popleft()
        self.__lock.release()

    def __set_socket(self) -> None:
        def recv_chat(msg: Message) -> Message:
            self.__add_chat(self.__socket.get_opposite(), msg[1])
            return Tmt.chat_r, None

        def ready_or_not(msg: Message) -> Message:
            self.__lock.acquire()
            if msg[0] == Tmt.ready:
                self.__opposite_ready = True
                self.__lock.release()
                return Tmt.ready_r, None
            if msg[0] == Tmt.busy:
                self.__opposite_ready = False
                self.__lock.release()
                return Tmt.busy_r, None

        if not self.__is_server:
            def not_ready(msg: Message) -> Message:
                return Tmt.mdchngd_r, False

            self.__socket.enroll(Tmt.mdchngd, not_ready)

        self.__socket.enroll(Tmt.chat, recv_chat)
        self.__socket.enroll(Tmt.ready, ready_or_not)
        self.__socket.enroll(Tmt.busy, ready_or_not)
