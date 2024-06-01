import socket
from abc import ABC, abstractmethod
from enum import IntEnum, unique
from pickle import dumps, loads
from queue import Queue
from threading import Thread, Lock
from typing import Type, Callable, TypeVar, Final
from time import sleep


@unique
class MessageType(IntEnum):
    """
    메시지의 타입을 정의한 열거형
    """
    pass


MT = TypeVar("MT", bound=MessageType)
Message = tuple[MT, any]  # 메시지의 정의


class PairSocket(ABC):
    def __init__(self, name: str):
        """
        양방향 메시지 비동기 버퍼링 소켓
        """
        self._name: Final[str] = name
        self._opposite_name: str | None = None
        self._socket: socket.socket | None = None
        self._message_queue: Queue[Message] = Queue()
        self._handler_map: dict[MT, Callable[[Message], None]] = {}
        self._lock = Lock()

        def socket_handler() -> None:
            self._lock.acquire()
            self._socket.send(dumps((-1, self._name)))
            self._lock.release()
            try:
                while True:
                    packet = self._socket.recv(1024)
                    if len(packet) == 0:
                        break
                    msg: Message = loads(packet)
                    msgtype, body = msg
                    self._lock.acquire()
                    if msgtype in self._handler_map:
                        self._handler_map[msgtype](body)
                    elif msgtype == -1:  # 소개
                        self._opposite_name = body
                    else:
                        self._message_queue.put(msg)
                    self._lock.release()
            except OSError:
                try:
                    self._lock.release()
                except RuntimeError:
                    pass
            finally:
                self._lock.acquire()
                self._socket.close()
                self._socket = None
                self._opposite_name = None
                self._lock.release()

        self._message_handler = socket_handler

    @abstractmethod
    def start(self, ip: str, port: int) -> None:
        """
        소켓을 시작한다.
        :param ip: IP 주소
        :param port: 포트 번호
        """
        pass

    def get_name(self) -> str:
        return self._name

    def get_opposite(self) -> str | None:
        """
        소켓이 연결된 상태인지를 확인한다. 연결되어있다면 연결 상대의 이름을 반환한다.
        :return: 연결되었다면 상대의 이름을, 그렇지 않으면 None을 반환한다.
        """
        sleep(0)
        self._lock.acquire()
        opposite = self._opposite_name
        self._lock.release()
        return opposite

    def take(self) -> Message | None:
        """
        메시지 큐에서 메시지를 꺼낸다.
        :return: 메시지가 있으면 메시지를, 없으면 None을 반환한다.
        """
        if self._message_queue.empty():
            return None
        return self._message_queue.get()

    def send(self, msg: Message) -> bool:
        """
        메시지를 보낸다
        :param msg: 메시지 객체
        :return: 메시지를 보내는 데 성공하면 True, 그렇지 않으면 False를 반환한다.
        """
        try:
            sleep(0)
            self._lock.acquire()
            self._socket.send(dumps(msg))
            return True
        except OSError:
            return False
        finally:
            self._lock.release()

    def enroll_handler(self, msgtype: Type[MT], handler: Callable[[Message], None]) -> None:
        """
        메시지 핸들러를 등록한다.
        :param msgtype: 메시지 타입
        :param handler: 핸들러 함수
        """
        sleep(0)
        self._lock.acquire()
        self._handler_map[msgtype] = handler
        self._lock.release()


PS = TypeVar("PS", bound=PairSocket)


class PairClientSocket(PairSocket):
    def __init__(self, name: str):
        """
        쿨라이언트 소켓
        """
        super().__init__(name)
        self.__connecting = False

    def start(self, ip: str, port: int, timeout: float = 1 / 60) -> None:
        """
        클라이언트 소켓을 시작한다.
        :param ip: IP 주소
        :param port: 포트 번호
        :param timeout: 연결 설정 시간
        """
        sleep(0)
        self._lock.acquire()
        connecting = self.__connecting
        self._lock.release()
        connecting |= self.get_opposite() is not None
        if connecting:
            return
        self._lock.acquire()
        self.__connecting = True
        self._lock.release()

        def connect() -> None:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2 ** 20)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2 ** 20)
                sock.settimeout(timeout)
                sock.connect((ip, port))
                sock.settimeout(None)
                self._lock.acquire()
                self._socket = sock
                self._lock.release()
                self._message_handler()
            except OSError:
                pass
            finally:
                self._lock.acquire()
                self.__connecting = False
                self._lock.release()

        Thread(target=connect, daemon=True).start()


class PairServerSocket(PairSocket):
    def __init__(self, name: str):
        """
        서버 소켓
        """
        super().__init__(name)
        self.__started = False

    def start(self, ip: str, port: int) -> None:
        """
        서버 소켓을 시작한다.
        :param ip: IP 주소
        :param port: 포트 번호
        """
        sleep(0)
        self._lock.acquire()
        started = self.__started
        self._lock.release()
        if started:
            return
        self._lock.acquire()
        self.__started = True
        self._lock.release()

        def accept() -> None:
            listner = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listner.bind((ip, port))
            listner.listen(5)
            while True:
                sock, _ = listner.accept()
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2 ** 20)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2 ** 20)
                self._lock.acquire()
                self._socket = sock
                self._lock.release()
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

    c.send((TetrisMessageType.chat, "hello"))
    while True:
        m = s.take()
        if m is not None and m[0] == TetrisMessageType.chat:
            print("server gets: " + m[1])
            break

    print("Test clear.")
