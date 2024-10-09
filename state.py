import pygame
from random import random
import math

from input import FakeController, keymap_WASD, keymap_arrow_keys
from entities import Object, Food, MovingObject, Amoeba, PlayerAmoeba, GravityGrenade
import utils


TARGET_FRAMERATE = 60

# Available controllers
controllers: list[pygame.joystick.Joystick] = []
# Mapping from player_id to controller used
player_to_controller_map: dict[int: pygame.joystick.Joystick] = {}
next_free_player_id = 0

window: pygame.Surface = None
clock: pygame.time.Clock = None

# Fonts
my_font: pygame.font.Font = None
debug_font: pygame.font.Font = None

# Game entities
# # All moving objects
# moving_objects: list[MovingObject] = []
# # Contains all amoebae, including player-controlled amoebe
# amoebae: list[Amoeba] = []
# # Contains only player-controlled amoebae
# player_amoebae: list[PlayerAmoeba] = []
# gravity_grenades: list[GravityGrenade] = []

class EntityCollection:
    def __init__(self):
        self.objects: list[Object] = []
        self.moving_objects: list[MovingObject] = []
        self.edible_objects: list[Object] = []
        self.player_amoebae: list[PlayerAmoeba] = []
        self.gravity_grenades: list[GravityGrenade] = []

    def append(self, obj):
        self.objects.append(obj)
        if isinstance(obj, MovingObject):
            self.moving_objects.append(obj)
            if isinstance(obj, PlayerAmoeba):
                self.player_amoebae.append(obj)
            elif isinstance(obj, GravityGrenade):
                self.gravity_grenades.append(obj)
        if obj.is_edible:
            self.edible_objects.append(obj)

    def remove(self, obj):
        self.objects.remove(obj)
        if isinstance(obj, MovingObject):
            self.moving_objects.remove(obj)
            if isinstance(obj, PlayerAmoeba):
                self.player_amoebae.remove(obj)
            elif isinstance(obj, GravityGrenade):
                self.gravity_grenades.remove(obj)
        if obj.is_edible:
            self.edible_objects.remove(obj)

    def update(self, dt):
        for moving_obj in self.moving_objects:
            moving_obj.update(dt)

# Game entities
entities = EntityCollection()

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
    # window = pygame.display.set_mode((800, 600), vsync=True)

    for i in range(pygame.joystick.get_count()):
        controller = pygame.joystick.Joystick(i)
        print(f"Controller [{i}]: {controller.get_name()}")
        controllers.append(controller)
    # Add keyboard support
    controllers.append(FakeController(keymap_WASD, "WASD"))
    controllers.append(FakeController(keymap_arrow_keys, "Arrow Keys"))

    # Windowless fullscreen
    info = pygame.display.Info()
    win_size = (info.current_w, info.current_h)
    flags = 0
    window = pygame.display.set_mode(win_size, flags, vsync=1)

    for i in range(len(controllers)):
        add_player()

    spawn_food(100)


def spawn_food(amount: int):
    info = pygame.display.Info()
    win_width = info.current_w
    win_height = info.current_h

    for i in range(amount):
        entities.append(Food(random() * win_width, random() * win_height,
                             5, (0, 255, 100)))


