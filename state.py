import pygame
from random import random, choice as random_choice
import math

from input import FakeController, keymap_WASD, keymap_arrow_keys
from entities import Object, Food, MovingObject, Amoeba, PlayerAmoeba, GravityGrenade
from powerups import PowerupType, Powerup
from quadtree import QuadTree
from accelerator import Grid
import utils


TARGET_FRAMERATE = 60

# Available controllers
controllers: list[pygame.joystick.Joystick] = []
# Mapping from player_id to controller used
player_to_controller_map: dict[int: pygame.joystick.Joystick] = {}
next_free_player_id = 1

window: pygame.Surface = None
clock: pygame.time.Clock = None

# Fonts
my_font: pygame.font.Font = None
debug_font: pygame.font.Font = None

draw_debug = False

class EntityCollection:
    def __init__(self, window_size: tuple[float, float]):
        self.objects: list[Object] = []
        self.moving_objects: list[MovingObject] = []
        self.player_amoebae: list[PlayerAmoeba] = []
        self.gravity_grenades: list[GravityGrenade] = []

        self.accelerator = Grid(window_size[0], window_size[1], 16)

    def append(self, obj):
        self.accelerator.add(obj)
        self.objects.append(obj)
        if isinstance(obj, MovingObject):
            self.moving_objects.append(obj)
            if isinstance(obj, PlayerAmoeba):
                self.player_amoebae.append(obj)
            elif isinstance(obj, GravityGrenade):
                self.gravity_grenades.append(obj)

    def remove(self, obj):
        self.accelerator.remove(obj, obj.pos_x, obj.pos_y, obj.radius)
        self.objects.remove(obj)
        if isinstance(obj, MovingObject):
            self.moving_objects.remove(obj)
            if isinstance(obj, PlayerAmoeba):
                self.player_amoebae.remove(obj)
            elif isinstance(obj, GravityGrenade):
                self.gravity_grenades.remove(obj)

    def update(self, dt):
        for obj in self.moving_objects:
            old_data = obj.pos_x, obj.pos_y, obj.radius
            obj.update(dt)
            new_data = obj.pos_x, obj.pos_y, obj.radius

            # The object might have moved from one accelerator cell into another
            if old_data != new_data:
                self.accelerator.remove(obj, *old_data)
                self.accelerator.add(obj)

# Game entities
entities: EntityCollection = None

respawn_queue: list[tuple[PlayerAmoeba, float]] = []
food_last_added = 0
powerup_last_added = 0


def init_system():
    """
    Runs before the main game loop starts.
    Global stuff is initialized here, and the starting game state is set up (spawning players, adding food etc.)
    """
    pygame.init()
    pygame.joystick.init()
    pygame.display.set_caption("Amoeba Game")

    # Init globals
    global clock, my_font, debug_font, window, entities
    clock = pygame.time.Clock()
    my_font = pygame.font.SysFont("Comic Sans MS", 30)
    debug_font = pygame.font.SysFont("Monospace", 20)
    # window = pygame.display.set_mode((800, 600), vsync=True)

    for i in range(pygame.joystick.get_count()):
        controller = pygame.joystick.Joystick(i)
        # print(f"Controller [{i}]: {controller.get_name()}")
        controllers.append(controller)
    # Add keyboard support
    controllers.append(FakeController(keymap_WASD, "WASD"))
    controllers.append(FakeController(keymap_arrow_keys, "Arrow Keys"))

    # Windowless fullscreen
    info = pygame.display.Info()
    win_size = (info.current_w, info.current_h)
    flags = 0
    window = pygame.display.set_mode(win_size, flags, vsync=1)

    entities = EntityCollection(win_size)


def init_board_and_players():
    for i in range(len(controllers)):
        add_player()

    spawn_food(100)
    spawn_powerup(1)

    entities.player_amoebae[0].radius = 100


def spawn_food(amount: int):
    info = pygame.display.Info()
    win_width = info.current_w
    win_height = info.current_h

    for i in range(amount):
        entities.append(Food(random() * win_width, random() * win_height,
                             5, (0, 170, 60)))


def spawn_powerup(amount: int):
    info = pygame.display.Info()
    win_width = info.current_w
    win_height = info.current_h

    MIN_DIST_TO_PLAYERS = 200

    for i in range(amount):
        powerup_type = random_choice(PowerupType.values)

        too_close_to_players = True

        while too_close_to_players:
            x = random() * win_width
            y = random() * win_height
            too_close_to_players = False

            rect = utils.get_square_around_point(x, y, MIN_DIST_TO_PLAYERS)
            objs_in_rect = entities.accelerator.get_objs_in_rect(*rect)

            for obj in objs_in_rect:
                dist_squared = utils.calc_distance_squared((x, y), (obj.pos_x, obj.pos_y))
                if dist_squared < MIN_DIST_TO_PLAYERS**2:
                    too_close_to_players = True

        entities.append(Powerup(x, y, powerup_type))



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

    # print("Adding player with ID:", player_id)

    # Find a free controller
    found_free_controller = False
    for controller in controllers:
        if controller not in player_to_controller_map.values():
            player_to_controller_map[player_id] = controller
            found_free_controller = True
            # print(f"Player {player_id} is using controller: {controller.get_name()}")
            break

    # if not found_free_controller:
    #     print("Could not find a free controller for player", player_id)

    spawn_player(player_id)


