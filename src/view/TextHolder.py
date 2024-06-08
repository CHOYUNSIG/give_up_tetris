import pygame

from src.util.custom_type import Point
from src.view.widget import Drawable
from src.view.Alignment import Alignment


class TextHolder(Drawable):
    def __init__(self,
                 point: Point,
                 size: Point,
                 color: tuple[int, int, int],
                 font: pygame.font.Font,
                 value: str = "",
                 align: Alignment = Alignment.center,
                 padding: int = 10,
                 thickness: int = 3):
        Drawable.__init__(self)
        self.rect = pygame.rect.Rect(*point, *size)
        self.font = font
        self.color = color
        self.value = value
        self.align = align
        self.padding = padding
        self.thickness = thickness

    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, self.color, self.rect, self.thickness)
        text = self.font.render(self.value, True, self.color)
        move = []
        for rect in (self.rect, text.get_rect()):
            p = [rect.topleft, rect.center, rect.bottomright]
            x = p[self.align.value % 3][0]
            y = p[self.align.value // 3][1]
            move.append((x, y))
        screen.blit(text, (
                move[0][0] - move[1][0] + self.padding * (1 - self.align.value % 3),
                move[0][1] - move[1][1] + self.padding * (1 - self.align.value // 3)
            )
        )
