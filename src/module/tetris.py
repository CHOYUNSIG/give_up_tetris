from time import monotonic_ns
from copy import deepcopy
from typing import Final
from random import randrange, shuffle
from math import cos, sin, pi
from collections import deque
from src.module.custom_type import *


class TetrisMap:
    """
    테트리스 게임 판
    """
    height: Final[int] = 30
    spawn_height: Final[int] = 6
    width: Final[int] = 10
    min_queue_size: Final[int] = 3

    def __init__(self, key_list: list[int]):
        self.map = [[0] * TetrisMap.width for _ in range(TetrisMap.height)]  # 게임판, 이 게임판은 항상 무결함이 보장되어야 한다.
        self.moving_blocks: dict[int, TetrisBlock or None] = dict()  # 현재 움직이고 있는 블록, 이 블록은 항상 무결함이 보장되어야 한다.
        self.queued_blocks: dict[int, deque[TetrisBlock]] = dict()  # 블록 대기열
        for key in key_list:
            self.moving_blocks[key] = None
            self.queued_blocks[key] = deque()
            self.queue_block(key)
            self.pop_block(key)
        self.score = 0  # 점수
        self.downgap_ns = 1 * 10 ** 9  # 블록이 내려가는 데 걸리는 시간
        self.end = False

    def __repr__(self) -> str:
        result = super().__repr__() + '\n'
        for row in self.get_map():
            for i in row:
                if i:
                    result += '■'
                else:
                    result += ' '
            result += '\n'
        return result

    def update(self) -> bool:
        """
        게임판의 상태를 변경한다. 매 프레임마다 호출되어야 하는 함수이다.
        :return: 게임 판이 더 이상 진행되지 못하면 False를 반환한다.
        """
        if self.end:
            return False
        now = monotonic_ns()
        # 시간이 된 블록 아래로 이동
        for key, block in self.moving_blocks.copy().items():
            if now - block.created_time < self.downgap_ns:
                continue
            new_block = block.move((1, 0)).copy()
            confirm = self.confirm_block(key, new_block)
            if confirm == 0:  # 내려야 하는 경우
                self.moving_blocks[key] = new_block
            elif confirm == 1 or confirm == 3:  # 다 내려왔을 경우
                self.fix_block(key)
                self.score += 100 * self.remove_line()
                if not self.pop_block(key):
                    self.end = True
                    return False
            else:  # 다른 플레이어의 블록에 막힌 경우
                self.moving_blocks[key] = block.move((0, 0))
        return True

    def get_map(self) -> list[list[int]]:
        """
        현재 게임판 상태를 반환한다.
        :return: int 자료형의 2차원 리스트
        """
        result = deepcopy(self.map)
        for key, block in self.moving_blocks.items():
            if block is None:
                continue
            for x, y in block.get_position():
                result[x][y] = block.color
        return result

    def get_score(self) -> int:
        """
        현재 점수를 반환한다.
        """
        return self.score

    def set_downgap(self, ns: int) -> None:
        """
        블록이 내려오는 시간을 조절한다.
        :param ns: 나노초 단위의 시간
        """
        self.downgap_ns = ns

    def remove_line(self) -> int:
        """
        완성된 줄을 제거한다.
        :return: 제거된 줄의 개수이다.
        """
        removed = 0
        for i in range(TetrisMap.height):
            if all(self.map[i]):
                self.map.pop(i)
                self.map.insert(0, [0] * TetrisMap.width)
                removed += 1
        return removed

    def queue_block(self, key: int) -> None:
        """
        대기열에 블록을 7개 추가한다.
        :param key: 플레이어 구분자
        """
        bag = list(range(1, 8))
        shuffle(bag)
        self.queued_blocks[key].extend(map(lambda i: TetrisBlock((0, 0), i), bag))

    def pop_block(self, key: int) -> bool:
        """
        대기열에 있는 블록을 판 위로 하나 가져온다.
        :param key: 플레이어 구분자
        :return: 블록을 가져왔으면 True, 블록이 꽉 차 놓을 수 없으면 False를 반환한다.
        """
        if self.moving_blocks[key] is not None:
            return False
        block = self.queued_blocks[key].popleft()
        if len(self.queued_blocks[key]) < TetrisMap.min_queue_size:
            self.queue_block(key)
        spot = list(range(TetrisMap.width))
        shuffle(spot)
        for s in spot:
            new_block = block.move((TetrisMap.spawn_height, s))
            if self.confirm_block(key, new_block) == 0:
                self.moving_blocks[key] = new_block
                return True
        return False

    def fix_block(self, key: int) -> bool:
        """
        블록을 현재 위치에 고정한다.
        :param key: 플레이어 구분자
        :return: 고정에 성공하면 True, 그렇지 않으면 False를 반환한다.
        """
        if self.moving_blocks[key] is None:
            return False
        block = self.moving_blocks[key]
        for x, y in block.get_position():
            self.map[x][y] = block.color
        self.moving_blocks[key] = None
        return True

    def rotate_block(self, key: int, clockwise: bool) -> bool:
        """
        블록을 회전한다.
        :param key: 플레이어 구분자
        :param clockwise: 시계 방향이면 True, 반대 방향이면 False
        :return: 블록 회전에 성공하면 True, 그렇지 않으면 False를 반환한다.
        """
        if self.moving_blocks[key] is None:
            return False
        new_block = self.moving_blocks[key].rotate(clockwise)
        if self.confirm_block(key, new_block) == 0:
            self.moving_blocks[key] = new_block
            return True
        for mov in zip((1, 1, 1, 0, 0, -1, -1, -1), (-1, 0, 1, -1, 1, -1, 0, 1)):
            mov_block = new_block.move(mov)
            if self.confirm_block(key, mov_block) == 0:
                self.moving_blocks[key] = mov_block
                return True
        return False

    def move_block(self, key: int, mov: int) -> bool:
        """
        블록을 움직인다.
        :param key: 플레이어 구분자
        :param mov: 블록을 움직이는 정도를 표현하는 수이다. 0: 오른쪽, 1: 아래, 2: 왼쪽, 3: 위
        :return: 블록 이동에 성공하면 True, 그렇지 않으면 False,를 반환한다.
        """
        if self.moving_blocks[key] is None:
            return False
        rad = mov * pi / 2
        new_block = self.moving_blocks[key].move((round(sin(rad)), round(cos(rad))))
        if mov == 1:
            new_block = new_block.copy()
        if self.confirm_block(key, new_block) == 0:
            self.moving_blocks[key] = new_block
            return True
        return False

    def superdown_block(self, key: int) -> bool:
        """
        블록을 최대한 아래로 내리고 고정한다.
        :param key: 플레이어 구분자
        :return: 최대한 아래로 내릴 수 있으면 True, 다른 블록에 의해 막혀 있으면 False를 반환한다.
        """
        if self.moving_blocks[key] is None:
            return False
        pre_block = self.moving_blocks[key]
        new_block = pre_block.move((1, 0))
        confirm = self.confirm_block(key, new_block)
        while confirm == 0:
            pre_block = new_block
            new_block = new_block.move((1, 0))
            confirm = self.confirm_block(key, new_block)
        if confirm == 1 or confirm == 3:
            self.moving_blocks[key] = pre_block
            return True
        return False

    def confirm_block(self, key: int, block: 'TetrisBlock') -> int:
        """
        현재 게임판 상태에서 주어진 블록이 위치할 수 있는지를 확인한다.
        :param key: 플레이어 구분자
        :param block: TetrisBlock 객체
        :return: 이상이 없으면 0, 맵 이탈은 1, 다른 플레이어의 블록과 겹치면 2, 이미 놓인 블록과 겹치면 3을 반환한다.
        """
        if not all(map(lambda p: 0 <= p[0] < TetrisMap.height and 0 <= p[1] < TetrisMap.width, block.get_position())):
            return 1
        if any(map(lambda d: d[0] != key and block.collide(d[1]), self.moving_blocks.items())):
            return 2
        if any(map(lambda p: self.map[p[0]][p[1]] != 0, block.get_position())):
            return 3
        return 0


