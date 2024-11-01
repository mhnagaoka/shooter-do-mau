import os

import pygame

from shooter_game import ShooterGame


def main():
    pygame.init()
    pygame.display.set_caption("Shooter do Mau")
    pygame.mouse.set_visible(False)

    scale_factor = float(os.getenv("SCALE_FACTOR", 2.0))
    size = (288, 288)
    display_size = (
        round(size[0] * scale_factor),
        round(size[1] * scale_factor),
    )
    display = pygame.display.set_mode(display_size)
    clock = pygame.time.Clock()
    running = True
    game = ShooterGame(size, scale_factor, ["assets"])
    display.blit(pygame.transform.scale(game.screen, display_size), (0, 0))

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        dt = clock.tick(60) / 1000.0
        game.update(dt)
        display.blit(pygame.transform.scale(game.screen, display_size), (0, 0))
        pygame.display.flip()


if __name__ == "__main__":
    main()
