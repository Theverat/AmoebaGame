import pygame
from random import random
import math


class Amoeba:
    def __init__(self, x: float, y: float, radius: float, color=None):
        self.pos_x = x
        self.pos_y = y
        self.speed_x = 0
        self.speed_y = 0
        self.radius = radius
        if color:
            self.color = color
        else:
            color = [random() * 255, random() * 255, random() * 255]
            # Make sure it's a bright color
            max_value = max(color)
            if max_value < 200:
                random_channel = int(random() * 2.9)
                color[random_channel] = 200 + random() * 55
            self.color = color

    def give_impulse(self, x, y):
        acceleration = 70 / self.radius
        self.speed_x += x * acceleration
        self.speed_y += y * acceleration

    def eat(self, other):
        area = (self.radius ** 2) * math.pi
        other_area = (other.radius ** 2) * math.pi
        assert area > other_area  # Cant' eat something bigger than yourself
        self.radius = math.sqrt((area + other_area) / math.pi)

    def update(self, dt: float):
        self.pos_x += self.speed_x * dt
        self.pos_y += self.speed_y * dt

        # TODO also make dependent of dt
        DAMPING = 0.97
        self.speed_x *= DAMPING
        self.speed_y *= DAMPING

    def draw(self):
        import state
        outline_width = 2
        outline_color = [50] * 3
        pygame.draw.circle(state.window, self.color, (self.pos_x, self.pos_y), self.radius)
        pygame.draw.circle(state.window, outline_color, (self.pos_x, self.pos_y), self.radius, outline_width)

        if self.radius > 30:
            text_surface = state.my_font.render(str(round(self.radius)), True, (0, 0, 0))
            state.window.blit(text_surface, (self.pos_x - text_surface.get_width() / 2,
                                             self.pos_y - text_surface.get_height() / 2))


class PlayerAmoeba(Amoeba):
    def __init__(self, player_id: int, x: float, y: float):
        PLAYER_INIT_RADIUS = 10
        super().__init__(x, y, PLAYER_INIT_RADIUS)
        self.player_id = player_id
