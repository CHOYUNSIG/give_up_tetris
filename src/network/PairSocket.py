import socket
from abc import *
from enum import IntEnum, unique
from pickle import dumps, loads
from queue import Queue
from threading import Thread
from typing import Type


@unique
class MessageType(IntEnum):
    """
    메시지의 타입을 정의한 열거형
    """
    pass


Message = tuple[Type[MessageType], any]  # 메시지의 정의


class PairSocket(metaclass=ABCMeta):
    def __init__(self):
        """
        양방향 메시지 비동기 버퍼링 소켓
        """
        self._socket: socket.socket | None = None
        self._message_queue: Queue[Message] = Queue()

        def recv_handler() -> None:
            try:
                while True:
                    msg = self._socket.recv(1024)
                    if len(msg) == 0:
                        break
                    self._message_queue.put(loads(msg))
            except OSError:
                pass
            finally:
                self._socket.close()
                self._socket = None

        self._message_handler = recv_handler

    @abstractmethod
    def start(self, ip: str, port: int) -> None:
        """
        소켓을 시작한다.
        :param ip: IP 주소
        :param port: 포트 번호
        """
        pass

    def is_connected(self) -> bool:
        """
        소켓이 연결된 상태인지를 확인한다.
        :return: 연결되었다면 True, 그렇지 않으면 False를 반환한다.
        """
        return self._socket is not None

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
            self._socket.send(dumps(msg))
            return True
        except OSError:
            return False


class PairClientSocket(PairSocket):
    def __init__(self):
        """
        쿨라이언트 소켓
        """
        super().__init__()
        self.__connecting = False

    def start(self, ip: str, port: int, timeout: float = 0.5) -> None:
        """
        클라이언트 소켓을 시작한다.
        :param ip: IP 주소
        :param port: 포트 번호
        :param timeout: 연결 설정 시간
        """
        if self.__connecting or self.is_connected():
            return
        self.__connecting = True

        def connect() -> None:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                sock.connect((ip, port))
                self._socket = sock
                self._message_handler()
            except OSError:
                pass
            finally:
                self.__connecting = False

        Thread(target=connect, daemon=True).start()


class PairServerSocket(PairSocket):
    def __init__(self):
        """
        서버 소켓
        """
        super().__init__()
        self.__started = False

    def start(self, ip: str, port: int) -> None:
        """
        서버 소켓을 시작한다.
        :param ip: IP 주소
        :param port: 포트 번호
        """
        if self.__started:
            return
        self.__started = True

        def accept() -> None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind((ip, port))
            sock.listen(5)
            while True:
                self._socket, _ = sock.accept()
                self._message_handler()

        Thread(target=accept, daemon=True).start()


if __name__ == "__main__":
    from time import sleep
    from src.network.TetrisProtocol import tetris_port
    from src.network.ServerScanner import ServerScanner
    from src.network.TetrisProtocol import TetrisMessageType

    s = PairServerSocket()
    s.start('0.0.0.0', tetris_port)
    print("Server started.")

    sleep(1)

    scan = ServerScanner()
    scan.scan(tetris_port)
    a = []
    while True:
        a = scan.get_server_list()
        if a:
            print(f'Server scaned at : {a[0]}')
            break
        sleep(0.5)

    sleep(1)

    c = PairClientSocket()
    c.start(a[0][0], a[0][1])
    while True:
        if c.is_connected() and s.is_connected():
            print("Client connected.")
            break
        sleep(0.5)

    c.send((TetrisMessageType.chat, "hello"))
    while True:
        m = s.take()
        if m is not None and m[0] == TetrisMessageType.chat:
            print("server gets: " + m[1])
            break
        sleep(0.5)

    print("Test clear.")
