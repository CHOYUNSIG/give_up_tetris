from abc import ABC, abstractmethod
import pygame
from src.util.custom_type import Point
from typing import Callable


class Button(ABC):
    buttons: set['Button'] = set()

    @staticmethod
    def spread_click(pos: Point) -> None:
        """
        모든 버튼에 클릭 이벤트를 전파한다.
        :param pos: 마우스가 클릭된 위치
        """
        for button in Button.buttons.copy():
            if button._clickable and button._rect.collidepoint(pos):
                button.click()

    @staticmethod
    def spread_draw(screen: pygame.Surface) -> None:
        """
        모든 버튼을 화면에 그린다.
        :param screen: 화면 객체
        """
        for button in Button.buttons:
            if button._drawable:
                button.draw(screen)

    def __init__(self, point: Point, size: Point, callback: Callable[[], None]):
        """
        버튼 인터페이스
        :param point: 시작점
        :param size: 크기
        """
        self._rect = pygame.rect.Rect(*point, *size)
        self._clickable = False
        self._drawable = False
        self._callback = callback
        Button.buttons.add(self)

    def activate(self) -> None:
        self._clickable = True
        self._drawable = True

    def kill(self) -> None:
        """
        버튼을 삭제한다.
        """
        self._clickable = False
        self._drawable = False
        Button.buttons.remove(self)

    def click(self) -> None:
        """
        클릭되었을 때의 행동을 정의한다.
        """
        self._callback()

    @abstractmethod
    def draw(self, screen: pygame.Surface) -> None:
        """
        버튼을 그리는 방법을 정의하여야 한다.
        :param screen: 화면 객체
        """
        pass


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
        self._text = text
        self._font = font
        self._color = color

    def draw(self, screen: pygame.Surface) -> None:
        text = self._font.render(self._text, True, self._color)
        text_center = text.get_rect().center
        real_center = self._rect.center
        move = (real_center[0] - text_center[0], real_center[1] - text_center[1])
        screen.blit(self._font.render(self._text, True, self._color), move)

    def change_text(self, text: str) -> None:
        self._text = text

    def change_color(self, color: tuple[int, int, int]):
        self._color = color


class EdgeButton(TextButton):
    def __init__(self,
                 point: Point,
                 size: Point,
                 callback: Callable[[], None],
                 text: str,
                 font: pygame.font.Font,
                 color: tuple[int, int, int],
                 thickness: int):
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
        self._thickness = thickness

    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, self._color, self._rect, self._thickness)
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
        screen.blit(self.image, self._rect)
