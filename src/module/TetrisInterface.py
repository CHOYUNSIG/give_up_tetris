from abc import ABC, abstractmethod
from typing import TypeVar, Final
from src.module.Tetris import Tetris
from src.network.PairSocket import Message, PairServerSocket, PairClientSocket, PS
from src.network.protocol import TetrisMessageType as Tmt
from src.util.custom_type import Point, Matrix
from threading import Lock
from time import sleep


class TetrisInterface(ABC):
    def __init__(self, socket: PS):
        self._socket = socket
        self._lock = Lock()

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def update(self) -> None:
        pass

    @abstractmethod
    def get_state(self) -> int:
        pass

    @abstractmethod
    def get_map(self) -> Matrix:
        pass

    @abstractmethod
    def get_score(self) -> int:
        pass

    @abstractmethod
    def get_queue(self) -> list[Matrix]:
        pass

    @abstractmethod
    def get_position(self, player: str) -> list[Point]:
        pass

    @abstractmethod
    def move_left(self) -> None:
        pass

    @abstractmethod
    def move_right(self) -> None:
        pass

    @abstractmethod
    def move_down(self) -> None:
        pass

    @abstractmethod
    def superdown(self) -> None:
        pass

    @abstractmethod
    def rotate(self) -> None:
        pass


TI = TypeVar("TI", bound=TetrisInterface)


class TetrisServerInterface(TetrisInterface):
    def __init__(self, socket: PairServerSocket):
        super().__init__(socket)
        self.__opposite: Final[str] = socket.get_opposite()
        self.__ended = False
        self.__tetris = Tetris(socket.get_name(), self.__opposite)

        def send_data(msg: Message) -> Message:
            if msg[0] == Tmt.map_req:
                return Tmt.map, self.get_map()
            if msg[0] == Tmt.score_req:
                return Tmt.score, self.get_score()
            if msg[0] == Tmt.queue_req:
                return Tmt.queue, self.get_queue()
            if msg[0] == Tmt.pos_req:
                return Tmt.pos, (msg[1], self.get_position(msg[1]))
            if msg[0] == Tmt.all_req:
                response = {}
                self._lock.acquire()
                response[Tmt.map] = self.__tetris.get_map()
                response[Tmt.score] = self.__tetris.get_score()
                response[Tmt.queue] = self.__tetris.get_queue()
                response[Tmt.pos] = {
                    self._socket.get_name(): self.__tetris.get_position(self._socket.get_name()),
                    self.__opposite: self.__tetris.get_position(self.__opposite),
                }
                self._lock.release()
                return Tmt.all, response

        def recv_ctrl(msg: Message) -> Message:
            for ctrl, callback in [
                ("move_left", self.__tetris.move_left),
                ("move_right", self.__tetris.move_right),
                ("move_down", self.__tetris.move_down),
                ("superdown", self.__tetris.superdown),
                ("rotate", self.__tetris.rotate),
            ]:
                if msg[1] == ctrl:
                    self._lock.acquire()
                    callback(self.__opposite)
                    self._lock.release()
                    return Tmt.ctrlkey_r, None

        self._socket.enroll(Tmt.map_req, send_data)
        self._socket.enroll(Tmt.score_req, send_data)
        self._socket.enroll(Tmt.queue_req, send_data)
        self._socket.enroll(Tmt.pos_req, send_data)
        self._socket.enroll(Tmt.ctrlkey, recv_ctrl)
        self._socket.enroll(Tmt.all_req, send_data)

    def start(self) -> None:
        sleep(0)
        self._lock.acquire()
        self.__tetris.start()
        self._lock.release()
        while not self._socket.request((Tmt.mdchngd, None), Tmt.mdchngd_r)[1]:
            continue
        self._socket.request((Tmt.start, None), Tmt.start_r)

    def update(self) -> None:
        sleep(0)
        self._lock.acquire()
        self.__tetris.update()
        if self.__tetris.get_state() == 2 and not self.__ended:
            self.__ended = True
            self._socket.request((Tmt.ended, None), Tmt.ended_r)
        self._lock.release()

    def get_state(self) -> int:
        sleep(0)
        self._lock.acquire()
        result = self.__tetris.get_state()
        self._lock.release()
        return result

    def get_map(self) -> Matrix:
        sleep(0)
        self._lock.acquire()
        result = self.__tetris.get_map()
        self._lock.release()
        return result

    def get_score(self) -> int:
        sleep(0)
        self._lock.acquire()
        result = self.__tetris.get_score()
        self._lock.release()
        return result

    def get_queue(self) -> list[Matrix]:
        sleep(0)
        self._lock.acquire()
        result = self.__tetris.get_queue()
        self._lock.release()
        return result

    def get_position(self, player: str) -> list[Point]:
        sleep(0)
        self._lock.acquire()
        result = self.__tetris.get_position(player)
        self._lock.release()
        return result

    def move_left(self) -> None:
        sleep(0)
        self._lock.acquire()
        self.__tetris.move_left(self._socket.get_name())
        self._lock.release()

    def move_right(self) -> None:
        sleep(0)
        self._lock.acquire()
        self.__tetris.move_right(self._socket.get_name())
        self._lock.release()

    def move_down(self) -> None:
        sleep(0)
        self._lock.acquire()
        self.__tetris.move_down(self._socket.get_name())
        self._lock.release()

    def superdown(self) -> None:
        sleep(0)
        self._lock.acquire()
        self.__tetris.superdown(self._socket.get_name())
        self._lock.release()

    def rotate(self) -> None:
        sleep(0)
        self._lock.acquire()
        self.__tetris.rotate(self._socket.get_name())
        self._lock.release()


