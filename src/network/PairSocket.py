import socket
from abc import ABC, abstractmethod
from enum import IntEnum, unique
from pickle import dumps, loads
from threading import Thread, Lock, Semaphore
from typing import Type, Callable, TypeVar, Final


@unique
class MessageType(IntEnum):
    """
    메시지의 타입을 정의한 열거형
    메시지 타입은 반드시 요청과 응답 쌍을 가지고 있어야 한다.
    """
    pass


MT = TypeVar("MT", bound=MessageType)
MTI = MT | int
Message = tuple[MTI, any]  # 메시지의 정의


class PairSocket(ABC):
    def __init__(self, name: str, on_disconnected: Callable[[], None] | None = None):
        """
        요청-응답 형식의 스레드 안정성 소켓
        """
        self._name: Final[str] = name
        self._opposite_name: str | None = None
        self._socket: socket.socket | None = None
        self._handler_map: dict[MTI, Callable[[Message], Message]] = {}
        self._lock = Lock()
        self.__response: dict[MTI, Message] = {}

        def introduce(msg: Message) -> Message:
            self._opposite_name = msg[1]
            return -2, self._name

        self._handler_map[-1] = introduce

        def message_handler() -> None:
            with self._lock:
                self._socket.send(dumps((-1, self._name)))
            try:
                while True:
                    packet = self._socket.recv(4096)
                    if len(packet) == 0:
                        break
                    msg: Message = loads(packet)
                    handler: Callable[[Message], Message] | None = None
                    with self._lock:
                        if msg[0] in self._handler_map:  # 요청 메시지일 시
                            handler = self._handler_map[msg[0]]
                        else:  # 응답 메시지일 시
                            self.__response[msg[0]] = msg
                    if handler is not None:

                        def send_thread(h: Callable[[Message], Message]) -> None:
                            response = h(msg)
                            with self._lock:
                                self._socket.send(dumps(response))

                        Thread(target=send_thread, args=(handler,), daemon=True).start()
            except OSError:
                pass
            finally:
                with self._lock:
                    self._socket.close()
                    self._socket = None
                    self._opposite_name = None
                if on_disconnected is not None:
                    on_disconnected()

        self._message_handler = message_handler

    @abstractmethod
    def start(self, ip: str, port: int, sem: Semaphore | None = None) -> None:
        """
        소켓을 시작한다.
        :param ip: IP 주소
        :param port: 포트 번호
        :param sem: 서버 시작을 기다리기 위한 잠금
        """
        pass

    def get_name(self) -> str:
        """
        자신의 이름을 반환한다.
        :return: 이름
        """
        return self._name

    def get_opposite(self) -> str | None:
        """
        연결 상대의 이름을 반환한다.
        :return: 연결되었다면 상대의 이름을, 그렇지 않으면 None을 반환한다.
        """
        return self._opposite_name

    def is_connected(self) -> bool:
        """
        연결되어있는지를 확인한다.
        :return: 연결되어있다면 True, 그렇지 않으면 False를 반환한다.
        """
        return self._socket is not None

    def request(self, msg: Message, response_type: MTI) -> Message | None:
        """
        메시지를 보내고 응답을 받은 뒤 반환한다.
        :param msg: 메시지 객체
        :param response_type: 응답 형식
        :return: 응답 메시지 객체
        """
        try:
            with self._lock:
                self._socket.send(dumps(msg))
            while True:
                with self._lock:
                    if response_type in self.__response:
                        return self.__response.pop(response_type)
        except (OSError, AttributeError):
            return None

    def enroll(self, msgtype: Type[MTI], handler: Callable[[Message], Message]) -> None:
        """
        메시지 핸들러를 등록한다.
        :param msgtype: 메시지 타입
        :param handler: 핸들러 함수
        """
        with self._lock:
            self._handler_map[msgtype] = handler

    def kill(self) -> None:
        with self._lock:
            if self._socket is not None:
                self._socket.close()


PS = TypeVar("PS", bound=PairSocket)


class PairClientSocket(PairSocket):
    def __init__(self, name: str, on_disconnected: Callable[[], None] | None = None):
        """
        쿨라이언트 소켓
        """
        super().__init__(name, on_disconnected)
        self.__connecting = False

    def start(self, ip: str, port: int, sem: Semaphore | None = None) -> None:
        with self._lock:
            connecting = self.__connecting
        connecting |= self.get_opposite() is not None
        if connecting:
            return
        with self._lock:
            self.__connecting = True
        if sem is not None:
            sem.release()

        def connect() -> None:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2 ** 20)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2 ** 20)
                sock.settimeout(1)
                sock.connect((ip, port))
                sock.settimeout(None)
                with self._lock:
                    self.__connecting = False
                    self._socket = sock
                self._message_handler()
            except OSError:
                pass
            finally:
                with self._lock:
                    self.__connecting = False
                    self._socket = None

        Thread(target=connect, daemon=True).start()

    def is_connecting(self) -> bool:
        """
        소켓이 연결 중인지를 확인한다.
        :return: 연결 중이면 True, 그렇지 않으면 False를 반환한다.
        """
        with self._lock:
            return self.__connecting


class PairServerSocket(PairSocket):
    def __init__(self, name: str, on_disconnected: Callable[[], None] | None = None):
        """
        서버 소켓
        """
        super().__init__(name, on_disconnected)
        self.__started = False

    def start(self, ip: str, port: int, sem: Semaphore | None = None) -> None:
        with self._lock:
            started = self.__started
        if started:
            return
        with self._lock:
            self.__started = True
        if sem is not None:
            sem.release()

        def accept() -> None:
            listner = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listner.bind((ip, port))
            listner.listen(5)
            while True:
                sock, _ = listner.accept()
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2 ** 20)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2 ** 20)
                sock.settimeout(None)
                with self._lock:
                    self._socket = sock
                self._message_handler()

        Thread(target=accept, daemon=True).start()


if __name__ == "__main__":
    from src.network.protocol import tetris_port
    from src.network.ServerScanner import ServerScanner
    from src.network.protocol import TetrisMessageType

    s = PairServerSocket("server")
    s.start('0.0.0.0', tetris_port)
    print("Server started.")

    scan = ServerScanner()
    scan.scan(tetris_port)
    a = []
    while True:
        a = scan.get_server_list()
        if a:
            print(f'Server scaned at : {a[0]}')
            break

    c = PairClientSocket("client")
    c.start(a[0][0], a[0][1])
    while True:
        if None not in (c.get_opposite(), s.get_opposite()):
            print("Client connected.")
            break

    def echo(msg: Message) -> Message:
        return TetrisMessageType.chat_r, msg[1]
    s.enroll(TetrisMessageType.chat, echo)

    m = c.request((TetrisMessageType.chat, "hello"), TetrisMessageType.chat_r)
    print("server gets: " + m[1])
    print("Test clear.")
