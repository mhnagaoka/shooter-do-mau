import pygame

from animation import Animation
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
    pygame.init()
    screen = pygame.Surface((288, 288))
    display = pygame.display.set_mode((screen.get_width() * 4, screen.get_height() * 4))
    pygame.display.set_caption("Surface Factory")
    font = pygame.font.Font(pygame.font.get_default_font(), 12)
    clock = pygame.time.Clock()
    running = True

    factory = SurfaceFactory(["assets"])
    animation = dict()
    for name, frames in factory.surfaces.items():
        animation[name] = Animation(frames, 0.1, loop=True)
    dt = 0

    enemy = factory.surfaces["red-enemy"][0]
    angle = 0

    while running:
        # poll for events
        # pygame.QUIT event means the user clicked X to close your window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # fill the screen with a color to wipe away anything from last frame
        screen.fill((0, 0, 0))

        render_all(factory, animation, screen)
        for anim in animation.values():
            anim.update(dt)
        enemy = pygame.transform.rotate(factory.surfaces["red-enemy"][0], angle)
        enemy_rect = enemy.get_rect()
        enemy_rect.center = (240, 240)
        trimmed = trim(enemy)
        trimmed_rect = trimmed.get_rect()
        trimmed_rect.center = (240, 240)
        screen.blit(enemy, enemy_rect)
        pygame.draw.rect(screen, "white", enemy_rect, 1)
        pygame.draw.rect(screen, "red", trimmed_rect, 1)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            angle += 180 * dt
        if keys[pygame.K_RIGHT]:
            angle -= 180 * dt

        # flip() the display to put your work on screen
        display.blit(pygame.transform.scale(screen, display.get_size()), (0, 0))
        pygame.display.flip()

        # limits FPS to 60
        # dt is delta time in seconds since last frame, used for framerate-
        # independent physics.
        dt = clock.tick(60) / 1000

    pygame.quit()
