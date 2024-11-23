import asyncio
import os
import platform
import sys

import pygame

from shooter_game import ShooterGame
import engine

from build_info import build_info


def draw_game_pad(display: pygame.Surface, scale_factor: float):
    rect_color = (48, 48, 48)  # Red color
    rect_position = (0, round(288 * scale_factor))  # Top-left corner of the rectangle
    rect_size = (
        round(144 * scale_factor),
        round(100 * scale_factor),
    )  # Width and height of the rectangle
    pygame.draw.rect(display, rect_color, (*rect_position, *rect_size), 1)
    rect_color = (48, 48, 48)  # Red color
    rect_position = (
        round(144 * scale_factor),
        round(288 * scale_factor),
    )  # Top-left corner of the rectangle
    rect_size = (
        round(144 * scale_factor),
        round(100 * scale_factor),
    )  # Width and height of the rectangle
    pygame.draw.rect(display, rect_color, (*rect_position, *rect_size), 1)


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
    window_size = (display_size[0], display_size[1] + round(100 * scale_factor))
    display = pygame.display.set_mode(window_size)
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
    dir_finger_id = -1
    fire_finger_id = -1
    while running:
        events.clear()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif (
                event.type == pygame.KEYDOWN or event.type == pygame.KEYUP
            ) and event.unicode == " ":
                events.append(event)
            elif (
                event.type == pygame.FINGERDOWN
                or event.type == pygame.FINGERUP
                or event.type == pygame.FINGERMOTION
            ):
                if event.type == pygame.FINGERMOTION or event.type == pygame.FINGERDOWN:
                    rect_position_dir = (
                        round(0 * scale_factor),
                        round(288 * scale_factor),
                    )  # Top-left corner of the rectangle
                    rect_position_fire = (
                        round(144 * scale_factor),
                        round(288 * scale_factor),
                    )  # Top-left corner of the rectangle
                    rect_size = (
                        round(144 * scale_factor),
                        round(100 * scale_factor),
                    )  # Width and height of the rectangle
                    dir_pad = pygame.Rect(*rect_position_dir, *rect_size)
                    fire_pad = pygame.Rect(*rect_position_fire, *rect_size)
                    touch_x = round(event.x * window_size[0])
                    touch_y = round(event.y * window_size[1])
                    if (
                        dir_pad.collidepoint(touch_x, touch_y)
                        and event.finger_id != fire_finger_id
                    ):
                        dir_finger_id = event.finger_id
                        direction = pygame.Vector2(touch_x, touch_y) - pygame.Vector2(
                            dir_pad.center
                        )
                        if direction.length() > 15:
                            angle = -direction.angle_to(pygame.Vector2(1, 0))
                            if -22.5 < angle <= 22.5:
                                events.append(
                                    pygame.event.Event(
                                        pygame.USEREVENT,
                                        {
                                            "direction": engine.Direction.RIGHT,
                                            "fire": None,
                                        },
                                    )
                                )
                            elif 22.5 < angle <= 67.5:
                                events.append(
                                    pygame.event.Event(
                                        pygame.USEREVENT,
                                        {
                                            "direction": engine.Direction.RIGHT
                                            | engine.Direction.DOWN,
                                            "fire": None,
                                        },
                                    )
                                )
                            elif 67.5 < angle <= 112.5:
                                events.append(
                                    pygame.event.Event(
                                        pygame.USEREVENT,
                                        {
                                            "direction": engine.Direction.DOWN,
                                            "fire": None,
                                        },
                                    )
                                )
                            elif 112.5 < angle <= 157.5:
                                events.append(
                                    pygame.event.Event(
                                        pygame.USEREVENT,
                                        {
                                            "direction": engine.Direction.LEFT
                                            | engine.Direction.DOWN,
                                            "fire": None,
                                        },
                                    )
                                )
                            elif 157.5 < angle or angle <= -157.5:
                                events.append(
                                    pygame.event.Event(
                                        pygame.USEREVENT,
                                        {
                                            "direction": engine.Direction.LEFT,
                                            "fire": None,
                                        },
                                    )
                                )
                            elif -157.5 < angle <= -112.5:
                                events.append(
                                    pygame.event.Event(
                                        pygame.USEREVENT,
                                        {
                                            "direction": engine.Direction.LEFT
                                            | engine.Direction.UP,
                                            "fire": None,
                                        },
                                    )
                                )
                            elif -112.5 < angle <= -67.5:
                                events.append(
                                    pygame.event.Event(
                                        pygame.USEREVENT,
                                        {
                                            "direction": engine.Direction.UP,
                                            "fire": None,
                                        },
                                    )
                                )
                            elif -67.5 < angle <= -22.5:
                                events.append(
                                    pygame.event.Event(
                                        pygame.USEREVENT,
                                        {
                                            "direction": engine.Direction.RIGHT
                                            | engine.Direction.UP,
                                            "fire": None,
                                        },
                                    )
                                )
                        else:
                            events.append(
                                pygame.event.Event(
                                    pygame.USEREVENT,
                                    {"direction": engine.Direction(0), "fire": None},
                                )
                            )
                    elif (
                        fire_pad.collidepoint(touch_x, touch_y)
                        and event.finger_id != dir_finger_id
                    ):
                        fire_finger_id = event.finger_id
                        events.append(
                            pygame.event.Event(
                                pygame.USEREVENT, {"direction": None, "fire": True}
                            )
                        )
                elif event.type == pygame.FINGERUP:
                    if event.finger_id == dir_finger_id:
                        dir_finger_id = -1
                        events.append(
                            pygame.event.Event(
                                pygame.USEREVENT,
                                {"direction": engine.Direction(0), "fire": None},
                            )
                        )
                    elif event.finger_id == fire_finger_id:
                        fire_finger_id = -1
                        events.append(
                            pygame.event.Event(
                                pygame.USEREVENT, {"direction": None, "fire": False}
                            )
                        )

        await asyncio.sleep(0)
        dt = clock.tick(60) / 1000.0
        fps = clock.get_fps()
        try:
            game.update(events, dt, fps)
        except StopIteration:
            old = game
            game = ShooterGame(
                build_info(), size, scale_factor, ["assets"], keybindings
            )
            game.hi_score = old.hi_score
        display.blit(pygame.transform.scale(game.screen, display_size), (0, 0))

        draw_game_pad(display, scale_factor)

        pygame.display.flip()


asyncio.run(main())
