import socket
from abc import ABC, abstractmethod
from enum import IntEnum, unique
from pickle import dumps, loads
from threading import Thread, Lock
from time import sleep
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
    def __init__(self, name: str):
        """
        요청-응답 형식의 스레드 안정성 소켓
        """
        self._name: Final[str] = name
        self._socket: socket.socket | None = None
        self._handler_map: dict[MTI, Callable[[Message], Message]] = {}
        self.__response: dict[MTI, Message] = {}
        self._lock = Lock()

        def introduce(msg: Message) -> Message:
            self._opposite_name = msg[1]
            return -2, self._name

        self._handler_map[-1] = introduce

        def receive() -> None:
            try:
                while True:
                    packet = self._socket.recv(4096)
                    if len(packet) == 0:
                        break
                    msg: Message = loads(packet)
                    msgtype, body = msg
                    self._lock.acquire()
                    if msgtype in self._handler_map:  # 요청 메시지일 시
                        self._socket.send(dumps(self._handler_map[msgtype](msg)))
                    else:  # 응답 메시지일 시
                        self.__response[msgtype] = msg
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
                self._lock.release()

        self._message_handler = receive

    @abstractmethod
    def start(self, ip: str, port: int) -> None:
        """
        소켓을 시작한다.
        :param ip: IP 주소
        :param port: 포트 번호
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
        result = self.request((-1, None), -2)
        if result is None:
            return None
        return result[1]

    def request(self, msg: Message, response_type: MTI) -> Message | None:
        """
        메시지를 보내고 응답을 받은 뒤 반환한다.
        :param msg: 메시지 객체
        :param response_type: 응답 형식
        :return: 응답 메시지 객체
        """
        try:
            self._lock.acquire()
            self._socket.send(dumps(msg))
            self._lock.release()
            while True:
                self._lock.acquire()
                if response_type in self.__response:
                    result = self.__response[response_type]
                    self.__response.pop(response_type)
                    return result
                self._lock.release()
        except (OSError, AttributeError):
            return None
        finally:
            try:
                self._lock.release()
            except RuntimeError:
                pass

    def enroll(self, msgtype: Type[MTI], handler: Callable[[Message], Message]) -> None:
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

    def echo(msg: Message) -> Message:
        return msg
    s.enroll(TetrisMessageType.chat, echo)

    m = c.request((TetrisMessageType.chat, "hello"), TetrisMessageType.chat_r)
    print("server gets: " + m[1])
    print("Test clear.")
