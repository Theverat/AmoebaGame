from time import perf_counter
start = perf_counter()

import pygame

import state


def main():
    state.init()
    print(f"Startup time {round(perf_counter() - start, 2)} s")

    done = False

    while not done:
        # Delta time (time it took to update and draw the last frame, plus time waiting for vsync)
        dt = state.clock.tick(60) / 1000
        # Only the time it took to update and draw the last frame, excluding idle waiting time
        dt_used_ms = state.clock.get_rawtime()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    done = True

        state.update(dt)
        state.draw(dt_used_ms)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
