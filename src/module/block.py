from time import perf_counter_ns
from copy import deepcopy
from typing import Final
from random import randrange
import pygame

Point = tuple[int, int]
Matrix = list[list[int]]


class TetrisMap:
    general_height: Final[int] = 30
    general_width: Final[int] = 10

    def __init__(self):
        self.map = [[0] * TetrisMap.general_width for _ in range(TetrisMap.general_height)]
        self.moving_blocks: dict[int: TetrisBlock] = dict()
        self.score = 0

    def update(self):
        for block in self.moving_blocks:
            block.update()
        for i in range(TetrisMap.general_height):
            if all(self.map[i]):
                self.map.pop(i)
                self.map.insert(0, [0] * TetrisMap.general_width)

    def get_map(self) -> list[list[int]]:
        result = deepcopy(self.map)
        for key, block in self.moving_blocks.items():
            for x, y in block.get_position():
                result[x][y] = key
        return result

    def create_block(self, key: int):
        pass

    def fix_block(self, key: int):
        pass

    def rotate_block(self, key: int, clockwise: bool) -> bool:
        pass

    def move_block(self, key: int, mov: Point) -> bool:
        pass

    def superdown_block(self, key: int):
        pass

    def confirm_block(self, key: int, block: 'TetrisBlock') -> bool:
        if not all(
            map(
                lambda p: 0 <= p[0] < TetrisMap.general_height and 0 <= p[1] < TetrisMap.general_width and not self.map[p[0]][p[1]],
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

    general_color: Final[list[pygame.Color]] = [
        pygame.Color(0, 255, 255),
        pygame.Color(255, 255, 0),
        pygame.Color(0, 255, 0),
        pygame.Color(255, 0, 0),
        pygame.Color(0, 0, 255),
        pygame.Color(255, 127, 0),
        pygame.Color(255, 0, 255),
    ]

    def __init__(self, pos: Point, form: Matrix or None = None, color: pygame.Color or None = None):
        self.created_time = perf_counter_ns()
        self.form = form
        self.color = color
        if self.form is None:
            i = randrange(7)
            self.form = deepcopy(TetrisBlock.general_form[i])
            self.color = deepcopy(TetrisBlock.general_color[i])
        self.pos = pos

    def update(self):
        pass

    def get_position(self) -> list[Point]:
        result = []
        for i in range(4):
            for j in range(4):
                if self.form[i][j]:
                    result.append((self.pos[0] + i, self.pos[1] + j))
        return result

    def rotate(self, clockwise: bool) -> 'TetrisBlock':
        new_form = [[0] * 4 for _ in range(4)]
        for i in range(4):
            for j in range(4):
                if clockwise:
                    new_form[i][j] = self.form[3 - j][i]
                else:
                    new_form[i][j] = self.form[j][3 - i]
        return TetrisBlock(self.pos, new_form, deepcopy(self.color))

    def move(self, amount: Point) -> 'TetrisBlock':
        return TetrisBlock((self.pos[0] + amount[0], self.pos[1] + amount[1]), deepcopy(self.form), deepcopy(self.color))

    def collide(self, other: 'TetrisBlock') -> bool:
        point = self.get_position()
        return any(map(lambda p: p in point, other.get_position()))
