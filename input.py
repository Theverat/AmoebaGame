import pygame


class Axis:
    # Values range from -1 to 1
    LEFT_STICK_X = 0
    LEFT_STICK_Y = 1
    RIGHT_STICK_X = 2
    RIGHT_STICK_Y = 3
    # Not sure yet which values these yield, needs testing
    RIGHT_TRIGGER = 4
    LEFT_TRIGGER = 5


class MoveDir:
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3


class AimDir:
    UP = 4
    RIGHT = 5
    DOWN = 6
    LEFT = 7


RIGHT_TRIGGER = 8
LEFT_TRIGGER = 9


keymap_WASD = {
    MoveDir.UP: pygame.K_w,
    MoveDir.DOWN: pygame.K_s,
    MoveDir.LEFT: pygame.K_a,
    MoveDir.RIGHT: pygame.K_d,
    AimDir.UP: pygame.K_i,
    AimDir.DOWN: pygame.K_k,
    AimDir.LEFT: pygame.K_j,
    AimDir.RIGHT: pygame.K_l,
    RIGHT_TRIGGER: pygame.K_e,
    LEFT_TRIGGER: pygame.K_q,
}


keymap_arrow_keys = {
    MoveDir.UP: pygame.K_UP,
    MoveDir.DOWN: pygame.K_DOWN,
    MoveDir.LEFT: pygame.K_LEFT,
    MoveDir.RIGHT: pygame.K_RIGHT,
    # TODO aimdir
}


class FakeController:
    def __init__(self, move_map, name):
        self.move_map = move_map
        self.name = name

    def get_name(self):
        return self.name

    def get_axis(self, axis: int):
        pressed = pygame.key.get_pressed()

        def map_dirs_to_values(dir_1, value_1, dir_2, value_2, default_value):
            if pressed[self.move_map[dir_1]]:
                return value_1
            if pressed[self.move_map[dir_2]]:
                return value_2
            return default_value

        try:
            if axis == Axis.LEFT_STICK_X:
                return map_dirs_to_values(MoveDir.RIGHT, 1, MoveDir.LEFT, -1, 0)
            elif axis == Axis.LEFT_STICK_Y:
                return map_dirs_to_values(MoveDir.UP, -1, MoveDir.DOWN, 1, 0)
            elif axis == Axis.RIGHT_STICK_X:
                return map_dirs_to_values(AimDir.RIGHT, 1, AimDir.LEFT, -1, 0)
            elif axis == Axis.RIGHT_STICK_Y:
                return map_dirs_to_values(AimDir.UP, -1, AimDir.DOWN, 1, 0)
            elif axis == Axis.RIGHT_TRIGGER:
                if pressed[self.move_map[RIGHT_TRIGGER]]:
                    return 1
                else:
                    return 0
            elif axis == Axis.LEFT_TRIGGER:
                # TODO
                return 0
            else:
                raise Exception("Unsupported axis:", axis)
        except KeyError:
            # print("Warning: missing entry in move map")
            return 0
