import os

import pygame

from animation import Animation
from engine import KeyboardTrajectoryProvider, MouseTrajectoryProvider, TrajectorySprite
from surface_factory import SurfaceFactory, trim


def render_all(
    factory: SurfaceFactory, animation: dict[str, Animation], screen: pygame.Surface
):
    y = 0
    x = 0
    max_width = 0
    for name, raw_surface in factory.raw_surfaces.items():
        # draw a border around the surface
        # border = surface.get_rect()
        # border.topleft = (0, y)
        # pygame.draw.rect(screen, "white", border, 5)
        # 2x transform
        name_surface = font.render(
            f"{name} {raw_surface.get_rect().width}x{raw_surface.get_rect().height}",
            True,
            "white",
        )

        # Find the tallest sprite in the row
        row_height = 0
        for surface in factory.surfaces[name]:
            if surface.get_height() > row_height:
                row_height = surface.get_height()

        if len(animation[name].frames) > 1:
            show_animation_frame = True
            animation_frame = animation[name].get_current_frame()
        else:
            show_animation_frame = False
            animation_frame = pygame.Surface((0, 0))

        if (
            y + name_surface.get_height() + row_height + animation_frame.get_height()
            > screen.get_height()
        ):
            y = 0
            x += max_width + 1
            max_width = 0

        screen.blit(name_surface, (x, y))
        y += name_surface.get_height()
        max_width = max(max_width, name_surface.get_width())

        row_width = 0
        dark_bg = False
        for sprite_surface in factory.surfaces[name]:
            sprite_rect = sprite_surface.get_rect()
            sprite_rect.topleft = (x + row_width, y)
            if dark_bg:
                pygame.draw.rect(screen, (25, 25, 25), sprite_rect)
            else:
                pygame.draw.rect(screen, (75, 75, 75), sprite_rect)
            dark_bg = not dark_bg
            screen.blit(sprite_surface, sprite_rect)
            row_width += sprite_surface.get_width()
        y += row_height
        max_width = max(max_width, row_width)

        if show_animation_frame:
            screen.blit(animation_frame, (x, y))
            y += animation_frame.get_height()
            max_width = max(max_width, animation_frame.get_width())


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
    pygame.display.set_caption("Surface Factory")
    pygame.mouse.set_visible(False)
    font = pygame.font.Font(pygame.font.get_default_font(), 12)
    clock = pygame.time.Clock()
    running = True

    factory = SurfaceFactory(["assets"])
    animation = dict()
    for name, frames in factory.surfaces.items():
        animation[name] = Animation(frames, 0.1, loop=True)
    dt = 0

    player_trajectory_provider = KeyboardTrajectoryProvider(
        screen.get_rect(), (240, 240), 150.0, 180.0
    )
    player_group = pygame.sprite.RenderPlain()
    player_anim = Animation(factory.surfaces["player-ship"], 0.1, loop=True)
    player = TrajectorySprite(
        player_anim, 0.0, player_trajectory_provider, player_group
    )

    mouse_trajectory_provider = MouseTrajectoryProvider(scale_factor)
    reticle_group = pygame.sprite.RenderPlain()
    reticle_anim = Animation.static(factory.surfaces["shots"][0])
    reticle = TrajectorySprite(
        reticle_anim, 0.0, mouse_trajectory_provider, reticle_group
    )
    while running:
        # poll for events
        # pygame.QUIT event means the user clicked X to close your window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # fill the screen with a color to wipe away anything from last frame
        screen.fill((0, 0, 0))

        render_all(factory, animation, screen)

        # Update animations
        for anim in animation.values():
            anim.update(dt)

        # Rotation Test and keyboard driven sprite
        player_group.update(dt)
        player_group.draw(screen)
        pygame.draw.rect(screen, "cyan", player.rect, 1)
        trimmed = trim(player.image)
        trimmed_rect = trimmed.get_rect()
        trimmed_rect.center = player.rect.center
        pygame.draw.rect(screen, "magenta", trimmed_rect, 1)

        # Reticle (mouse driven sprite)
        reticle_group.update(dt)
        reticle_group.draw(screen)

        # flip() the display to put your work on screen
        display.blit(pygame.transform.scale(screen, display.get_size()), (0, 0))
        pygame.display.flip()

        # limits FPS to 60
        # dt is delta time in seconds since last frame, used for framerate-
        # independent physics.
        dt = clock.tick(60) / 1000

    pygame.quit()
