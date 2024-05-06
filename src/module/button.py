import pygame
from abc import *
from src.module.custom_type import *


class Button(pygame.sprite.Sprite, metaclass=ABCMeta):
    """
    Pygame 스프라이트 버튼 클래스
    """
    buttons: set['Button'] = set()

    @staticmethod
    def spread_click(pos: Point) -> None:
        """
        모든 버튼에 클릭 이벤트를 전파한다.
        :param pos: 마우스가 클릭된 위치
        """
        for button in Button.buttons:
            if button.rect.collidepoint(pos):
                button.click()

    @staticmethod
    def spread_draw(screen: pygame.Surface) -> None:
        """
        모든 버튼을 화면에 그린다.
        :param screen: 화면 객체
        """
        for button in Button.buttons:
            button.draw(screen)

    def __init__(self, point: Point, size: Point, *groups: pygame.sprite.Group):
        self.rect: pygame.rect.Rect = pygame.rect.Rect(*point, *size)
        Button.buttons.add(self)
        super().__init__(*groups)

    def kill(self):
        Button.buttons.remove(self)
        pygame.sprite.Sprite.kill(self)

    @abstractmethod
    def click(self):
        """
        클릭되었을 때의 행동을 정의하여야 한다.
        """
        pass

    @abstractmethod
    def draw(self, screen: pygame.Surface):
        """
        버튼을 그리는 방법을 정의하여야 한다.
        :param screen: 화면 객체
        """
        pass
