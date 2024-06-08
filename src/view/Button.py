from abc import ABCMeta
from typing import Callable

import pygame

from src.util.custom_type import Point
from src.view.widget import Drawable, Clickable


class Button(Drawable, Clickable, metaclass=ABCMeta):
    def __init__(self, point: Point, size: Point, callback: Callable[[], None]):
        """
        버튼 클래스
        :param point: 시작점
        :param size: 크기
        """
        Drawable.__init__(self)
        Clickable.__init__(self, point, size, callback)

    def activate(self) -> None:
        Drawable.activate(self)
        Clickable.activate(self)

    def kill(self) -> None:
        Drawable.kill(self)
        Clickable.kill(self)


class TextButton(Button):
    def __init__(self,
                 point: Point,
                 size: Point,
                 callback: Callable[[], None],
                 text: str,
                 font: pygame.font.Font,
                 color: tuple[int, int, int]):
        """
        텍스트 버튼
        :param point: 시작점
        :param size: 크기
        :param callback: 버튼이 클릭되었을 때의 행동
        :param text: 표시할 텍스트
        :param font: 폰트
        :param color: 글자 색
        """
        super().__init__(point, size, callback)
        self.text = text
        self.color = color
        self.font = font

    def draw(self, screen: pygame.Surface) -> None:
        text = self.font.render(self.text, True, self.color)
        text_center = text.get_rect().center
        real_center = self.rect.center
        screen.blit(text, (real_center[0] - text_center[0], real_center[1] - text_center[1]))

    def change_text(self, text: str) -> None:
        self.text = text

    def change_color(self, color: tuple[int, int, int]):
        self.color = color


class EdgeButton(TextButton):
    def __init__(self,
                 point: Point,
                 size: Point,
                 callback: Callable[[], None],
                 text: str,
                 font: pygame.font.Font,
                 color: tuple[int, int, int],
                 padding: int = 10,
                 thickness: int = 3):
        """
        테두리 텍스트 버튼
        :param point: 시작점
        :param size: 크기
        :param callback: 버튼이 클릭되었을 때의 행동
        :param text: 표시할 텍스트
        :param font: 폰트
        :param color: 글자 색
        :param thickness: 테두리 굵기
        """
        super().__init__(point, size, callback, text, font, color)
        self.padding = padding
        self.thickness = thickness

    def draw(self, screen: pygame.Surface) -> None:
        rect = (self.rect.topleft[0] + self.padding, self.rect.topleft[1] + self.padding, self.rect.width - 2 * self.padding, self.rect.height - 2 * self.padding)
        pygame.draw.rect(screen, self.color, rect, self.thickness)
        super().draw(screen)


class ImageButton(Button):
    def __init__(self,
                 point: Point,
                 size: Point,
                 callback: Callable[[], None],
                 image: pygame.Surface):
        """
        이미지 버튼
        :param point: 시작점
        :param size: 크기
        :param callback: 버튼이 클릭되었을 때의 행동
        :param image: 이미지
        """
        super().__init__(point, size, callback)
        self.image = image

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.image, self.rect)
