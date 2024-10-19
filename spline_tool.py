import os
from enum import IntEnum

import pygame

import enemy
from animation import Animation
from surface_factory import SurfaceFactory


class ToolMode(IntEnum):
    HIDE_ALL = 0
    SHOW_POINTS = 1
    SHOW_LINES = 2
    SHOW_SPLINE = 3


tool_mode = ToolMode.SHOW_SPLINE

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
    dt = 0
    running = True
    mouse_trajectory_provider = enemy.MouseTrajectoryProvider(scale_factor)
    mouse_pos = mouse_trajectory_provider.position
    prev_keys = None
    dragging_rect = None
    ctrl_rects: list[pygame.Rect] = list()
    trajectory = None
    prev_trajectory_idx = 0
    trajectory_idx = 0

    factory = SurfaceFactory(["assets"])
    group = pygame.sprite.RenderPlain()

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
            if len(ctrl_rects) > 2:
                ctrlpoints = [(r.center[0], r.center[1]) for r in ctrl_rects]
                trajectory = enemy.SplineTrajectoryProvider(
                    ctrlpoints, 150.0
                ).trajectory
                tool_mode = ToolMode.SHOW_SPLINE

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and (prev_keys is None or not prev_keys[pygame.K_a]):
            rect = pygame.Rect(0, 0, 5, 5)
            rect.center = mouse_pos
            ctrl_rects.append(rect)
            tool_mode = ToolMode.SHOW_LINES
            if len(ctrl_rects) > 2:
                ctrlpoints = [(r.center[0], r.center[1]) for r in ctrl_rects]
                trajectory = enemy.SplineTrajectoryProvider(
                    ctrlpoints, 150.0
                ).trajectory
                tool_mode = ToolMode.SHOW_SPLINE
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
            if len(ctrl_rects) > 2:
                ctrlpoints = [(r.center[0], r.center[1]) for r in ctrl_rects]
                trajectory = enemy.SplineTrajectoryProvider(
                    ctrlpoints, 150.0
                ).trajectory
                tool_mode = ToolMode.SHOW_SPLINE
        if keys[pygame.K_d] and (prev_keys is None or not prev_keys[pygame.K_d]):
            for i, rect in enumerate(ctrl_rects):
                if rect.collidepoint(mouse_pos):
                    ctrl_rects.pop(i)
                    break
            tool_mode = ToolMode.SHOW_LINES
            if len(ctrl_rects) > 2:
                ctrlpoints = [(r.center[0], r.center[1]) for r in ctrl_rects]
                trajectory = enemy.SplineTrajectoryProvider(
                    ctrlpoints, 150.0
                ).trajectory
                tool_mode = ToolMode.SHOW_SPLINE
        if keys[pygame.K_h] and (prev_keys is None or not prev_keys[pygame.K_h]):
            tool_mode = (tool_mode + 1) % len(ToolMode)
        if keys[pygame.K_RETURN] and (
            prev_keys is None or not prev_keys[pygame.K_RETURN]
        ):
            if len(ctrl_rects) > 2:
                trajectory_idx = 0
                s = enemy.TrajectorySprite(
                    Animation(factory.surfaces["red-enemy"], 0.1, loop=True),
                    90.0,
                    enemy.SplineTrajectoryProvider(ctrlpoints, 150.0),
                    group,
                ).on_trajectory_end(
                    lambda sprite: sprite.on_animation_end(
                        lambda sprite: sprite.kill()
                    ).set_animation(Animation(factory.surfaces["explosion"], 0.02))
                )
                print(ctrlpoints, len(trajectory[0]))

        prev_keys = keys

        # fill the screen with a color to wipe away anything from last frame
        screen.fill((0, 0, 0))

        if tool_mode >= ToolMode.SHOW_LINES:
            prev_rect = None
            for rect in ctrl_rects:
                if prev_rect:
                    pygame.draw.line(screen, "gray36", prev_rect.center, rect.center)
                prev_rect = rect
        if tool_mode >= ToolMode.SHOW_SPLINE:
            if len(ctrl_rects) > 2:
                ctrlpoints = [(r.center[0], r.center[1]) for r in ctrl_rects]
                prev = None
                trajectory_positions, _ = trajectory
                for curr in trajectory_positions:
                    if prev is None:
                        prev = curr
                        continue
                    pygame.draw.line(screen, "green", prev, curr)
                    prev = curr
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
        dt = clock.tick(60) / 1000

    pygame.quit()
