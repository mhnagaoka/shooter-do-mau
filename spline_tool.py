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
    pygame.init()
    screen = pygame.Surface((288, 288))
    display = pygame.display.set_mode((screen.get_width() * 2, screen.get_height() * 2))
    pygame.display.set_caption("Spline Tool")
    mouse_pos = pygame.mouse.get_pos()
    clock = pygame.time.Clock()
    dt = 0
    running = True
    mouse_pos = (0, 0)
    prev_keys = None
    dragging = None
    ctrl_rects: list[pygame.Rect] = list()

    factory = SurfaceFactory(["assets"])
    ship = enemy.AnimatedSprite(Animation(factory.surfaces["red-enemy"], 0.1, loop=True))
    ship_group = pygame.sprite.GroupSingle()
    ship_group.add(ship)
    prev_trajectory_idx = 0
    trajectory_idx = 0
    trajectory = None

    while running:
        # pygame.QUIT event means the user clicked X to close your window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        mouse_pos = pygame.mouse.get_pos()
        mouse_pos = (mouse_pos[0] // 2, mouse_pos[1] // 2)

        if pygame.mouse.get_pressed()[0]:
            for rect in ctrl_rects:
                if rect.collidepoint(mouse_pos[0], mouse_pos[1]):
                    dragging = rect
        else:
            dragging = None
        if dragging:
            dragging.center = mouse_pos
            tool_mode = ToolMode.SHOW_SPLINE

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and (prev_keys is None or not prev_keys[pygame.K_a]):
            rect = pygame.Rect(0, 0, 5, 5)
            rect.center = mouse_pos
            ctrl_rects.append(rect)
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
            tool_mode = ToolMode.SHOW_SPLINE
        if keys[pygame.K_d] and (prev_keys is None or not prev_keys[pygame.K_d]):
            for i, rect in enumerate(ctrl_rects):
                if rect.collidepoint(mouse_pos):
                    ctrl_rects.pop(i)
                    break
            tool_mode = ToolMode.SHOW_SPLINE
        if keys[pygame.K_h] and (prev_keys is None or not prev_keys[pygame.K_h]):
            tool_mode = (tool_mode + 1) % len(ToolMode)
        if keys[pygame.K_RETURN] and (
            prev_keys is None or not prev_keys[pygame.K_RETURN]
        ):
            if len(ctrl_rects) > 2:
                ctrlpoints = [(r.center[0], r.center[1]) for r in ctrl_rects]
                trajectory = enemy.trajectory(ctrlpoints)
                trajectory_idx = 0
                print(ctrlpoints)

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
                for curr in enemy.trajectory(ctrlpoints):
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

        if trajectory:
            prev_trajectory_idx = trajectory_idx
            trajectory_idx += int(150 * dt)

            if trajectory_idx < len(trajectory):
                curr_vec = pygame.Vector2(trajectory[trajectory_idx])
                prev_vec = pygame.Vector2(trajectory[prev_trajectory_idx])
                ship_vec = curr_vec - prev_vec
                ship.angle = (-ship_vec.as_polar()[1] + 90) // 9 * 9
                ship.rect.center = trajectory[trajectory_idx]
                ship_group.update(dt)
                ship_group.draw(screen)
            else:
                trajectory = None
                trajectory_idx = 0

        display.blit(pygame.transform.scale(screen, display.get_size()), (0, 0))
        pygame.display.flip()

        # limits FPS to 60
        # dt is delta time in seconds since last frame, used for framerate-
        # independent physics.
        dt = clock.tick(60) / 1000

    pygame.quit()
