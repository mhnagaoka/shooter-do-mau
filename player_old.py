from typing import TYPE_CHECKING

import pygame
from pygame import Vector2
from pygame.sprite import Sprite
from pygame.surface import Surface

if TYPE_CHECKING:
    from shooter_game import ShooterGame

CANNON_DELAY = 0.300
TURRET_DELAY = 0.200


class Player(Sprite):
    def __init__(self, images: list[Surface], *groups) -> None:
        super().__init__(*groups)
        self.images = images
        self.image = self.images[2]
        self.rect = self.image.get_rect()
        self.pos = None
        self.cannon_timer = 0
        self.turret_timer = 0

    def _handle_input(self, game: "ShooterGame") -> None:
        dt = game.dt
        self.image = self.images[2]
        keys = pygame.key.get_pressed()
        left_button, _, right_button = pygame.mouse.get_pressed()
        if keys[pygame.K_w]:
            self.pos.y -= 450 * dt
            if self.pos.y < 0:
                self.pos.y = 0
        if keys[pygame.K_s]:
            self.pos.y += 450 * dt
            if self.pos.y > game.screen.get_height() - self.image.get_height():
                self.pos.y = game.screen.get_height() - self.image.get_height()
        if keys[pygame.K_a]:
            self.pos.x -= 450 * dt
            self.image = self.images[0]
            if self.pos.x < 0:
                self.pos.x = 0
                self.image = self.images[2]
        if keys[pygame.K_d]:
            self.pos.x += 450 * dt
            self.image = self.images[3]
            if self.pos.x > game.screen.get_width() - self.image.get_width():
                self.pos.x = game.screen.get_width() - self.image.get_width()
                self.image = self.images[2]
        if self.cannon_timer <= 0:
            if keys[pygame.K_SPACE] or left_button:
                game.bullet_factory.create_bullet(
                    Vector2(self.pos.x + self.image.get_width() / 2, self.pos.y),
                    game.player_bullet_group,
                )
                self.cannon_timer += dt
        elif self.cannon_timer > CANNON_DELAY:
            self.cannon_timer = 0
        else:
            self.cannon_timer += dt
        if self.turret_timer <= 0:
            if right_button:
                player_center_pos = Vector2(
                    self.pos.x + self.image.get_width() / 2,
                    self.pos.y + self.image.get_height() / 2,
                )
                direction = (pygame.mouse.get_pos() - player_center_pos).normalize()
                game.turret_bullet_factory.create_bullet(
                    player_center_pos,
                    direction,
                    game.player_bullet_group,
                )
                self.turret_timer += dt
        elif self.turret_timer > TURRET_DELAY:
            self.turret_timer = 0
        else:
            self.turret_timer += dt

    def update(self, game: "ShooterGame") -> None:
        if self.pos is None:
            self.pos = Vector2(
                game.screen.get_width() / 2 - self.rect.width / 2,
                game.screen.get_height() * 0.75,
            )
        self._handle_input(game)
        self.rect.topleft = self.pos
