import pygame
from random import random
import math
from dataclasses import dataclass
from typing import Optional

import state
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

        # Prevent stuff from going beyond the edges of the screen
        import state
        self.pos_x = utils.clamp(self.pos_x, 0, state.window.get_width())
        self.pos_y = utils.clamp(self.pos_y, 0, state.window.get_height())


class Food(MovingObject):
    def __init__(self, x: float, y: float, radius: float, color):
        super().__init__(x, y, radius)
        self.color = color
        self.is_edible = True

    def draw(self):
        import state
        pygame.draw.circle(state.window, self.color, (self.pos_x, self.pos_y), self.radius)


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


class PlayerAmoeba(Amoeba):
    def __init__(self, player_id: int, x: float, y: float):
        PLAYER_INIT_RADIUS = 10
        super().__init__(x, y, PLAYER_INIT_RADIUS)
        self.player_id = player_id
        self.GRENADE_RELOAD_TIME = .5
        # Start with a grenade ready
        self.last_grenade_fired = -99
        self.aim_angle: float = 0
        # turn speed in degrees per second
        self.aim_speed: float = math.radians(90)
        self.reserve_powerups = []
        from powerups import Powerup
        self.active_powerup: Optional[Powerup] = None

    def add_powerup(self, powerup):
        self.reserve_powerups.append(powerup)

    def update_aim(self, dt: float, aim_x: float, aim_y: float):
        if aim_x or aim_y:
            target_angle = utils.vec_to_angle((aim_x, aim_y))

            difference = math.fmod(target_angle - self.aim_angle, math.tau)
            distance = math.fmod(2 * difference, math.tau) - difference
            movement_abs = min(abs(distance), self.aim_speed * dt)
            movement = math.copysign(movement_abs, distance)

            self.aim_angle += movement

    def update(self, dt: float):
        super().update(dt)

        if not self.active_powerup and self.reserve_powerups:
            self.active_powerup = self.reserve_powerups.pop(0)

        if self.active_powerup:
            aim_x, aim_y = utils.angle_to_vec(self.aim_angle)
            self.active_powerup.pos_x = self.pos_x + aim_x * self.radius
            self.active_powerup.pos_y = self.pos_y + aim_y * self.radius

        for powerup in self.reserve_powerups:
            # Copy player cell acceleration to powerups
            powerup.speed_x = self.speed_x
            powerup.speed_y = self.speed_y

            # Make the powerups move inside the player amoeba randomly
            distance_squared = utils.calc_distance_squared_objs(self, powerup)

            if distance_squared > (self.radius * 0.7)**2:
                # Accelerate back towards center
                dir_x = self.pos_x - powerup.pos_x
                dir_y = self.pos_y - powerup.pos_y
            else:
                # Accelerate in random direction
                dir_x = random() * 2 - 1
                dir_y = random() * 2 - 1

            dir_x, dir_y = utils.normalize((dir_x, dir_y))
            powerup.accelerate(dir_x, dir_y, random() * 10)

            powerup.update(dt)

    def draw(self):
        super().draw()

        # Draw powerups
        if self.active_powerup:
            self.active_powerup.draw()

        for powerup in self.reserve_powerups:
            powerup.draw()

        if state.draw_debug:
            # Show where the aim is currently
            from state import window
            color = (1, 0, 0)

            aim_x = math.cos(self.aim_angle)
            aim_y = math.sin(self.aim_angle)

            start_pos = (self.pos_x, self.pos_y)
            end_pos = (self.pos_x + aim_x * 100,
                       self.pos_y + aim_y * 100)
            width = 2
            pygame.draw.line(window, color, start_pos, end_pos, width)

            utils.draw_text(window, str(math.degrees(self.aim_angle)), (self.pos_x, self.pos_y), state.debug_font)

    def fire_grenade(self, game_time: float):
        if game_time - self.last_grenade_fired < self.GRENADE_RELOAD_TIME:
            # Not reloaded yet, can't fire
            return None

        self.last_grenade_fired = game_time

        # Create the grenade outside of our circle in the direction that we're aiming
        spawn_distance = self.radius + 10
        aim_x, aim_y = utils.angle_to_vec(self.aim_angle)
        x = self.pos_x + aim_x * spawn_distance
        y = self.pos_y + aim_y * spawn_distance

        grenade = GravityGrenade(x, y, game_time)

        # Copy our own impulse
        grenade.speed_x = self.speed_x
        grenade.speed_y = self.speed_y

        # Add a starting speed
        LAUNCH_SPEED = 1500
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
        from state import window
        game_time = utils.get_time()
        elapsed = game_time - self.creation_time

        if self.is_exploding(game_time):
            # Goes from 0 to 1
            explosion_timeline_pos = (elapsed - (self.ARMING_DURATION + self.FUSE_DURATION)) / self.EXPLOSION_DURATION
            color = (255, 128, 0)
            # Over the explosion time, the radius gets bigger, then smaller
            radius = self.radius + math.sin(explosion_timeline_pos * math.pi) * (self.radius * 10)
            pygame.draw.circle(window, color, (self.pos_x, self.pos_y), radius)
        else:
            color = (220, 0, 0) if self.is_active(game_time) else (0, 0, 0)
            pygame.draw.circle(window, color, (self.pos_x, self.pos_y), self.radius)

            # pygame.draw.circle(state.window, color, (self.pos_x, self.pos_y), 100, 1)
            # pygame.draw.circle(state.window, color, (self.pos_x, self.pos_y), 200, 1)
            pygame.draw.circle(window, color, (self.pos_x, self.pos_y), 300, 1)
