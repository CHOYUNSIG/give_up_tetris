from enum import Enum


class Color(Enum):
    red = (255, 0, 0)
    green = (0, 255, 0)
    blue = (0, 0, 255)
    white = (255, 255, 255)
    black = (0, 0, 0)
    lightgrey = (200, 200, 200)

    game_bg = (50, 50, 50)

    my_egde = red
    peer_edge = green

    blocks: dict = {
        1: (255, 255, 127),
        2: (127, 255, 127),
        3: (255, 127, 127),
        4: (127, 127, 255),
        5: (255, 191, 127),
        6: (255, 127, 255),
        7: (127, 255, 255),
    }