def spawn_player(player_id: int, color=None):
    info = pygame.display.Info()
    win_width = info.current_w
    win_height = info.current_h

    spawn_margin = 50
    spawn_width = win_width - spawn_margin * 2
    spawn_height = win_height - spawn_margin * 2

    spawn_x = spawn_margin + random() * spawn_width
    spawn_y = spawn_margin + random() * spawn_height

    player_amoeba = PlayerAmoeba(player_id, spawn_x, spawn_y)
    if color:
        player_amoeba.color = color

    entities.append(player_amoeba)


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
    """
    Runs every frame, before draw(). Updates the game state (moving objects etc.)
    :param dt: Delta time, the time that passed since the last call to update().
               Used in various calculcations to make the game framerate-independent.
    """
    gamespeed = dt / (1 / TARGET_FRAMERATE)

    # Add some food
    FOOD_INTERVAL_SEC = 0.1
    game_time = utils.get_time()
    global food_last_added
    if game_time - food_last_added > FOOD_INTERVAL_SEC:
        food_last_added = game_time
        spawn_food(1)

    # Debug: add food
    pressed = pygame.key.get_pressed()
    if pressed[pygame.K_SPACE]:
        spawn_food(20)

    # Respawn dead players
    RESPAWN_TIME_SEC = 5
    respawned = []
    for elem in respawn_queue:
        dead_player, time_of_death = elem
        if game_time - time_of_death > RESPAWN_TIME_SEC:
            # Create a new, small amoeba for the player
            spawn_player(dead_player.player_id, dead_player.color)
            respawned.append(elem)

    for elem in respawned:
        respawn_queue.remove(elem)

    for player_amoeba in entities.player_amoebae:
        # Handle player input
        try:
            # For controller input handling, see https://stackoverflow.com/a/70056815
            # Also helpful: https://github.com/martinohanlon/XboxController/blob/master/XboxController.py
            from input import Axis

            controller = player_to_controller_map[player_amoeba.player_id]
            move_x = controller.get_axis(Axis.LEFT_STICK_X)
            move_y = controller.get_axis(Axis.LEFT_STICK_Y)
            aim_x = controller.get_axis(Axis.RIGHT_STICK_X)
            aim_y = controller.get_axis(Axis.RIGHT_STICK_Y)
            right_trigger = controller.get_axis(Axis.RIGHT_TRIGGER)
            left_trigger = controller.get_axis(Axis.LEFT_TRIGGER)
        except KeyError:
            # No controller found for this player
            move_x = 0
            move_y = 0
            aim_x = 0
            aim_y = 0
            right_trigger = 0
            left_trigger = 0

        strength = gamespeed
        player_amoeba.accelerate(move_x, move_y, strength)

        # Fire weapons
        if right_trigger > 0.95:
            grenade = player_amoeba.fire_grenade(game_time, aim_x, aim_y)
            if grenade:
                entities.append(grenade)

    # Check if any players are eating anything (overlapping with it)
    player_amoebae_to_delete = set()
    entities_to_delete = set()

    for player_amoeba in entities.player_amoebae:
        # Check if we ate something
        for other in entities.edible_objects:
            # Don't try to eat yourself
            if other is player_amoeba:
                continue

            player_radius = player_amoeba.radius
            other_radius = other.radius
            if other_radius > player_radius:
                # Can't eat anything bigger than ourselves
                continue

            dist_squared = utils.calc_distance_squared(player_amoeba, other)

            # We know that the other is the smaller amoeba. Don't eat it when the circles touch,
            # but only once the others center overlaps with our edge.
            if dist_squared < player_radius**2:
                # We ate it
                entities_to_delete.add(other)
                if isinstance(other, PlayerAmoeba):
                    player_amoebae_to_delete.add(other)
                # Make us bigger
                player_amoeba.eat(other)

    # Remove all entities that were eaten
    for amoeba in entities_to_delete:
        entities.remove(amoeba)

    # Queue dead players for respawn later
    for player_amoeba in player_amoebae_to_delete:
        respawn_queue.append((player_amoeba, game_time))

    # Handle gravity grenades
    grenades_to_delete = set()
    for grenade in entities.gravity_grenades:
        if grenade.should_be_removed(game_time):
            grenades_to_delete.add(grenade)
            continue

        if not grenade.is_active(game_time):
            continue

        for obj in entities.moving_objects:
            # Ignore ourself
            if obj is grenade:
                continue

            # F = (G * m1 * m2) / dist_squared
            GRAVITY_CONSTANT = 1
            # Grenade gets heavier and heavier
            mass_grenade = 10 + 200 * grenade.get_lifetime_percent(game_time)
            mass_obj = (obj.radius ** 2) * math.pi  # Just use the area for now
            dist_squared = utils.calc_distance_squared(grenade, obj)
            force = (GRAVITY_CONSTANT * mass_grenade * mass_obj) / dist_squared

            force_x = grenade.pos_x - obj.pos_x
            force_y = grenade.pos_y - obj.pos_y
            force_x, force_y = utils.normalize((force_x, force_y))
            obj.accelerate(force_x, force_y, force)

    for grenade in grenades_to_delete:
        entities.remove(grenade)

    entities.update(dt)


def draw(dt_used_ms: float):
    """
    Runs every frame. Draws everything that should be visible into the window.
    :param dt_used_ms: Delta time that was actually used for computations last frame.
    """

    # Background color
    window.fill(color=(255, 255, 255))

    for obj in entities.objects:
        obj.draw()

    # Debug information
    utils.draw_text(window, f"{round(clock.get_fps()):03} fps / {dt_used_ms:02} ms / "
                            f"{len(entities.objects)} entities",
                    (10, 10), debug_font, bg_color=(0, 255, 255))
