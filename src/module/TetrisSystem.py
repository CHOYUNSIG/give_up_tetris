from abc import ABC, abstractmethod
from typing import TypeVar
from src.module.Tetris import Tetris
from src.network.PairSocket import Message, PairServerSocket, PairClientSocket, PS
from src.network.protocol import TetrisMessageType
from src.util.custom_type import Point, Matrix
from threading import Lock
from time import sleep


class TetrisSystem(ABC):
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
    def move_left(self, player: str) -> None:
        pass

    @abstractmethod
    def move_right(self, player: str) -> None:
        pass

    @abstractmethod
    def move_down(self, player: str) -> None:
        pass

    @abstractmethod
    def superdown(self, player: str) -> None:
        pass

    @abstractmethod
    def rotate(self, player: str) -> None:
        pass


TS = TypeVar("TS", bound=TetrisSystem)


class TetrisServerSystem(TetrisSystem):
    def __init__(self, socket: PairServerSocket):
        super().__init__(socket)
        self.__tetris = Tetris(socket.get_name(), socket.get_opposite())

        def send_data(msg: Message) -> None:
            self._lock.acquire()
            if msg[0] == TetrisMessageType.tetris_map_request:
                self._socket.send((TetrisMessageType.tetris_map, self.get_map()))
            elif msg[0] == TetrisMessageType.score_request:
                self._socket.send((TetrisMessageType.score, self.get_score()))
            elif msg[0] == TetrisMessageType.queue_request:
                self._socket.send((TetrisMessageType.queue, self.get_queue()))
            elif msg[0] == TetrisMessageType.player_pos_request:
                self._socket.send((TetrisMessageType.player_pos, (msg[1], self.get_position(msg[1]))))
            self._lock.release()

        def recv_ctrl(msg: Message) -> None:
            self._lock.acquire()
            for ctrl, callback in [
                ("move_left", self.__tetris.move_left),
                ("move_right", self.__tetris.move_right),
                ("move_down", self.__tetris.move_down),
                ("superdown", self.__tetris.superdown),
                ("rotate", self.__tetris.rotate),
            ]:
                if msg[1] == ctrl:
                    callback(self._socket.get_opposite())
                    break
            self._lock.release()

        self._socket.enroll_handler(TetrisMessageType.tetris_map_request, send_data)
        self._socket.enroll_handler(TetrisMessageType.score_request, send_data)
        self._socket.enroll_handler(TetrisMessageType.queue_request, send_data)
        self._socket.enroll_handler(TetrisMessageType.player_pos_request, send_data)
        self._socket.enroll_handler(TetrisMessageType.control_key, recv_ctrl)

    def start(self) -> None:
        sleep(0)
        self._lock.acquire()
        self.__tetris.start()
        self._socket.send((TetrisMessageType.game_start, None))
        self._lock.release()

    def update(self) -> None:
        sleep(0)
        self._lock.acquire()
        pre_state = self.__tetris.get_state()
        self.__tetris.update()
        now_state = self.__tetris.get_state()
        if (pre_state, now_state) == (1, 2):
            self._socket.send((TetrisMessageType.game_ended, None))
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

    def move_left(self, player: str) -> None:
        sleep(0)
        self._lock.acquire()
        self.__tetris.move_left(player)
        self._lock.release()

    def move_right(self, player: str) -> None:
        sleep(0)
        self._lock.acquire()
        self.__tetris.move_right(player)
        self._lock.release()

    def move_down(self, player: str) -> None:
        sleep(0)
        self._lock.acquire()
        self.__tetris.move_down(player)
        self._lock.release()

    def superdown(self, player: str) -> None:
        sleep(0)
        self._lock.acquire()
        self.__tetris.superdown(player)
        self._lock.release()

    def rotate(self, player: str) -> None:
        sleep(0)
        self._lock.acquire()
        self.__tetris.rotate(player)
        self._lock.release()


class TetrisClientSystem(TetrisSystem):
    def __init__(self, socket: PairClientSocket):
        super().__init__(socket)
        self.__map: Matrix | None = None
        self.__score: int | None = None
        self.__player_pos: dict[str, list[Point]] | None = None
        self.__queue: list[Matrix] | None = None
        self.__started = False
        self.__ended = False

        def recv_data(msg: Message) -> None:
            self._lock.acquire()
            if msg[0] == TetrisMessageType.tetris_map:
                self.__map = msg[1]
            elif msg[0] == TetrisMessageType.score:
                self.__score = msg[1]
            elif msg[0] == TetrisMessageType.player_pos:
                player, pos = msg[1]
                if self.__player_pos is None:
                    self.__player_pos = {}
                self.__player_pos[player] = msg[1]
            elif msg[0] == TetrisMessageType.queue:
                self.__queue = msg[1]
            self._lock.release()

        def recv_gamestate(msg: Message) -> None:
            self._lock.acquire()
            if msg[0] == TetrisMessageType.game_start:
                self.__started = True
            elif msg[0] == TetrisMessageType.game_ended:
                self.__ended = True
            self._lock.release()

        self._socket.enroll_handler(TetrisMessageType.tetris_map, recv_data)
        self._socket.enroll_handler(TetrisMessageType.score, recv_data)
        self._socket.enroll_handler(TetrisMessageType.queue, recv_data)
        self._socket.enroll_handler(TetrisMessageType.player_pos, recv_data)
        self._socket.enroll_handler(TetrisMessageType.game_start, recv_gamestate)
        self._socket.enroll_handler(TetrisMessageType.game_ended, recv_gamestate)

    def start(self) -> None:
        pass

    def update(self) -> None:
        sleep(0)
        self._lock.acquire()
        self._socket.send((TetrisMessageType.tetris_map_request, None))
        self._socket.send((TetrisMessageType.score_request, None))
        self._socket.send((TetrisMessageType.queue_request, None))
        self._socket.send((TetrisMessageType.player_pos_request, self._socket.get_opposite()))
        self._socket.send((TetrisMessageType.player_pos_request, self._socket.get_name()))
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
        sleep(0)
        self._lock.acquire()
        result = self.__map
        self._lock.release()
        return result

    def get_score(self) -> int:
        sleep(0)
        self._lock.acquire()
        result = self.__score
        self._lock.release()
        return result

    def get_queue(self) -> list[Matrix]:
        sleep(0)
        self._lock.acquire()
        result = self.__queue
        self._lock.release()
        return result

    def get_position(self, player: str) -> list[Point]:
        sleep(0)
        self._lock.acquire()
        result = self.__player_pos[player]
        self._lock.release()
        return result

    def move_left(self, player: str) -> None:
        sleep(0)
        self._lock.acquire()
        self._socket.send((TetrisMessageType.control_key, "move_left"))
        self._lock.release()

    def move_right(self, player: str) -> None:
        sleep(0)
        self._lock.acquire()
        self._socket.send((TetrisMessageType.control_key, "move_right"))
        self._lock.release()

    def move_down(self, player: str) -> None:
        sleep(0)
        self._lock.acquire()
        self._socket.send((TetrisMessageType.control_key, "move_down"))
        self._lock.release()

    def superdown(self, player: str) -> None:
        sleep(0)
        self._lock.acquire()
        self._socket.send((TetrisMessageType.control_key, "superdown"))
        self._lock.release()

    def rotate(self, player: str) -> None:
        sleep(0)
        self._lock.acquire()
        self._socket.send((TetrisMessageType.control_key, "rotate"))
        self._lock.release()
