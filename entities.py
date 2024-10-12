import pygame
from random import random
import math

import utils


class Object:
    def __init__(self, x: float, y: float, radius: float):
        self.pos_x = x
        self.pos_y = y
        self.radius = radius
        self.is_edible = False

    def draw(self):
        raise NotImplementedError()


class MovingObject(Object):
    def __init__(self, x: float, y: float, radius: float):
        super().__init__(x, y, radius)
        self.speed_x = 0
        self.speed_y = 0

    def accelerate(self, dir_x: float, dir_y: float, strength: float):
        self.speed_x += dir_x * strength
        self.speed_y += dir_y * strength

    def update(self, dt: float):
        # From https://gamedev.stackexchange.com/a/169559
        r = 0.04
        pow_r_dt = pow(r, dt)
        damping = (pow_r_dt - 1) / math.log(r)
        self.pos_x += self.speed_x * damping
        self.pos_y += self.speed_y * damping
        self.speed_x *= pow_r_dt
        self.speed_y *= pow_r_dt


class Food(MovingObject):
    def __init__(self, x: float, y: float, radius: float, color):
        super().__init__(x, y, radius)
        self.color = color
        self.is_edible = True

    def draw(self):
        import state
        pygame.draw.circle(state.window, self.color, (self.pos_x, self.pos_y), self.radius)

        # Outlines cost a ton of performance when there's a lot of food visible
        # outline_width = 2
        # outline_color = [50] * 3
        # pygame.draw.circle(state.window, outline_color, (self.pos_x, self.pos_y), self.radius, outline_width)

        # text_surface = state.debug_font.render(f"{round(self.speed_x)}, {round(self.speed_y)}", True, (0, 0, 0))
        # state.window.blit(text_surface, (self.pos_x, self.pos_y))


class Amoeba(MovingObject):
    def __init__(self, x: float, y: float, radius: float, color=None):
        super().__init__(x, y, radius)
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

    # def accelerate(self, dir_x: float, dir_y: float, strength: float):
    #     super().accelerate(dir_x, dir_y, 70 / self.radius)

    def eat(self, other):
        if self.radius < other.radius:
            # Cant' eat something bigger than yourself
            return
        area = (self.radius ** 2) * math.pi
        other_area = (other.radius ** 2) * math.pi
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

        # text_surface = state.debug_font.render(f"{round(self.speed_x)}, {round(self.speed_y)}", True, (0, 0, 0))
        # state.window.blit(text_surface, (self.pos_x, self.pos_y))


class PlayerAmoeba(Amoeba):
    def __init__(self, player_id: int, x: float, y: float):
        PLAYER_INIT_RADIUS = 10
        super().__init__(x, y, PLAYER_INIT_RADIUS)
        self.player_id = player_id
        self.GRENADE_RELOAD_TIME = .1
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


# TODO Grenade could also look like a small black hole once it activates, then gets bigger the more it swallows
#  until it shrinks rapidly
class GravityGrenade(MovingObject):
    def __init__(self, x: float, y: float, creation_time: float):
        GRENADE_RADIUS = 10
        super().__init__(x, y, GRENADE_RADIUS)
        self.creation_time = creation_time
        # TODO maybe it would be a better idea to use percentages of the total lifetime for these steps
        #  Like ARMING_DURATION = 0.1, FUSE_DURATION = 0.8, and EXPLOSION_DURATION is implicitly what's left until 1.0
        # Time until the grenade activates its gravity after creation
        self.ARMING_DURATION = 2
        # Time until the grenade explodes after arming
        self.FUSE_DURATION = 10
        self.EXPLOSION_DURATION = 0.5
        self.LIFETIME = self.ARMING_DURATION + self.FUSE_DURATION + self.EXPLOSION_DURATION

    def is_active(self, game_time: float):
        elapsed = game_time - self.creation_time
        return elapsed > self.ARMING_DURATION and elapsed < self.ARMING_DURATION + self.FUSE_DURATION

    def is_exploding(self, game_time: float):
        elapsed = game_time - self.creation_time
        return elapsed > self.ARMING_DURATION + self.FUSE_DURATION and elapsed < self.LIFETIME

    def get_lifetime_percent(self, game_time: float):
        elapsed = game_time - self.creation_time
        return elapsed / self.LIFETIME

    def should_be_removed(self, game_time: float):
        elapsed = game_time - self.creation_time
        return elapsed > self.LIFETIME

    def draw(self):
        import state
        game_time = utils.get_time()
        elapsed = game_time - self.creation_time

        if self.is_exploding(game_time):
            # Goes from 0 to 1
            explosion_timeline_pos = (elapsed - (self.ARMING_DURATION + self.FUSE_DURATION)) / self.EXPLOSION_DURATION
            color = (255, 128, 0)
            # Over the explosion time, the radius gets bigger, then smaller
            radius = self.radius + math.sin(explosion_timeline_pos * math.pi) * (self.radius * 10)
            pygame.draw.circle(state.window, color, (self.pos_x, self.pos_y), radius)
        else:
            color = (220, 0, 0) if self.is_active(game_time) else (0, 0, 0)
            pygame.draw.circle(state.window, color, (self.pos_x, self.pos_y), self.radius)

            # pygame.draw.circle(state.window, color, (self.pos_x, self.pos_y), 100, 1)
            # pygame.draw.circle(state.window, color, (self.pos_x, self.pos_y), 200, 1)
            # pygame.draw.circle(state.window, color, (self.pos_x, self.pos_y), 300, 1)