class TetrisClientInterface(TetrisInterface):
    def __init__(self, socket: PairClientSocket):
        super().__init__(socket)
        self.__map: Matrix = []
        self.__score: int = 0
        self.__player_pos: dict[str, list[Point]] = {
            self._socket.get_name(): [],
            self._socket.get_opposite(): [],
        }
        self.__queue: list[Matrix] = []
        self.__started = False
        self.__ended = False

        def ready(msg: Message) -> Message:
            return Tmt.mdchngd_r, True

        def recv_gamestate(msg: Message) -> Message:
            self._lock.acquire()
            if msg[0] == Tmt.start:
                self.__started = True
                self._lock.release()
                return Tmt.start_r, None
            elif msg[0] == Tmt.ended:
                self.__ended = True
                self._lock.release()
                return Tmt.ended_r, None

        self._socket.enroll(Tmt.start, recv_gamestate)
        self._socket.enroll(Tmt.ended, recv_gamestate)
        self._socket.enroll(Tmt.mdchngd, ready)

    def start(self) -> None:
        self.update()

    def update(self) -> None:
        response = self._socket.request((Tmt.all_req, None), Tmt.all)[1]
        sleep(0)
        self._lock.acquire()
        self.__map = response[Tmt.map]
        self.__score = response[Tmt.score]
        self.__queue = response[Tmt.queue]
        self.__player_pos = response[Tmt.pos]
        self._lock.release()

    def get_state(self) -> int:
        sleep(0)
        self._lock.acquire()
        started = self.__started
        ended = self.__ended
        self._lock.release()
        if not started:
            return 0
        elif not ended:
            return 1
        else:
            return 2

    def get_map(self) -> Matrix:
        return self.__map

    def get_score(self) -> int:
        return self.__score

    def get_queue(self) -> list[Matrix]:
        return self.__queue

    def get_position(self, player: str) -> list[Point]:
        return self.__player_pos[player]

    def move_left(self) -> None:
        self._socket.request((Tmt.ctrlkey, "move_left"), Tmt.ctrlkey_r)

    def move_right(self) -> None:
        self._socket.request((Tmt.ctrlkey, "move_right"), Tmt.ctrlkey_r)

    def move_down(self) -> None:
        self._socket.request((Tmt.ctrlkey, "move_down"), Tmt.ctrlkey_r)

    def superdown(self) -> None:
        self._socket.request((Tmt.ctrlkey, "superdown"), Tmt.ctrlkey_r)

    def rotate(self) -> None:
        self._socket.request((Tmt.ctrlkey, "rotate"), Tmt.ctrlkey_r)
