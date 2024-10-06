import pygame
from random import random
import math

from input import FakeController, keymap_WASD, keymap_arrow_keys
from amoeba import Amoeba, PlayerAmoeba
import utils

player_to_controller_map: dict[int: pygame.joystick.Joystick] = {}
next_free_player_id = 0

window: pygame.Surface = None
clock: pygame.time.Clock = None

# Fonts
my_font: pygame.font.Font = None
debug_font: pygame.font.Font = None

# Available controllers
controllers: list[pygame.joystick.Joystick] = []

# Game entities
# Contains all amoebae, including player-controlled amoebe
amoebae: list[Amoeba] = []
# Contains only player-controlled amoebae
player_amoebae: list[PlayerAmoeba] = []

respawn_queue: list[tuple[PlayerAmoeba, float]] = []
food_last_added = 0


def init():
    """
    Runs before the main game loop starts.
    Global stuff is initialized here, and the starting game state is set up (spawning players, adding food etc.)
    """
    pygame.init()
    pygame.joystick.init()
    pygame.display.set_caption("Amoeba Game")

    # Init globals
    global clock, my_font, debug_font, window
    clock = pygame.time.Clock()
    my_font = pygame.font.SysFont("Comic Sans MS", 30)
    debug_font = pygame.font.SysFont("Monospace", 20)
    window = pygame.display.set_mode((800, 600), vsync=True)

    for i in range(pygame.joystick.get_count()):
        controller = pygame.joystick.Joystick(i)
        print(f"Controller [{i}]: {controller.get_name()}")
        controllers.append(controller)
    # Add keyboard support
    controllers.append(FakeController(keymap_WASD, "WASD"))
    controllers.append(FakeController(keymap_arrow_keys, "Arrow Keys"))

    # Windowless fullscreen
    # info = pygame.display.Info()
    # w = info.current_w
    # h = info.current_h
    # window = pygame.display.set_mode((w, h), pygame.FULLSCREEN|pygame.SCALED)

    for i in range(len(controllers)):
        add_player()

    spawn_food(100)


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


def draw(dt_used_ms: float):
    # Background color
    window.fill(color=(255, 255, 255))

    for amoeba in amoebae:
        amoeba.draw()

    # Debug information
    utils.draw_text(window, f"{round(clock.get_fps())} fps / {dt_used_ms} ms",
                    (10, 10), debug_font, bg_color=(0, 255, 255))