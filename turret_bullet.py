import pygame
from pygame import Vector2
from pygame.sprite import Sprite
from pygame.surface import Surface


class TurretBulletFactory:
    def __init__(self, images: list[Surface]) -> None:
        self.images = images

    def create_bullet(self, pos: Vector2, direction: Vector2, *groups) -> "Bullet":
        return TurretBullet(self.images, pos, direction, *groups)


class TurretBullet(Sprite):
    def __init__(
        self, images: list[Surface], pos: Vector2, direction: Vector2, *groups
    ) -> None:
        super().__init__(*groups)
        self.images = images
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.pos = pos
        self.direction = direction

    def update(self, game: "shooter.Shooter") -> None:
        self.pos = self.pos + (self.direction * 600 * game.dt)
        if (
            self.pos.y < 0
            or self.pos.y > game.screen.get_height()
            or self.pos.x < 0
            or self.pos.x > game.screen.get_width()
        ):
            self.kill()
        self.rect.topleft = self.pos - Vector2(
            self.rect.width / 2, self.rect.height / 2
        )
