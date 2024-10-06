import pygame
from random import random
import math

player_to_controller_map = {}
next_free_player_id = 0

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

pygame.init()
pygame.display.set_caption("My Awesome Game")
clock = pygame.time.Clock()
target_fps = 60

my_font = pygame.font.SysFont("Comic Sans MS", 30)
debug_font = pygame.font.SysFont("Monospace", 20)

# Windowless fullscreen
# info = pygame.display.Info()
# w = info.current_w
# h = info.current_h
# window = pygame.display.set_mode((w, h), pygame.FULLSCREEN|pygame.SCALED)
window = pygame.display.set_mode((800, 600), vsync=True)

# Controller support
pygame.joystick.init()
controllers = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
# Add keyboard support
controllers.append(FakeController(keymap_WASD, "WASD"))
controllers.append(FakeController(keymap_arrow_keys, "Arrow Keys"))

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
        outline_width = 2
        outline_color = [50] * 3
        pygame.draw.circle(window, self.color, (self.pos_x, self.pos_y), self.radius)
        pygame.draw.circle(window, outline_color, (self.pos_x, self.pos_y), self.radius, outline_width)

        if self.radius > 30:
            text_surface = my_font.render(str(round(self.radius)), True, (0, 0, 0))
            window.blit(text_surface, (self.pos_x - text_surface.get_width() / 2,
                                       self.pos_y - text_surface.get_height() / 2))

class PlayerAmoeba(Amoeba):
    def __init__(self, player_id: int, x: float, y: float):
        PLAYER_INIT_RADIUS = 10
        super().__init__(x, y, PLAYER_INIT_RADIUS)
        self.player_id = player_id

amoebae: list[Amoeba] = []
player_amoebae: list[PlayerAmoeba] = []

def spawn_food(amount: int):
    info = pygame.display.Info()
    win_width = info.current_w
    win_height = info.current_h

    for i in range(amount):
        amoebae.append(Amoeba(random() * win_width,
                              random() * win_height,
                              5,
                              (0, 255, 100)))

def spawn_player(player_id: int, color=None):
    info = pygame.display.Info()
    win_width = info.current_w
    win_height = info.current_h

    spawn_margin = 50
    spawn_width = win_width - spawn_margin * 2
    spawn_height = win_height - spawn_margin * 2

    spawn_x = spawn_margin + random() * spawn_width
    spawn_y = spawn_margin + random() * spawn_height

    a = PlayerAmoeba(player_id, spawn_x, spawn_y)
    if color:
        a.color = color

    amoebae.append(a)
    player_amoebae.append(a)

def add_player():
    # Get a new player id
    global next_free_player_id
    player_id = next_free_player_id
    next_free_player_id += 1

    print("Adding player with ID:", player_id)

    # Find a free controller
    found_free_controller = False
    for controller in controllers:
        if controller not in player_to_controller_map.values():
            player_to_controller_map[player_id] = controller
            found_free_controller = True
            print(f"Player {player_id} is using controller: {controller.get_name()}")
            break

    if not found_free_controller:
        print("Could not find a free controller for player", player_id)

    spawn_player(player_id)

def init():
    for i, c in enumerate(controllers):
        print(f"[{i}]", c.get_name())

    for i in range(len(controllers)):
        add_player()

    spawn_food(100)

respawn_queue = []
food_last_added = 0

def update(dt: float):
    # Add some food
    FOOD_INTERVAL_SEC = 0.1
    elapsed = pygame.time.get_ticks() / 1000
    global food_last_added
    if elapsed - food_last_added > FOOD_INTERVAL_SEC:
        food_last_added = elapsed
        food_amount = math.floor(dt * 100)
        spawn_food(food_amount)

    # Respawn dead players
    RESPAWN_TIME_SEC = 5
    respawned = []
    for elem in respawn_queue:
        dead_player, time_of_death = elem
        if elapsed - time_of_death > RESPAWN_TIME_SEC:
            # Create a new, small amoeba for the player
            spawn_player(dead_player.player_id, dead_player.color)
            respawned.append(elem)

    for elem in respawned:
        respawn_queue.remove(elem)

    player_amoebae_to_delete = set()
    amoebae_to_delete = set()

    for player_amoeba in player_amoebae:
        move_x = 0
        move_y = 0

        try:
            controller = player_to_controller_map[player_amoeba.player_id]
            move_x = controller.get_axis(0)
            move_y = controller.get_axis(1)
        except KeyError:
            # No controller found for this player
            pass

        # Find out if the player wants to move in any direction
        # move_x, move_y = get_move_direction(player_amoeba.player_id)
        player_amoeba.give_impulse(move_x, move_y)
        # Move the player amoebae
        player_amoeba.update(dt)

        radius_squared = player_amoeba.radius ** 2

        # Check if we ate something
        for other in amoebae:
            # Don't try to eat yourself
            if other is player_amoeba:
                continue

            if other.radius > player_amoeba.radius:
                # Can't eat anything bigger than ourselves
                continue

            px = player_amoeba.pos_x
            py = player_amoeba.pos_y
            x = other.pos_x
            y = other.pos_y
            dist_squared = (px - x) ** 2 + (py - y) ** 2

            if dist_squared < (radius_squared + other.radius ** 2):
                # We ate it
                amoebae_to_delete.add(other)
                if isinstance(other, PlayerAmoeba):
                    player_amoebae_to_delete.add(other)
                # Make us bigger
                player_amoeba.eat(other)

    # Remove all entities that were eaten
    for amoeba in amoebae_to_delete:
        amoebae.remove(amoeba)

    for player_amoeba in player_amoebae_to_delete:
        player_amoebae.remove(player_amoeba)
        RESPAWN_TIME_SEC = 5
        respawn_queue.append((player_amoeba, elapsed))


def draw_text(text, position, color=(0, 0, 0), font=None, bg_color=None):
    if font is None:
        font = debug_font

    text_surface = font.render(text, True, color)

    if bg_color:
        # (left, top), (width, height)
        # rect = pygame.Rect(position, (text_surface.get_width(), text_surface.get_s))
        rect = text_surface.get_rect()
        rect.x = position[0]
        rect.y = position[1]
        pygame.draw.rect(window, bg_color, rect)

    window.blit(text_surface, position)



def draw(dt_used_ms: float):
    for amoeba in amoebae:
        amoeba.draw()

    # Debug information
    draw_text(f"{round(clock.get_fps())} fps / {dt_used_ms} ms", (10, 10), bg_color=(0, 255, 255))

def main():
    init()

    done = False

    while not done:
        # Delta time (time it took to update and draw the last frame, plus time waiting for vsync)
        dt = clock.tick(target_fps) / 1000
        # Only the time it took to update and draw the last frame, excluding idle waiting time
        dt_used_ms = clock.get_rawtime()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    done = True

        window.fill(color=(255, 255, 255))
        update(dt)
        draw(dt_used_ms)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
