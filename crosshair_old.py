from typing import TYPE_CHECKING

import pygame
from pygame.sprite import Sprite
from pygame.surface import Surface

if TYPE_CHECKING:
    from shooter_game import ShooterGame


class Crosshair(Sprite):
    def __init__(self, images: list[Surface], *groups) -> None:
        super().__init__(*groups)
        self.images = images
        self.image = self.images[0]
        self.rect = self.image.get_rect()

    def update(self, game: "ShooterGame") -> None:
        mouse_pos = pygame.mouse.get_pos()
        self.rect.center = mouse_pos
