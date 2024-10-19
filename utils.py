import pygame
import math
from math import sqrt


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


def normalize(vec):
    x = vec[0]
    y = vec[1]
    length = sqrt(x ** 2 + y ** 2)
    if length > 0:
        return x / length, y / length
    else:
        return 0, 0


def lerp_vec(vec1, vec2, factor: float):
    return lerp(vec1[0], vec2[0], factor), lerp(vec1[1], vec2[1], factor)


def lerp(value1: float, value2: float, factor: float):
    """
    Linear interpolation between two values
    :param factor: How much of value2 to blend in. factor = 0 -> only use value1, factor = 1 -> only use value2
    """
    return value2 * factor + value1 * (1 - factor)


def lerp_angle(angle1: float, angle2: float, factor: float):
    """
    Linear interpolation between two angles (in radians)
    :param factor: How much of angle2 to blend in. factor = 0 -> only use angle1, factor = 1 -> only use angle2
    """
    difference = math.fmod(angle2 - angle1, math.tau)
    distance = math.fmod(2 * difference, math.tau) - difference
    return angle1 + distance * factor


def smoothstep(value1: float, value2: float, factor: float):
    t = clamp((factor - value1) / (value2 - value1))
    return t * t * (3 - t * 2)


def vec_to_angle(vec):
    # y (vec[1]) being first here is correct, not a mistake
    return math.atan2(vec[1], vec[0])


def angle_to_vec(angle: float):
    return math.cos(angle), math.sin(angle)


def calc_distance_squared(vec1, vec2):
    return (vec1[0] - vec2[0])**2 + (vec1[1] - vec2[0])**2


def clamp(value, min_value=0, max_value=1):
    return min(max(value, min_value), max_value)


def calc_distance_squared_objs(obj1, obj2):
    return (obj1.pos_x - obj2.pos_x)**2 + (obj1.pos_y - obj2.pos_y)**2


def calc_distance_objs(obj1, obj2):
    return sqrt((obj1.pos_x - obj2.pos_x)**2 + (obj1.pos_y - obj2.pos_y)**2)


def are_objs_colliding(obj1, obj2):
    return calc_distance_squared_objs(obj1, obj2) < (obj1.radius + obj2.radius)**2


def get_square_around_point(x: float, y: float, size: float):
    halfsize = size / 2
    return x - halfsize, y - halfsize, size, size


def calc_gravitational_force(from_obj, from_obj_mass, to_obj, to_obj_mass):
    assert from_obj is not to_obj
    # F = (G * m1 * m2) / dist_squared
    GRAVITY_CONSTANT = 1
    dist_squared = calc_distance_squared_objs(to_obj, from_obj)
    return (GRAVITY_CONSTANT * from_obj_mass * to_obj_mass) / dist_squared
