
import pygame

from entities import MovingObject

# TODO maybe weapons could work like this:
#  They are powerups in the world
#  You can collect them, and they are queued up inside the cell in a FIFO queue
#  Only one weapon is active, and can only be fired once (or a number of times)

class PowerupType:
    GRAVITY_GRENADE_LAUNCHER = 1
    LASER = 2
    values = (GRAVITY_GRENADE_LAUNCHER, LASER)

class Powerup(MovingObject):
    """
    A powerup in the world, as an item that can be collected by a player.
    """
    POWERUP_COLORS: dict[PowerupType, pygame.Color] = {
        PowerupType.GRAVITY_GRENADE_LAUNCHER: (180, 180, 0),
        PowerupType.LASER: (0, 0, 220),
    }

    def __init__(self, x: float, y: float, powerup_type: PowerupType):
        POWERUP_RADIUS = 15
        super().__init__(x, y, POWERUP_RADIUS)
        self.powerup_type: PowerupType = powerup_type
        self.color: pygame.Color = self.POWERUP_COLORS[self.powerup_type]

    def draw(self):
        # Draw a star
        from math import cos, sin, pi
        from pygame.math import Vector2
        # These two numbers control how "fat" your star is
        inner_r = 5
        outer_r = 15
        r_seq = [inner_r, outer_r] * 5  # for convenience

        # Make the coordinate for a star centered at 0,0 with points outer_r away
        # from the center and inner v things inner_r away from the center
        STAR_BASE_POLY = tuple(
            Vector2(r * cos(2 * pi * index / 10 - pi / 2), r * sin(2 * pi * index / 10 - pi / 2))
            for r, index in zip(r_seq, range(10))
        )

        # Now (or whenever you need to draw a star), translate the constant come up
        # a version of the polygon centered wherever you need it
        center_coords = Vector2(self.pos_x, self.pos_y)  # or wherever the star needs to be
        star_at_center_coords = [vertex + center_coords for vertex in STAR_BASE_POLY]

        from state import window
        pygame.draw.polygon(window, self.color, star_at_center_coords)


# @dataclass
# class Laser:
#     length: float
#     creation_time: float
#     start_pos_x: float = 0
#     start_pos_y: float = 0
#     dir_x: float = 0
#     dir_y: float = 0
#     turn_speed: float = math.radians(1)  # degrees per second
#
#     def draw(self):
#         from state import window
#         game_time = utils.get_time()
#         color = (0, 1, 0)
#         start_pos = (self.start_pos_x, self.start_pos_y)
#         end_pos = (self.start_pos_x + self.dir_x * self.length,
#                    self.start_pos_y + self.dir_y * self.length)
#         width = 10
#         pygame.draw.line(window, color, start_pos, end_pos, width)
#
#     def update(self, dt: float):
#         ...
