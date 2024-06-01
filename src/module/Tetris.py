from collections import deque
from copy import deepcopy
from math import cos, sin, pi
from random import randrange, shuffle
from time import monotonic_ns
from typing import Final

from src.util.custom_type import *


class Tetris:
    def __init__(self, *player_list: str):
        """
        테트리스 API 모듈
        :param player_list: 플레이어 목록
        """
        self.__players = { player: key for key, player in enumerate(player_list) }
        self.__tetris = TetrisMap(list(self.__players.values()), 3)
        self.__downgap_ns = 1 * 10 ** 9
        self.__score = 0
        self.__started = False
        self.__ended = False

    def update(self) -> None:
        """
        매 프레임마다 호출되는 함수이다.
        """
        if not self.__started or self.__ended:
            return
        # 내려갈 시간이 된 블록 내리기
        for key in self.__players.values():
            if self.__tetris.get_hangtime(key) < self.__downgap_ns:
                continue
            err = self.__tetris.move_block(key, 1)
            if err in (1, 3):
                line = self.__tetris.fix_remove_pop(key)
                if line is None:
                    self.end()
                    return
                self.__score += 100 * line
        # 내려가는 시간 조절
        self.__downgap_ns = round(1000 * 10 ** 9 / (1000 + self.__score))

    def start(self) -> None:
        """
        게임을 시작한다.
        """
        self.__started = True

    def end(self) -> None:
        """
        게임을 끝낸다.
        """
        self.__ended = True

    def get_state(self) -> int:
        """
        게임의 진행 상태를 반환한다.
        :return: 게임 시작 전이면 0, 진행 중이면 1, 끝났으면 2를 반환한다.
        """
        if not self.__started:
            return 0
        elif not self.__ended:
            return 1
        else:
            return 2

    def get_map(self) -> Matrix:
        """
        게임 맵 상대를 얻어온다.
        :return: 2차원 int 자료형의 리스트이다.
        """
        return self.__tetris.get_map()

    def get_score(self) -> int:
        """
        현재 점수를 얻는다.
        :return: 현재 점수이다.
        """
        return self.__score

    def get_queue(self) -> list[Matrix]:
        """
        현재 대기 큐 상태를 얻는다.
        :return: 블록을 표현하는 행렬을 담은 리스트이다.
        """
        return self.__tetris.get_queue()

    def get_position(self, player: str) -> list[Point]:
        """
        현재 플레이어가 조종하고 있는 블록의 위치를 얻는다.
        :param player: 플레이어 이름
        :return: 블록의 좌표를 담은 리스트이다.
        """
        return self.__tetris.get_position(self.__players[player])

    def move_left(self, player: str) -> None:
        """
        블록을 왼쪽으로 이동한다.
        :param player: 플레이어 이름
        """
        if not self.__started or self.__ended:
            return
        self.__tetris.move_block(self.__players[player], 2)

    def move_right(self, player: str) -> None:
        """
        블록을 오른쪽으로 이동한다.
        :param player: 플레이어 이름
        """
        if not self.__started or self.__ended:
            return
        self.__tetris.move_block(self.__players[player], 0)

    def move_down(self, player: str) -> None:
        """
        블록을 아래쪽으로 이동한다.
        :param player: 플레이어 이름
        """
        if not self.__started or self.__ended:
            return
        self.__tetris.move_block(self.__players[player], 1)

    def superdown(self, player: str) -> None:
        """
        블록을 슈퍼다운한다.
        :param player: 플레이어 이름
        """
        if not self.__started or self.__ended:
            return
        err = self.__tetris.superdown_block(self.__players[player])
        if err in (1, 3):
            line = self.__tetris.fix_remove_pop(self.__players[player])
            if line is None:
                self.end()
                return
            self.__score += 100 * line

    def rotate(self, player: str) -> None:
        """
        블록을 회전한다.
        :param player: 플레이어 이름
        """
        if not self.__started or self.__ended:
            return
        self.__tetris.rotate_block(self.__players[player], True)


