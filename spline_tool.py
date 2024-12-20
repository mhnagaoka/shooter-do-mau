import os
from enum import IntEnum

import pygame
from pygame.sprite import RenderPlain

import engine
from animation import Animation
from surface_factory import SurfaceFactory


class ToolMode(IntEnum):
    HIDE_ALL = 0
    SHOW_POINTS = 1
    SHOW_LINES = 2


tool_mode = ToolMode.SHOW_LINES

if __name__ == "__main__":
    scale_factor = float(os.getenv("SCALE_FACTOR", 2.0))
    pygame.init()
    screen = pygame.Surface((288, 288))
    display = pygame.display.set_mode(
        (
            round(screen.get_width() * scale_factor),
            round(screen.get_height() * scale_factor),
        )
    )
    pygame.display.set_caption("Spline Tool")
    mouse_pos = pygame.mouse.get_pos()
    clock = pygame.time.Clock()
    dt = 0.0
    running = True
    mouse_trajectory_provider = engine.MouseTrajectoryProvider(scale_factor)
    mouse_pos = mouse_trajectory_provider.position
    prev_keys = None
    dragging_rect = None
    ctrl_rects: list[pygame.Rect] = list()
    trajectory = None
    factory = SurfaceFactory(["assets"])
    group: RenderPlain = RenderPlain()

    while running:
        # pygame.QUIT event means the user clicked X to close your window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        mouse_trajectory_provider.update(dt)
        mouse_pos = mouse_trajectory_provider.position

        if pygame.mouse.get_pressed()[0]:
            for rect in ctrl_rects:
                if rect.collidepoint(mouse_pos[0], mouse_pos[1]):
                    dragging_rect = rect
        else:
            dragging_rect = None
        if dragging_rect:
            dragging_rect.center = mouse_pos
            tool_mode = ToolMode.SHOW_LINES

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and (prev_keys is None or not prev_keys[pygame.K_a]):
            rect = pygame.Rect(0, 0, 5, 5)
            rect.center = mouse_pos
            ctrl_rects.append(rect)
            tool_mode = ToolMode.SHOW_LINES
        if keys[pygame.K_i] and (prev_keys is None or not prev_keys[pygame.K_i]):
            for i, rect in enumerate(ctrl_rects):
                if i < len(ctrl_rects) - 1 and rect.collidepoint(
                    mouse_pos[0], mouse_pos[1]
                ):
                    next = ctrl_rects[i + 1]
                    new_pos = (
                        (rect.center[0] + next.center[0]) // 2,
                        (rect.center[1] + next.center[1]) // 2,
                    )
                    new_rect = pygame.Rect(0, 0, 5, 5)
                    new_rect.center = new_pos
                    ctrl_rects.insert(i + 1, new_rect)
                    break
            tool_mode = ToolMode.SHOW_LINES
        if keys[pygame.K_d] and (prev_keys is None or not prev_keys[pygame.K_d]):
            for i, rect in enumerate(ctrl_rects):
                if rect.collidepoint(mouse_pos):
                    ctrl_rects.pop(i)
                    break
            tool_mode = ToolMode.SHOW_LINES
        if keys[pygame.K_h] and (prev_keys is None or not prev_keys[pygame.K_h]):
            tool_mode = ToolMode((tool_mode + 1) % len(ToolMode))
        if keys[pygame.K_RETURN] and (
            prev_keys is None or not prev_keys[pygame.K_RETURN]
        ):
            if len(ctrl_rects) > 1:

                def explode(sprite: engine.TrajectorySprite):
                    frames = factory.surfaces["explosion"][:]
                    frames.reverse()
                    frames = factory.surfaces["explosion"] + frames
                    sprite.set_animation(Animation(frames, 0.03))
                    sprite.on_animation_end(lambda s: s.kill())
                    # sprite.trajectory_provider = (
                    #     engine.PredefinedTrajectoryProvider.fixed(
                    #         sprite.rect.center, 0.0
                    #     )
                    # )
                    sprite.trajectory_provider = engine.StraightTrajectoryProvider(
                        start=sprite.rect.center,
                        end=None,
                        angle=sprite.angle,
                        speed=100.0,
                    )

                ctrl_points = [rect.center for rect in ctrl_rects]
                s = engine.TrajectorySprite(
                    Animation(factory.surfaces["red-enemy"], 0.1, loop=True),
                    90.0,
                    engine.LinearSegmentsTrajectoryProvider(ctrl_points, 150.0),
                    group,
                ).on_trajectory_end(explode)
                print(ctrl_points)

        prev_keys = keys

        # fill the screen with a color to wipe away anything from last frame
        screen.fill((0, 0, 0))

        if tool_mode >= ToolMode.SHOW_LINES:
            prev_rect = None
            for rect in ctrl_rects:
                if prev_rect:
                    pygame.draw.line(screen, "gray36", prev_rect.center, rect.center)
                prev_rect = rect
        if tool_mode >= ToolMode.SHOW_POINTS:
            for i, rect in enumerate(ctrl_rects):
                if rect.collidepoint(mouse_pos):
                    color = "yellow"
                    if rect.height <= 5:
                        rect.inflate_ip(2, 2)
                else:
                    if i == 0:
                        color = "green"
                    elif i == len(ctrl_rects) - 1:
                        color = "red"
                    else:
                        color = "white"
                    if rect.height > 5:
                        rect.inflate_ip(-2, -2)
                pygame.draw.rect(screen, color, rect, 1)

        group.update(dt)
        group.draw(screen)

        display.blit(pygame.transform.scale(screen, display.get_size()), (0, 0))
        pygame.display.flip()

        # limits FPS to 60
        # dt is delta time in seconds since last frame, used for framerate-
        # independent physics.
        dt = clock.tick(60) / 1000.0

    pygame.quit()
