import pygame
from random import random
import math

import utils


class Object:
    def __init__(self, x: float, y: float):
        self.pos_x = x
        self.pos_y = y
        self.is_edible = False

    def draw(self):
        raise NotImplementedError()


class Food(Object):
    def __init__(self, x: float, y: float, radius: float, color):
        super().__init__(x, y)
        self.radius = radius
        self.color = color
        self.is_edible = True

    def draw(self):
        import state
        outline_width = 2
        outline_color = [50] * 3
        pygame.draw.circle(state.window, self.color, (self.pos_x, self.pos_y), self.radius)
        pygame.draw.circle(state.window, outline_color, (self.pos_x, self.pos_y), self.radius, outline_width)


class MovingObject(Object):
    def __init__(self, x: float, y: float):
        super().__init__(x, y)
        self.speed_x = 0
        self.speed_y = 0

    def accelerate(self, dir_x: float, dir_y: float, strength: float):
        self.speed_x += dir_x * strength
        self.speed_y += dir_y * strength

    def update(self, dt: float):
        self.pos_x += self.speed_x * dt
        self.pos_y += self.speed_y * dt

        # TODO also make dependent of dt
        DAMPING = 0.97
        self.speed_x *= DAMPING
        self.speed_y *= DAMPING


class Amoeba(MovingObject):
    def __init__(self, x: float, y: float, radius: float, color=None):
        super().__init__(x, y)
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
        self.is_edible = True

    def accelerate(self, dir_x: float, dir_y: float, strength: float):
        super().accelerate(dir_x, dir_y, 70 / self.radius)

    def eat(self, other):
        area = (self.radius ** 2) * math.pi
        other_area = (other.radius ** 2) * math.pi
        assert area > other_area  # Cant' eat something bigger than yourself
        self.radius = math.sqrt((area + other_area) / math.pi)

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
        self.GRENADE_RELOAD_TIME = 5
        # Start with a grenade ready
        self.last_grenade_fired = -99

    def fire_grenade(self, game_time: float, aim_x: float, aim_y: float):
        if game_time - self.last_grenade_fired < self.GRENADE_RELOAD_TIME:
            # Not reloaded yet, can't fire
            return None

        self.last_grenade_fired = game_time

        # Create the grenade outside of our circle in the direction that we're aiming
        # Note: I'm assuming aim_x and aim_y are normalized
        # In case the player isn't aiming, spawn the grenade in the movement direction
        if aim_x == 0 and aim_y == 0:
            if self.speed_x > 0 or self.speed_y > 0:
                aim_x, aim_y = utils.normalize((self.speed_x, self.speed_y))
            else:
                # Player is not aiming and not moving -> use some direction to
                # prevent the grenade from spawning inside the player
                aim_x = 1
                aim_y = 0

        spawn_distance = self.radius + 10
        x = self.pos_x + aim_x * spawn_distance
        y = self.pos_y + aim_y * spawn_distance

        grenade = GravityGrenade(x, y, game_time)

        # Copy our own impulse
        grenade.speed_x = self.speed_x
        grenade.speed_y = self.speed_y

        # Add a starting speed
        LAUNCH_SPEED = 300
        grenade.accelerate(aim_x, aim_y, LAUNCH_SPEED)

        return grenade


class GravityGrenade(MovingObject):
    def __init__(self, x: float, y: float, creation_time: float):
        super().__init__(x, y)
        self.radius = 10
        self.creation_time = creation_time
        self.FUSE_TIME = 3

    def try_to_explode(self, game_time: float):
        ...

    def draw(self):
        import state
        passed_lifetime = (utils.get_time() - self.creation_time) / self.FUSE_TIME
        color = (255 * min(1, passed_lifetime), 0, 0)
        pygame.draw.circle(state.window, color, (self.pos_x, self.pos_y), self.radius)
