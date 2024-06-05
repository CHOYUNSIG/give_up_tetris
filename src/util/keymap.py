import pygame

keymap: dict[int, str] = {}

# 문자
for i in range(26):
    keymap[pygame.K_a + i] = chr(ord('a') + i)

# 띄어쓰기
keymap[pygame.K_SPACE] = ' '

# 숫자
for i in range(10):
    keymap[pygame.K_0 + i] = keymap[pygame.K_KP0 + i] = str(i)
