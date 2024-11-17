import os

import pygame

from surface_factory import SurfaceFactory

font1_widths = [
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    0,
    0,
    7,
    7,
    0,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    5,
    3,
    5,
    9,
    7,
    8,
    8,
    3,
    5,
    5,
    7,
    9,
    4,
    8,
    3,
    5,
    8,
    4,
    7,
    7,
    8,
    7,
    7,
    7,
    7,
    7,
    3,
    4,
    6,
    9,
    6,
    7,
    9,
    8,
    8,
    8,
    8,
    8,
    8,
    8,
    8,
    5,
    7,
    8,
    7,
    9,
    9,
    9,
    8,
    9,
    8,
    8,
    9,
    8,
    9,
    10,
    9,
    9,
    8,
    4,
    6,
    4,
    8,
    9,
    5,
    7,
    7,
    6,
    7,
    7,
    6,
    7,
    7,
    3,
    5,
    7,
    3,
    9,
    7,
    7,
    7,
    7,
    6,
    6,
    6,
    7,
    7,
    10,
    7,
    7,
    6,
    5,
    3,
    5,
    8,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    3,
    3,
    5,
    5,
    3,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    3,
    6,
    7,
    7,
    13,
    3,
    11,
    10,
    13,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
    7,
]

if __name__ == "__main__":
    scale_factor = float(os.getenv("SCALE_FACTOR", 2.0))  # noqa: F821
    pygame.init()  # noqa: F821
    screen = pygame.Surface((288, 288))
    display = pygame.display.set_mode(
        (
            round(screen.get_width() * scale_factor),
            round(screen.get_height() * scale_factor),
        )
    )
    pygame.display.set_caption("Surface Factory")
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()
    factory = SurfaceFactory(["assets"])

    running = True
    while running:
        # poll for events
        # pygame.QUIT event means the user clicked X to close your window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # fill the screen with a color to wipe away anything from last frame
        screen.fill("purple")

        surfs = factory.surfaces["font1"]
        trimmed = [
            surf.subsurface(pygame.Rect(0, 0, font1_widths[i], 16))
            for i, surf in enumerate(surfs)
        ]
        txt = "The quick brown fox jumps over the lazy dog"
        width = 0
        char_surfs = []
        space_surf = pygame.Surface((4, 16), pygame.SRCALPHA)
        for i, c in enumerate(txt):
            if c != " ":
                surf = trimmed[ord(c)]
            else:
                surf = space_surf
            width += surf.get_width()
            char_surfs.append(surf)
        temp_surf = pygame.Surface((width, 16), pygame.SRCALPHA)
        temp_surf.fill((0, 0, 0, 0))
        x = 0
        for surf in char_surfs:
            temp_surf.blit(surf, (x, 0))
            x += surf.get_width()
        screen.blit(temp_surf, (0, 0))

        mystery = pygame.font.Font("assets/mystery-font.ttf", 7)
        text = mystery.render(
            "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJK",
            False,
            (255, 255, 255),
        )
        coord = (0, 32)
        screen.blit(text, coord)

        text = mystery.render(
            "LMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqr",
            False,
            (255, 255, 255),
        )
        coord = (0, 64)
        screen.blit(text, coord)

        text = mystery.render(
            "stuvwxyz{|}~",
            False,
            (255, 255, 255),
        )
        coord = (0, 96)
        screen.blit(text, coord)

        display.blit(pygame.transform.scale(screen, display.get_size()), (0, 0))
        pygame.display.flip()
        dt = clock.tick(60) / 1000
        # break


# 0  16  32  48
# 64 80  96  112
