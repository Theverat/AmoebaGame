import pygame


class Direction:
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3


keymap_WASD = {
    Direction.UP: pygame.K_w,
    Direction.DOWN: pygame.K_s,
    Direction.LEFT: pygame.K_a,
    Direction.RIGHT: pygame.K_d,
}


keymap_arrow_keys = {
    Direction.UP: pygame.K_UP,
    Direction.DOWN: pygame.K_DOWN,
    Direction.LEFT: pygame.K_LEFT,
    Direction.RIGHT: pygame.K_RIGHT,
}


class FakeController:
    def __init__(self, move_map, name):
        self.move_map = move_map
        self.name = name

    def get_name(self):
        return self.name

    def get_axis(self, axis: int):
        AXIS_X = 0
        AXIS_Y = 1
        pressed = pygame.key.get_pressed()

        if axis == AXIS_X:
            x = 0
            if pressed[self.move_map[Direction.RIGHT]]:
                x = 1
            if pressed[self.move_map[Direction.LEFT]]:
                x = -1
            return x
        elif axis == AXIS_Y:
            y = 0
            if pressed[self.move_map[Direction.UP]]:
                y = -1
            if pressed[self.move_map[Direction.DOWN]]:
                y = 1
            return y
        else:
            raise Exception("Unsupported axis:", axis)
