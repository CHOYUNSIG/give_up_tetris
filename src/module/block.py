from time import perf_counter_ns
from copy import deepcopy
from typing import Final
from random import randrange
from collections import deque

Point = tuple[int, int]
Matrix = list[list[int]]


class TetrisMap:
    height: Final[int] = 30
    width: Final[int] = 10
    down_gap_ns: Final[int] = 10 ** 6

    def __init__(self, key_list: list[int]):
        self.map = [[0] * TetrisMap.width for _ in range(TetrisMap.height)]  # 게임판
        self.moving_blocks: dict[int: TetrisBlock] = dict()  # 현재 움직이고 있는 블록
        self.queued_blocks: dict[int: deque] = dict()  # 블록 대기열
        for key in key_list:
            self.queued_blocks[key] = deque()
            self.queue_block(key)
        self.score = 0  # 점수
        self.end = False
    
    def update(self) -> bool:
        """
        게임판의 상태를 변경한다. 매 프레임마다 호출되어야 하는 함수이다.
        :return: 게임 판이 더 이상 진행되지 못하면 False를 반환한다.
        """
        if self.end:
            return False

        now = perf_counter_ns()

        # 시간이 된 블록 아래로 이동
        for key, block in self.moving_blocks.copy().items():
            if now - block.created_time < TetrisMap.down_gap_ns:
                continue
            new_block = block.move((1, 0))
            if self.confirm_block(key, new_block):
                self.moving_blocks[key] = new_block
            else:  # 다 내려왔을 경우
                self.fix_block(key)
                if not self.pop_block(key):
                    return False

        # 완성된 줄 제거
        for i in range(TetrisMap.height):
            if all(self.map[i]):
                self.map.pop(i)
                self.map.insert(0, [0] * TetrisMap.width)
                self.score += 100

        return True
    
    def get_map(self) -> list[list[int]]:
        """
        현재 게임판 상태를 반환한다.
        :return: int 자료형의 2차원 리스트
        """
        result = deepcopy(self.map)
        for key, block in self.moving_blocks.items():
            for x, y in block.get_position():
                result[x][y] = key
        return result

    def queue_block(self, key: int) -> None:
        """
        대기열에 블록을 7개 추가한다.
        :param key: 플레이어를 구분자
        """
        pass

    def pop_block(self, key: int) -> bool:
        """
        대기열에 있는 블록을 판 위로 하나 가져온다.
        :param key: 플레이어를 구분자
        :return: 블록을 가져왔으면 True, 블록이 꽉 차 놓을 수 없으면 False를 반환한다.
        """
        pass

    def fix_block(self, key: int) -> None:
        """
        블록을 현재 위치에 고정한다.
        :param key: 플레이어를 구분자
        """
        block = self.moving_blocks[key]
        for x, y in block.get_position():
            self.map[x][y] = block.color

    def rotate_block(self, key: int, clockwise: bool) -> bool:
        """
        블록을 회전한다.
        :param key: 플레이어를 구분자
        :param clockwise: 시계 방향이면 True, 반대 방향이면 False
        :return: 블록 회전에 성공하면 True, 그렇지 않으면 False를 반환한다.
        """
        pass
    
    def move_block(self, key: int, mov: Point) -> bool:
        """
        블록을 움직인다.
        :param key: 플레이어를 구분자
        :param mov: 블록을 움직이는 정도를 표현하는 벡터이다.
        :return: 블록 이동에 성공하면 True, 그렇지 않으면 False,를 반환한다.
        """
        pass

    def superdown_block(self, key: int) -> bool:
        """
        블록을 최대한 아래로 내리고 고정한다.
        :param key: 플레이어를 구분자
        :return: 최대한 아래로 내릴 수 있으면 True, 다른 블록에 의해 막혀 있으면 False를 반환한다.
        """
        pass

    def confirm_block(self, key: int, block: 'TetrisBlock') -> bool:
        """
        현재 게임판 상태에서 주어진 블록이 위치할 수 있는지를 확인한다.
        :param key: 플레이어를 구분자
        :param block: TetrisBlock 객체
        :return: 블록을 놓을 수 있으면 True, 그렇지 않으면 False를 반환한다.
        """
        if not all(
            map(
                lambda p: 0 <= p[0] < TetrisMap.height and 0 <= p[1] < TetrisMap.width and not self.map[p[0]][p[1]],
                block.get_position()
            )
        ):
            return False
        for another_key, another_block in self.moving_blocks.items():
            if another_key != key and another_block.collide(block):
                return False
        return True


class TetrisBlock:
    general_form: Final[list[Matrix]] = [
        [
            [0, 1, 0, 0],
            [0, 1, 0, 0],
            [0, 1, 0, 0],
            [0, 1, 0, 0],
        ],
        [
            [0, 0, 0, 0],
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
        ],
        [
            [0, 0, 0, 0],
            [0, 1, 1, 0],
            [1, 1, 0, 0],
            [0, 0, 0, 0],
        ],
        [
            [0, 0, 0, 0],
            [0, 1, 1, 0],
            [0, 0, 1, 1],
            [0, 0, 0, 0],
        ],
        [
            [0, 0, 0, 0],
            [1, 1, 1, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 0],
        ],
        [
            [0, 0, 0, 0],
            [0, 1, 1, 1],
            [0, 1, 0, 0],
            [0, 0, 0, 0],
        ],
        [
            [0, 0, 0, 0],
            [1, 1, 1, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 0],
        ],
    ]

    def __init__(self, pos: Point, color: int or None = None, form: Matrix or None = None):
        self.created_time = perf_counter_ns()
        self.color = color
        self.form = deepcopy(form)
        if self.color is None:
            self.color = randrange(7) + 1
        if self.form is None:
            self.form = deepcopy(TetrisBlock.general_form[self.color - 1])
        self.pos = pos

    def get_position(self) -> list[Point]:
        """
        블록의 위치를 반환한다.
        :return: 튜플로 표현된 점이 담긴 길이 4의 리스트
        """
        result = []
        for i in range(4):
            for j in range(4):
                if self.form[i][j]:
                    result.append((self.pos[0] + i, self.pos[1] + j))
        return result

    def rotate(self, clockwise: bool) -> 'TetrisBlock':
        """
        돌아간 블록을 반환한다.
        :param clockwise: 시계 방향이면 True, 아니면 False
        :return: 새로운 블록 객체
        """
        new_form = [[0] * 4 for _ in range(4)]
        for i in range(4):
            for j in range(4):
                if clockwise:
                    new_form[i][j] = self.form[3 - j][i]
                else:
                    new_form[i][j] = self.form[j][3 - i]
        return TetrisBlock(self.pos, self.color, new_form)

    def move(self, amount: Point) -> 'TetrisBlock':
        """
        이동한 블록을 반환한다.
        :param amount: 블록을 움직일 벡터
        :return: 새로운 블록 객체
        """
        return TetrisBlock((self.pos[0] + amount[0], self.pos[1] + amount[1]), self.color, self.form)

    def collide(self, other: 'TetrisBlock') -> bool:
        """
        다른 블록과 충돌 중인지를 반환한다.
        :param other: 다른 블록 객체
        :return: 충돌 중이면 True, 아니면 False를 반환한다.
        """
        point = self.get_position()
        return any(map(lambda p: p in point, other.get_position()))