def update(dt: float):
    """
    Runs every frame, before draw(). Updates the game state (moving objects etc.)
    :param dt: Delta time, the time that passed since the last call to update().
               Used in various calculcations to make the game framerate-independent.
    """
    # fps = clock.get_fps()
    # if fps == 0:
    #     fps = TARGET_FRAMERATE
    # gamespeed = fps / TARGET_FRAMERATE
    # gamespeed_correction = TARGET_FRAMERATE / fps

    # Add some food
    FOOD_INTERVAL_SEC = 0.1
    game_time = utils.get_time()
    global food_last_added
    if game_time - food_last_added > FOOD_INTERVAL_SEC:
        food_last_added = game_time
        spawn_food(1)

    POWERUP_INTERVAL_SEC = 10
    game_time = utils.get_time()
    global powerup_last_added
    if game_time - powerup_last_added > POWERUP_INTERVAL_SEC:
        powerup_last_added = game_time
        spawn_powerup(1)

    # Debug: add food
    pressed = pygame.key.get_pressed()
    if pressed[pygame.K_SPACE]:
        spawn_food(30)

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
            move_x, move_y = utils.normalize((move_x, move_y))

            aim_x = controller.get_axis(Axis.RIGHT_STICK_X)
            aim_y = controller.get_axis(Axis.RIGHT_STICK_Y)
            aim_x, aim_y = utils.normalize((aim_x, aim_y))

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

        TRIGGER_THRESHOLD = 0.95

        # Acceleration from player input is reduced as radius increases
        strength = max(80, (-0.5 * player_amoeba.radius + 205)) * dt
        player_amoeba.accelerate(move_x, move_y, strength)

        player_amoeba.update_aim(dt, aim_x, aim_y)

        # Fire weapons
        if right_trigger > TRIGGER_THRESHOLD:
            grenade = player_amoeba.fire_grenade(game_time)
            if grenade:
                entities.append(grenade)

    # Check if any players are eating anything (overlapping with it)
    player_amoebae_to_delete = set()
    entities_to_delete = set()

    for player_amoeba in entities.player_amoebae:
        # Check if we ate something
        p = player_amoeba
        r = p.radius
        r2 = r * 2
        objs_in_rect = entities.accelerator.get_objs_in_rect(p.pos_x - r, p.pos_y - r, r2, r2)

        for other in objs_in_rect:
            if not (other.is_edible or isinstance(other, Powerup)):
                continue

            # Don't try to eat yourself
            if other is player_amoeba:
                continue

            player_radius = player_amoeba.radius
            other_radius = other.radius
            if other_radius > player_radius:
                # Can't eat anything bigger than ourselves
                continue

            dist_squared = utils.calc_distance_squared_objs(player_amoeba, other)

            # We know that the other is the smaller amoeba. Don't eat it when the circles touch,
            # but only once the others center overlaps with our edge.
            if dist_squared < player_radius**2:
                # We ate it
                entities_to_delete.add(other)
                if isinstance(other, PlayerAmoeba):
                    player_amoebae_to_delete.add(other)

                if other.is_edible:
                    # Make us bigger
                    player_amoeba.eat(other)
                elif isinstance(other, Powerup):
                    player_amoeba.add_powerup(other)

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

        r = 300  # TODO find a good distance where the gravity effect becomes negligible
        r2 = r * 2
        objs_in_rect = entities.accelerator.get_objs_in_rect(grenade.pos_x - r, grenade.pos_y - r, r2, r2)

        for obj in objs_in_rect:
            # Ignore ourself
            if obj is grenade:
                continue

            # Grenade gets heavier and heavier over time
            grenade_mass = 10 + 200 * grenade.get_lifetime_percent(game_time)
            # Just use the object area as its mass for now
            obj_mass = (obj.radius ** 2) * math.pi

            force = utils.calc_gravitational_force(obj, obj_mass, grenade, grenade_mass)
            force = utils.clamp(force, 0, 50)

            dir_x = grenade.pos_x - obj.pos_x
            dir_y = grenade.pos_y - obj.pos_y
            dir_x, dir_y = utils.normalize((dir_x, dir_y))
            obj.accelerate(dir_x, dir_y, force)

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

    p = entities.player_amoebae[0] if entities.player_amoebae else None
    for obj in entities.objects:
        obj.draw()

        if draw_debug and p:
            r = p.radius
            r2 = r * 2
            rect_coords = p.pos_x - r, p.pos_y - r, r2, r2
            objs_in_rect = entities.accelerator.get_objs_in_rect(*rect_coords)
            if obj in objs_in_rect:
                outline_width = 2
                outline_color = (255, 0, 0)
                pygame.draw.circle(window, outline_color, (obj.pos_x, obj.pos_y), obj.radius, outline_width)
                pygame.draw.rect(window, outline_color, pygame.Rect(*rect_coords), width=1)

    if draw_debug:
        entities.accelerator.debug_draw(window)

        utils.draw_text(window, "(Press DEL to toggle debug info)",
                        (10, 34), debug_font, bg_color=(0, 255, 255))

    # Debug information
    utils.draw_text(window, f"{round(clock.get_fps()):03} fps / {dt_used_ms:02} ms / "
                            f"{len(entities.objects)} entities",
                    (10, 10), debug_font, bg_color=(0, 255, 255))