class TetrisMap:
    height: Final[int] = 30
    spawn_height: Final[int] = 6
    width: Final[int] = 10

    def __init__(self, key_list: list[int], min_queue_size: int):
        """
        테트리스 게임 판
        :param key_list: 풀레이어 구분자 리스트
        :param min_queue_size: 블록 대기 큐의 최소 사이즈
        """
        self.min_queue_size: Final[int] = min_queue_size
        self.__map: Matrix = [[0] * TetrisMap.width for _ in range(TetrisMap.height)]  # 게임판
        self.__moving_blocks: dict[int, TetrisBlock | None] = { key: None for key in key_list }  # 현재 움직이고 있는 블록
        self.__queue: deque[TetrisBlock] = deque()  # 블록 대기열
        for key in key_list:
            self.fix_remove_pop(key)

    def get_map(self) -> Matrix:
        """
        현재 게임판 상태를 반환한다.
        :return: int 자료형의 2차원 리스트이다.
        """
        result = deepcopy(self.__map)
        for key, block in self.__moving_blocks.items():
            if block is None:
                continue
            for x, y in block.get_position():
                result[x][y] = block.color
        return result

    def get_position(self, key: int) -> list[Point]:
        """
        현재 판에서 플레이어가 조종 중인 블록의 위치를 반환한다.
        :param key: 플레이어 식별자
        :return: 플레이어가 조종 중인 블록의 좌표 리스트이다.
        """
        return self.__moving_blocks[key].get_position()

    def get_hangtime(self, key: int) -> int:
        """
        플레이어가 조종 중인 블록의 현재 체공 유지 시간을 반환한다.
        :param key: 플레이어 식별자
        :return: 나노초 단위의 체공 유지 시간이다.
        """
        return monotonic_ns() - self.__moving_blocks[key].created_time

    def get_queue(self) -> list[Matrix]:
        """
        블록 대기 큐에 있는 블록 현황을 반환한다.
        :return: 블록을 나타내는 행렬을 담은 리스트이다.
        """
        return list(map(lambda b: deepcopy(b.form), self.__queue))

    def fix_remove_pop(self, key: int) -> int | None:
        """
        플레이어가 조종 중인 블록을 현재 위치에 고정하고 대기 큐에서 새로운 블록을 가져와 통제를 넘긴다.
        :param key: 플레이어 구분자
        :return: 정상적으로 종료되면 사라진 줄의 개수를, 그렇지 않으면 None을 반환한다.
        """
        if self.__moving_blocks[key] is not None:
            for x, y in self.__moving_blocks[key].get_position():
                self.__map[x][y] = self.__moving_blocks[key].color
        removed = 0
        for i in range(TetrisMap.height):
            if all(self.__map[i]):
                self.__map.pop(i)
                self.__map.insert(0, [0] * TetrisMap.width)
                removed += 1
        while len(self.__queue) <= self.min_queue_size:
            bag = list(range(1, 8))
            shuffle(bag)
            self.__queue.extend(map(lambda i: TetrisBlock((0, 0), i), bag))
        block = self.__queue.popleft()
        spot = list(range(TetrisMap.width))
        shuffle(spot)
        for s in spot:
            new_block = block.move((TetrisMap.spawn_height, s))
            if self.__confirm_block(key, new_block) == 0:
                self.__moving_blocks[key] = new_block.copy()
                return removed
        return None

    def rotate_block(self, key: int, clockwise: bool) -> bool:
        """
        플레이어가 조종 중인 블록을 회전한다.
        :param key: 플레이어 구분자
        :param clockwise: 시계 방향이면 True, 반대 방향이면 False
        :return: 블록 회전에 성공하면 True, 그렇지 않으면 False를 반환한다.
        """
        new_block = self.__moving_blocks[key].rotate(clockwise)
        if self.__confirm_block(key, new_block) == 0:
            self.__moving_blocks[key] = new_block
            return True
        for mov in zip((1, 1, 1, 0, 0, -1, -1, -1), (-1, 0, 1, -1, 1, -1, 0, 1)):
            mov_block = new_block.move(mov)
            if self.__confirm_block(key, mov_block) == 0:
                self.__moving_blocks[key] = mov_block
                return True
        return False

    def move_block(self, key: int, mov: int) -> int:
        """
        플레이어가 조종 중인 블록을 움직인다.
        :param key: 플레이어 구분자
        :param mov: 블록을 움직이는 정도를 표현하는 수이다. 0은 오른쪽, 1은 아래, 2는 왼쪽, 3은 위
        :return: 성공은 0, 맵 이탈에 의한 실패는 1, 다른 플레이어의 블록에 의한 실패는 2, 이미 놓은 블록에 의한 실패는 3을 반환한다.
        """
        rad = mov * pi / 2
        new_block = self.__moving_blocks[key].move((round(sin(rad)), round(cos(rad))))
        if mov == 1:
            new_block = new_block.copy()
        confirm = self.__confirm_block(key, new_block)
        if confirm == 0:
            self.__moving_blocks[key] = new_block
        return confirm

    def superdown_block(self, key: int) -> int:
        """
        플레이어가 조종 중인 블록을 최대한 아래로 내린다.
        :param key: 플레이어 구분자
        :return: 맵 이탈에 의한 멈춤은 1, 다른 플레이어의 블록에 의한 멈춤은 2, 이미 놓은 블록에 의한 멈춤은 3을 반환한다.
        """
        pre_block = self.__moving_blocks[key]
        new_block = pre_block.move((1, 0))
        confirm = self.__confirm_block(key, new_block)
        while confirm == 0:
            pre_block = new_block
            new_block = new_block.move((1, 0))
            confirm = self.__confirm_block(key, new_block)
        self.__moving_blocks[key] = pre_block.copy()
        return confirm

    def __confirm_block(self, key: int, block: 'TetrisBlock') -> int:
        """
        현재 게임판 상태에서 주어진 블록이 위치할 수 있는지를 확인한다.
        :param key: 플레이어 구분자
        :param block: TetrisBlock 객체
        :return: 이상이 없으면 0, 맵 이탈은 1, 다른 플레이어의 블록과 겹치면 2, 이미 놓인 블록과 겹치면 3을 반환한다.
        """
        if not all(map(lambda p: 0 <= p[0] < TetrisMap.height and 0 <= p[1] < TetrisMap.width, block.get_position())):
            return 1
        if any(map(lambda d: d[0] != key and d[1] is not None and block.collide(d[1]), self.__moving_blocks.items())):
            return 2
        if any(map(lambda p: self.__map[p[0]][p[1]] != 0, block.get_position())):
            return 3
        return 0


