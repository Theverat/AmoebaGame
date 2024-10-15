from entities import Object
from utils import clamp


class Grid:
    def __init__(self, width, height, cellcount):
        self.width = int(width)
        self.height = int(height)
        self.cellcount = cellcount
        self.cellwidth = self.width // self.cellcount
        self.cellheight = self.height // self.cellcount
        self.cells = [[set() for x in range(self.cellcount)] for y in range(self.cellcount)]
        self._max_index = self.cellcount - 1

    def add(self, obj: Object):
        left = obj.pos_x - obj.radius
        top = obj.pos_y - obj.radius
        width = obj.radius * 2
        height = width
        left_index, right_index, top_index, bottom_index = self._map_coords_to_indices(left, top, width, height)

        for y in range(top_index, bottom_index + 1):
            for x in range(left_index, right_index + 1):
                self.cells[x][y].add(obj)

    def remove(self, obj: Object, pos_x, pos_y, radius):
        left = pos_x - radius
        top = pos_y - radius
        width = radius * 2
        height = width
        left_index, right_index, top_index, bottom_index = self._map_coords_to_indices(left, top, width, height)

        for y in range(top_index, bottom_index + 1):
            for x in range(left_index, right_index + 1):
                try:
                    self.cells[x][y].remove(obj)
                except KeyError:
                    pass

    # TODO Maybe rename this, as it doesn't return only the objects in the rect, but also
    #  objects around it (from the cells the rect lies in)
    def get_objs_in_rect(self, left, top, width, height):
        left_index, right_index, top_index, bottom_index = self._map_coords_to_indices(left, top, width, height)

        objs = set()

        for y in range(top_index, bottom_index + 1):
            for x in range(left_index, right_index + 1):
                objs |= self.cells[x][y]

        return objs

    def _map_coords_to_indices(self, left, top, width, height):
        left = int(left)
        top = int(top)
        width = int(width)
        height = int(height)

        left_index = clamp(left // self.cellwidth, 0, self._max_index)
        right_index = clamp((left + width) // self.cellwidth, 0, self._max_index)
        top_index = clamp(top // self.cellheight, 0, self._max_index)
        bottom_index = clamp((top + height) // self.cellheight, 0, self._max_index)

        return left_index, right_index, top_index, bottom_index

    def debug_draw(self, window):
        import pygame
        for y in range(self.cellcount):
            for x in range(self.cellcount):
                coord_x = x * self.cellwidth
                coord_y = y * self.cellheight

                # Vertical line
                start = (coord_x, 0)
                end = (coord_x, self.height)
                pygame.draw.line(window, (0, 0, 0), start, end)

                # Horizontal line
                start = (0, coord_y)
                end = (self.width, coord_y)
                pygame.draw.line(window, (0, 0, 0), start, end)
