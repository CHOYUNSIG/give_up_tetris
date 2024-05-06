import pygame
from abc import *
from custom_type import *


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
