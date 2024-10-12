from time import perf_counter
from dataclasses import dataclass
import pygame

import state

@dataclass
class TestResult:
    success: bool
    elapsed_time: float


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
        dt = state.clock.tick(state.TARGET_FRAMERATE) / 1000
        dt_used_ms = state.clock.get_rawtime()
        state.update(dt)
        state.draw(dt_used_ms)
        pygame.display.flip()
    elapsed = perf_counter() - start

    return TestResult(elapsed < 1.05, elapsed)


def run_test(func, name):
    result = func()
    result_str = "success" if result.success else "FAILED!"
    print(f"[{result_str}] {name} took {round(result.elapsed_time, 1)} s")

def main():
    run_test(test_many_entities, "1 s at 60 fps with many entities")



if __name__ == "__main__":
    main()
