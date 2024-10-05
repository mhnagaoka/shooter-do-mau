import pygame
from pygame import Vector2
from pygame.sprite import Sprite
from pygame.surface import Surface


class Crosshair(Sprite):
    def __init__(self, images: list[Surface], *groups) -> None:
        super().__init__(*groups)
        self.images = images
        self.image = self.images[0]
        self.rect = self.image.get_rect()

    def update(self, game: "shooter.Shooter") -> None:
        mouse_pos = pygame.mouse.get_pos()
        self.rect.center = mouse_pos
