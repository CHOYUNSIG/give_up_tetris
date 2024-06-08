from abc import ABC, abstractmethod
from typing import Callable

import pygame

from src.util.custom_type import Point


class Drawable(ABC):
    drawables: set['Drawable'] = set()

    @staticmethod
    def spread_draw(screen: pygame.Surface) -> None:
        for drawable in Drawable.drawables.copy():
            if drawable._drawable:
                drawable.draw(screen)

    def __init__(self):
        self._drawable = False
        Drawable.drawables.add(self)

    def activate(self) -> None:
        self._drawable = True

    def kill(self) -> None:
        self._drawable = False
        Drawable.drawables.remove(self)

    @abstractmethod
    def draw(self, screen: pygame.Surface) -> None:
        pass


class Clickable(ABC):
    clickables: set['Clickable'] = set()

    @staticmethod
    def spread_click(mouse: Point) -> None:
        for clickable in Clickable.clickables.copy():
            if clickable._clickable and clickable.rect.collidepoint(*mouse):
                clickable.click()

    def __init__(self, point: Point, size: Point, callback: Callable[[], None]):
        self._clickable = False
        self.callback = callback
        self.rect = pygame.rect.Rect(*point, *size)
        Clickable.clickables.add(self)

    def activate(self) -> None:
        self._clickable = True

    def kill(self) -> None:
        self._clickable = False
        Clickable.clickables.remove(self)

    def click(self) -> None:
        self.callback()