class TetrisBlock:
    general_form: Final[list[Matrix]] = [
        [
            [0],
        ],
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

    def __init__(self,
                 pos: Point,
                 color: int or None = None,
                 form: Matrix or None = None,
                 created_time: int or None = None):
        """
        테트리스 블록
        :param pos: 생성 위치
        :param color: 색상 구분자
        :param form: 블록 위상을 나타내는 행렬
        :param created_time: 시스템 상의 생성 시간
        """
        if color is None:
            color = randrange(1, len(TetrisBlock.general_form))
        if form is None:
            form = TetrisBlock.general_form[color]
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
    import pygame

    pygame.init()

    w = 20
    screen = pygame.display.set_mode((600, 600))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 50)

    player = {
        "choyunsig": (
        pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_SPACE, pygame.Color(255, 0, 0)),
        "kim": (pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s, pygame.K_LSHIFT, pygame.Color(0, 255, 0)),
    }

    block_color = {
        1: pygame.Color(255, 255, 127),
        2: pygame.Color(127, 255, 127),
        3: pygame.Color(255, 127, 127),
        4: pygame.Color(127, 127, 255),
        5: pygame.Color(255, 191, 127),
        6: pygame.Color(255, 127, 255),
        7: pygame.Color(127, 255, 255),
    }

    tetris = Tetris(*player.keys())
    tetris.start()
    done = False

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.KEYDOWN:
                for p, key in player.items():
                    if event.key == key[0]:
                        tetris.move_left(p)
                    if event.key == key[1]:
                        tetris.move_right(p)
                    if event.key == key[2]:
                        tetris.rotate(p)
                    if event.key == key[3]:
                        tetris.move_down(p)
                    if event.key == key[4]:
                        tetris.superdown(p)

        tetris.update()
        m = tetris.get_map()

        screen.fill(pygame.Color(50, 50, 50))
        pygame.draw.rect(screen, (0, 0, 0), (0, 0, w * 10, w * 30))
        for p, color in player.items():
            for i, j in tetris.get_position(p):
                pygame.draw.rect(screen, color[5], (j * w - 2, i * w - 2, w + 4, w + 4))
        for i in range(len(m)):
            for j in range(len(m[i])):
                if m[i][j]:
                    pygame.draw.rect(screen, block_color[m[i][j]], (j * w, i * w, w, w))
        screen.blit(font.render("Score: %d" % tetris.get_score(), True, (255, 255, 255)), (300, 300))
        if tetris.get_state() == 2:
            screen.blit(font.render("Game Over", True, (255, 255, 255)), (300, 350))
        pygame.display.update()

        clock.tick(60)
