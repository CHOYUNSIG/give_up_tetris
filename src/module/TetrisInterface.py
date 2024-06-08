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
        self.__opposite: Final[str] = socket.get_opposite()

    def get_name(self) -> str:
        return self._socket.get_name()

    def get_opposite(self) -> str:
        return self.__opposite

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
        self.__ended = False
        self.__tetris = Tetris(socket.get_name(), self.get_opposite())

        def send_data(msg: Message) -> Message:
            with self._lock:
                if msg[0] == Tmt.map_req:
                    return Tmt.map, self.get_map()
                if msg[0] == Tmt.score_req:
                    return Tmt.score, self.get_score()
                if msg[0] == Tmt.queue_req:
                    return Tmt.queue, self.get_queue()
                if msg[0] == Tmt.pos_req:
                    return Tmt.pos, (msg[1], self.get_position(msg[1]))
                if msg[0] == Tmt.all_req:
                    return Tmt.all, {
                        Tmt.map: self.__tetris.get_map(),
                        Tmt.score: self.__tetris.get_score(),
                        Tmt.queue: self.__tetris.get_queue(),
                        Tmt.pos: {
                            self._socket.get_name(): self.__tetris.get_position(self._socket.get_name()),
                            self._socket.get_opposite(): self.__tetris.get_position(self._socket.get_opposite()),
                        }
                    }

        def recv_ctrl(msg: Message) -> Message:
            for ctrl, callback in [
                ("move_left", self.__tetris.move_left),
                ("move_right", self.__tetris.move_right),
                ("move_down", self.__tetris.move_down),
                ("superdown", self.__tetris.superdown),
                ("rotate", self.__tetris.rotate),
            ]:
                if msg[1] == ctrl:
                    with self._lock:
                        callback(self.get_opposite())
                    return Tmt.ctrlkey_r, None

        self._socket.enroll(Tmt.map_req, send_data)
        self._socket.enroll(Tmt.score_req, send_data)
        self._socket.enroll(Tmt.queue_req, send_data)
        self._socket.enroll(Tmt.pos_req, send_data)
        self._socket.enroll(Tmt.ctrlkey, recv_ctrl)
        self._socket.enroll(Tmt.all_req, send_data)

    def start(self) -> None:
        sleep(0)
        with self._lock:
            self.__tetris.start()
        while not self._socket.request((Tmt.mdchngd, None), Tmt.mdchngd_r)[1]:
            continue
        self._socket.request((Tmt.start, None), Tmt.start_r)

    def update(self) -> None:
        sleep(0)
        with self._lock:
            self.__tetris.update()
            if self.__tetris.get_state() == 2 and not self.__ended:
                self.__ended = True
                self._socket.request((Tmt.ended, None), Tmt.ended_r)

    def get_state(self) -> int:
        sleep(0)
        with self._lock:
            return self.__tetris.get_state()

    def get_map(self) -> Matrix:
        sleep(0)
        with self._lock:
            return self.__tetris.get_map()

    def get_score(self) -> int:
        sleep(0)
        with self._lock:
            return self.__tetris.get_score()

    def get_queue(self) -> list[Matrix]:
        sleep(0)
        with self._lock:
            return self.__tetris.get_queue()

    def get_position(self, player: str) -> list[Point]:
        sleep(0)
        with self._lock:
            return self.__tetris.get_position(player)

    def move_left(self) -> None:
        sleep(0)
        with self._lock:
            self.__tetris.move_left(self._socket.get_name())

    def move_right(self) -> None:
        sleep(0)
        with self._lock:
            self.__tetris.move_right(self._socket.get_name())

    def move_down(self) -> None:
        sleep(0)
        with self._lock:
            self.__tetris.move_down(self._socket.get_name())

    def superdown(self) -> None:
        sleep(0)
        with self._lock:
            self.__tetris.superdown(self._socket.get_name())

    def rotate(self) -> None:
        sleep(0)
        with self._lock:
            self.__tetris.rotate(self._socket.get_name())


class TetrisClientInterface(TetrisInterface):
    def __init__(self, socket: PairClientSocket):
        super().__init__(socket)
        self.__map: Matrix = []
        self.__score: int = 0
        self.__player_pos: dict[str, list[Point]] = {
            self._socket.get_name(): [],
            self.get_opposite(): [],
        }
        self.__queue: list[Matrix] = []
        self.__started = False
        self.__ended = False

        def ready(msg: Message) -> Message:
            return Tmt.mdchngd_r, True

        def recv_gamestate(msg: Message) -> Message:
            with self._lock:
                if msg[0] == Tmt.start:
                    self.__started = True
                    return Tmt.start_r, None
                elif msg[0] == Tmt.ended:
                    self.__ended = True
                    return Tmt.ended_r, None

        self._socket.enroll(Tmt.start, recv_gamestate)
        self._socket.enroll(Tmt.ended, recv_gamestate)
        self._socket.enroll(Tmt.mdchngd, ready)

    def start(self) -> None:
        while True:
            with self._lock:
                if self.__started:
                    break
        self.update()

    def update(self) -> None:
        response = self._socket.request((Tmt.all_req, None), Tmt.all)[1]
        sleep(0)
        with self._lock:
            self.__map = response[Tmt.map]
            self.__score = response[Tmt.score]
            self.__queue = response[Tmt.queue]
            self.__player_pos = response[Tmt.pos]

    def get_state(self) -> int:
        sleep(0)
        with self._lock:
            if not self.__started:
                return 0
            elif not self.__ended:
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
