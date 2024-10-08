from typing import TYPE_CHECKING

from pygame import Vector2
from pygame.sprite import Sprite
from pygame.surface import Surface

if TYPE_CHECKING:
    from shooter_game import ShooterGame


class BulletFactory:
    def __init__(self, images: list[Surface]) -> None:
        self.images = images

    def create_bullet(self, pos: Vector2, *groups) -> "Bullet":
        return Bullet(self.images, pos, *groups)


class Bullet(Sprite):
    def __init__(self, images: list[Surface], pos: Vector2, *groups) -> None:
        super().__init__(*groups)
        self.images = images
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.pos = pos

    def update(self, game: "ShooterGame") -> None:
        self.pos.y = self.pos.y - 1200 * game.dt
        if self.pos.y < 0:
            self.kill()
        self.rect.center = self.pos
