from time import perf_counter
from dataclasses import dataclass
from typing import Optional
import traceback
import sys

import pygame

import state
from accelerator import Grid
from entities import Object

@dataclass
class TestResult:
    success: bool
    elapsed_time: float = 0
    exception_info = None


def test_many_entities():
    state.init_system()
    state.draw_debug = False
    for i in range(6):
        state.add_player()
    state.spawn_food(8000)

    start = perf_counter()
    # The minimum framerate we want to optimize for. We simulate one second of gameplay
    # at this framerate and check if it takes longer than a second to execute.
    min_framerate = 60
    for i in range(min_framerate):
        dt = state.clock.tick(1000) / 1000
        dt_used_ms = state.clock.get_rawtime()
        state.update(dt)
        state.draw(dt_used_ms)
        pygame.display.flip()
    elapsed = perf_counter() - start

    pygame.quit()

    return TestResult(elapsed < 1.05, elapsed)


def test_many_entities2():
    # entity_count=5000 0.7 s
    # entity_count=10000 1.2 s
    # entity_count=15000 1.8 s
    # entity_count=20000 2.4 s
    # entity_count=25000 2.9 s
    # entity_count=30000 3.6 s
    # entity_count=35000 4.7 s
    # entity_count=40000 6.1 s

    player_count = 6
    entity_counts = [5000, 10000, 15000, 20000, 25000, 30000, 35000, 40000]

    for entity_count in entity_counts:
        state.init_system()
        state.draw_debug = False
        for i in range(player_count):
            state.add_player()
        state.spawn_food(entity_count)

        start = perf_counter()
        # The minimum framerate we want to optimize for. We simulate one second of gameplay
        # at this framerate and check if it takes longer than a second to execute.
        min_framerate = 60
        for i in range(min_framerate):
            dt = state.clock.tick(1000) / 1000
            dt_used_ms = state.clock.get_rawtime()
            state.update(dt)
            state.draw(dt_used_ms)
            pygame.display.flip()
        elapsed = perf_counter() - start
        print(f"{entity_count=} {round(elapsed, 1)} s")

        pygame.quit()

    return TestResult(True)


def test_grid():
    width = 145.6
    height = 139.2
    cellcount = 16
    grid = Grid(width, height, cellcount)

    obj1 = Object(0, 0, 30)
    grid.add(obj1)
    objs = grid.get_objs_in_rect(2, 2, 5, 5)
    if obj1 not in objs:
        print("obj1 not in objs!")
        return TestResult(False)

    obj2 = Object(145, 139, 20)
    grid.add(obj2)
    objs = grid.get_objs_in_rect(145, 139, 10, 10)
    if obj2 not in objs:
        print("obj2 not in objs!")
        return TestResult(False)

    return TestResult(True)


def run_test(func, name):
    try:
        result = func()
    except:
        result = TestResult(False, 0)
        result.exception_info = sys.exc_info()

    result_str = "success" if result.success else "FAILED!"
    print(f"[{result_str}] {name} took {round(result.elapsed_time, 1)} s")
    if result.exception_info:
        traceback.print_exception(*result.exception_info)

    print()

def main():
    run_test(test_many_entities, "1 s at 60 fps with many entities")
    run_test(test_many_entities2, "Various performance tests")
    run_test(test_grid, "Grid")



if __name__ == "__main__":
    main()
