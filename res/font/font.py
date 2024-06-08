import pygame
import os

pygame.init()

fonts = [pygame.font.Font(os.path.dirname(os.path.abspath(__file__)) + "/D2Coding-Ver1.3.2-20180524.ttf", 6 * i) for i in range(10)]