class TetrisBlock:
    """
    테트리스 블록
    """
    general_form: Final[list[Matrix]] = [
        [
            [1, 1],
            [1, 1],
        ],
        [
            [0, 1, 1],
            [1, 1, 0],
            [0, 0, 0],
        ],
        [
            [1, 1, 0],
            [0, 1, 1],
            [0, 0, 0],
        ],
        [
            [1, 0, 0],
            [1, 1, 1],
            [0, 0, 0],
        ],
        [
            [0, 0, 1],
            [1, 1, 1],
            [0, 0, 0],
        ],
        [
            [0, 1, 0],
            [1, 1, 1],
            [0, 0, 0],
        ],
        [
            [0, 0, 0, 0],
            [1, 1, 1, 1],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ],
    ]

    def __init__(self, pos: Point, color: int or None = None, form: Matrix or None = None, created_time: int or None = None):
        if color is None:
            color = randrange(7) + 1
        if form is None:
            form = TetrisBlock.general_form[color - 1]
        if created_time is None:
            created_time = monotonic_ns()
        self.pos: Final[Point] = pos
        self.created_time: Final[int] = created_time
        self.color: Final[int] = color
        self.form: Final[Matrix] = deepcopy(form)

    def get_position(self) -> list[Point]:
        """
        블록의 위치를 반환한다.
        :return: 튜플로 표현된 점이 담긴 길이 4의 리스트
        """
        result = []
        for i in range(len(self.form)):
            for j in range(len(self.form[i])):
                if self.form[i][j]:
                    result.append((self.pos[0] + i, self.pos[1] + j))
        return result

    def rotate(self, clockwise: bool) -> 'TetrisBlock':
        """
        돌아간 블록을 반환한다.
        :param clockwise: 시계 방향이면 True, 아니면 False
        :return: 새로운 블록 객체
        """
        new_form = [[0] * len(self.form[i]) for i in range(len(self.form))]
        for i in range(len(self.form)):
            for j in range(len(self.form[i])):
                if clockwise:
                    new_form[i][j] = self.form[- 1 - j][i]
                else:
                    new_form[i][j] = self.form[j][- 1 - i]
        return TetrisBlock(self.pos, self.color, new_form, self.created_time)

    def move(self, amount: Point) -> 'TetrisBlock':
        """
        이동한 블록을 반환한다.
        :param amount: 블록을 움직일 벡터
        :return: 새로운 블록 객체
        """
        return TetrisBlock((self.pos[0] + amount[0], self.pos[1] + amount[1]), self.color, self.form, self.created_time)

    def copy(self) -> 'TetrisBlock':
        """
        블록을 복사한다.
        :return: 새로운 블록 객체
        """
        return TetrisBlock(self.pos, self.color, self.form)

    def collide(self, other: 'TetrisBlock') -> bool:
        """
        다른 블록과 충돌 중인지를 반환한다.
        :param other: 다른 블록 객체
        :return: 충돌 중이면 True, 아니면 False를 반환한다.
        """
        point = self.get_position()
        return any(map(lambda p: p in point, other.get_position()))


if __name__ == "__main__":
    player = [0]
    tetris = TetrisMap(player)
    w = 20

    import pygame
    pygame.init()
    screen = pygame.display.set_mode((600, 600))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 50)
    done = False

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    tetris.move_block(player[0], 2)
                if event.key == pygame.K_RIGHT:
                    tetris.move_block(player[0], 0)
                if event.key == pygame.K_UP:
                    tetris.rotate_block(player[0], True)
                if event.key == pygame.K_DOWN:
                    tetris.move_block(player[0], 1)
                if event.key == pygame.K_SPACE:
                    tetris.superdown_block(player[0])

        tetris.update()
        m = tetris.get_map()
        tetris.set_downgap(round(1000 / (1000 + tetris.get_score()) * 10 ** 9))

        screen.fill(pygame.Color(0, 0, 0))
        for i in range(len(m)):
            for j in range(len(m[i])):
                if m[i][j]:
                    pygame.draw.rect(screen, (255, 255, 255), (j * w, i * w, w, w))
        screen.blit(font.render(str(tetris.get_score()), True, (255, 255, 255)), (300, 300))
        pygame.display.update()

        clock.tick(60)
