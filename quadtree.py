import pygame
from entities import Object

# TODO when objects move around, we will need to move them from node to node


class QuadTree:
    def __init__(self, bounding_box: pygame.Rect):
        self.root_node = Node(bounding_box, is_leaf=True)

    def add(self, obj: Object):
        self.root_node.add(obj)

    def remove(self, obj: Object):
        self.root_node.remove(obj)

    def get_objs_in_rect(self, rect: pygame.Rect):
        result = []
        self.root_node.get_objs_in_rect(rect, result)
        return result


class Node:
    MAX_OBJS_PER_LEAF = 100

    def __init__(self, bounding_box, is_leaf=False):
        self.bounding_box: pygame.Rect = bounding_box
        self.children: list[Node] = None
        self.is_leaf = is_leaf
        self.objects: list[Object] = []

    def get_objs_in_rect(self, rect: pygame.Rect, result: list[Object]):
        if not self.bounding_box.colliderect(rect):
            return

        if self.is_leaf:
            result.extend(self.objects)
        else:
            for node in self.children:
                node.get_objs_in_rect(rect, result)

    def add(self, obj: Object):
        if not self.bounding_box.collidepoint(obj.pos_x, obj.pos_y):
            return False

        if self.is_leaf:
            self.objects.append(obj)
            if len(self.objects) > Node.MAX_OBJS_PER_LEAF:
                # Add 4 subnodes and distribute the objects among them
                bbox = self.bounding_box
                new_width = bbox.width * 0.5
                new_height = bbox.height * 0.5

                bbox_top_left = pygame.Rect(bbox.left, bbox.top, new_width, new_height)
                bbox_top_right = pygame.Rect(bbox.left + new_width, bbox.top, new_width, new_height)
                bbox_bottom_left = pygame.Rect(bbox.left, bbox.top + new_height, new_width, new_height)
                bbox_bottom_right = pygame.Rect(bbox.left + new_width, bbox.top + new_height, new_width, new_height)

                top_left = Node(bbox_top_left, is_leaf=True)
                top_right = Node(bbox_top_right, is_leaf=True)
                bottom_left = Node(bbox_bottom_left, is_leaf=True)
                bottom_right = Node(bbox_bottom_right, is_leaf=True)

                self.children = [top_left, top_right, bottom_left, bottom_right]

                for obj in self.objects:
                    for node in self.children:
                        if node.bounding_box.collidepoint(obj.pos_x, obj.pos_y):
                            node.objects.append(obj)
                            break

                self.objects = []
                self.is_leaf = False
            # Wether we needed to split or not, we could add the object
            return True
        else:
            for node in self.children:
                if node.add(obj):
                    return True
        return False

    def remove(self, obj: Object):
        if not self.bounding_box.collidepoint(obj.pos_x, obj.pos_y):
            return False

        if self.is_leaf:
            self.objects.remove(obj)
            return True
        else:
            for node in self.children:
                if node.remove(obj):
                    return True
        return False
