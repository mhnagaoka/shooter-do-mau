import asyncio
import os
import platform
import sys

import pygame

from shooter_game import ShooterGame
import engine

from build_info import build_info


async def main():
    if sys.platform == "emscripten":
        platform.window.canvas.style.imageRendering = "pixelated"

    pygame.init()
    pygame.display.set_caption("Shooter do Mau")
    pygame.mouse.set_visible(False)

    scale_factor = float(os.getenv("SCALE_FACTOR", 1.0))
    size = (288, 288)
    display_size = (
        round(size[0] * scale_factor),
        round(size[1] * scale_factor),
    )
    display = pygame.display.set_mode(display_size)
    clock = pygame.time.Clock()
    running = True
    keybindings: engine.Keybindings = engine.default_keybindings | {
        pygame.K_w: engine.Direction.UP,
        pygame.K_a: engine.Direction.LEFT,
        pygame.K_s: engine.Direction.DOWN,
        pygame.K_d: engine.Direction.RIGHT,
    }
    game = ShooterGame(build_info(), size, scale_factor, ["assets"], keybindings)
    display.blit(pygame.transform.scale(game.screen, display_size), (0, 0))

    events = []
    while running:
        events.clear()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif (
                event.type == pygame.KEYDOWN or event.type == pygame.KEYUP
            ) and event.unicode == " ":
                events.append(event)

        await asyncio.sleep(0)
        dt = clock.tick(60) / 1000.0
        try:
            game.update(events, dt)
        except StopIteration:
            old = game
            game = ShooterGame(
                build_info(), size, scale_factor, ["assets"], keybindings
            )
            game.hi_score = old.hi_score
        display.blit(pygame.transform.scale(game.screen, display_size), (0, 0))
        pygame.display.flip()


asyncio.run(main())
