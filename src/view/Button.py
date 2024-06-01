import pygame
from abc import ABC, abstractmethod
from src.util.custom_type import Point, Matrix


class Button(ABC):
    buttons: set['Button'] = set()

    @staticmethod
    def spread_click(pos: Point) -> None:
        """
        모든 버튼에 클릭 이벤트를 전파한다.
        :param pos: 마우스가 클릭된 위치
        """
        for button in Button.buttons:
            if button.clickable and button.rect.collidepoint(pos):
                button.click()

    @staticmethod
    def spread_draw(screen: pygame.Surface) -> None:
        """
        모든 버튼을 화면에 그린다.
        :param screen: 화면 객체
        """
        for button in Button.buttons:
            if button.drawable:
                button.draw(screen)

    @staticmethod
    def spread_size(size: Point) -> None:
        """
        모든 버튼에 변경된 화면 사이즈를 전파한다.
        :param size: 변경된 화면 사이즈
        """
        for button in Button.buttons:
            button.size(size)

    def __init__(self, point: Point, size: Point):
        """
        버튼 인터페이스
        :param point: 시작점
        :param size: 크기
        """
        self.rect = pygame.rect.Rect(*point, *size)
        self.clickable = False
        self.drawable = False
        Button.buttons.add(self)

    def kill(self) -> None:
        """
        버튼을 삭제한다.
        """
        self.clickable = False
        self.drawable = False
        Button.buttons.remove(self)

    @abstractmethod
    def click(self) -> None:
        """
        클릭되었을 때의 행동을 정의하여야 한다.
        """
        pass

    @abstractmethod
    def draw(self, screen: pygame.Surface) -> None:
        """
        버튼을 그리는 방법을 정의하여야 한다.
        :param screen: 화면 객체
        """
        pass

    @abstractmethod
    def size(self, size: Point) -> None:
        """
        화면 사이즈 변경시 행동을 정의하여야 한다.
        :param size: 변경된 화면 사이즈
        """
        pass


class TextButton(Button, ABC):
    def __init__(self,
                 point: Point,
                 size: Point,
                 text: str,
                 font: pygame.font.Font,
                 color: tuple[int, int, int, int]):
        """
        텍스트 버튼
        :param point: 시작점
        :param size: 크기
        :param text: 표시할 텍스트
        :param font: 폰트
        :param color: 글자 색
        """
        super().__init__(point, size)
        self.text = text
        self.font = font
        self.color = color


class EdgeButton(TextButton, ABC):
    def __init__(self,
                 point: Point,
                 size: Point,
                 text: str,
                 font: pygame.font.Font,
                 color: tuple[int, int, int, int],
                 thickness: int):
        """
        테두리 텍스트 버튼
        :param point: 시작점
        :param size: 크기
        :param text: 표시할 텍스트
        :param font: 폰트
        :param color: 글자 색
        :param thickness: 테두리 굵기
        """
        super().__init__(point, size, text, font, color)
        self.thickness = thickness

    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, self.color, self.rect, self.thickness)
        screen.blit(self.font.render(self.text, True, self.color), self.rect)


class ImageButton(Button, ABC):
    def __init__(self,
                 point: Point,
                 size: Point,
                 image: pygame.Surface):
        """
        이미지 버튼
        :param point: 시작점
        :param size: 크기
        :param image: 이미지
        """
        super().__init__(point, size)
        self.image = image

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.image, self.rect)
