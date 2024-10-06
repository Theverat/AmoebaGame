import pygame
import math


def draw_text(window, text, position, font, color=(0, 0, 0), bg_color=None):
    text_surface = font.render(text, True, color)

    if bg_color:
        # (left, top), (width, height)
        # rect = pygame.Rect(position, (text_surface.get_width(), text_surface.get_s))
        rect = text_surface.get_rect()
        rect.x = position[0]
        rect.y = position[1]
        pygame.draw.rect(window, bg_color, rect)

    window.blit(text_surface, position)


def get_time():
    return pygame.time.get_ticks() / 1000


def normalize(vec2):
    x = vec2[0]
    y = vec2[1]
    length = math.sqrt(x ** 2 + y ** 2)
    return x / length, y / length
