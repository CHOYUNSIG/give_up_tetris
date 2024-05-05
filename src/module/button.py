import pygame
from abc import *


class Button(pygame.sprite.Sprite, metaclass=ABCMeta):
    buttons: set['Button'] = set()

    @staticmethod
    def spread_click(pos: tuple[int, int]):
        for button in Button.buttons:
            if button.rect.collidepoint(pos):
                button.click()

    def __init__(self, point: tuple[int, int], size: tuple[int, int], *groups: pygame.sprite.Group):
        self.rect: pygame.rect.Rect = pygame.rect.Rect(*point, *size)
        Button.buttons.add(self)
        super().__init__(*groups)

    def kill(self):
        Button.buttons.remove(self)
        pygame.sprite.Sprite.kill(self)

    @abstractmethod
    def click(self):
        pass
