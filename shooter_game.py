import random
from typing import Generator

import pygame
import pygame.event

from animation import Animation
from enemy import EnemySpawner
from engine import (
    KeyboardTrajectoryProvider,
    MouseTrajectoryProvider,
    StraightTrajectoryProvider,
    TrajectorySprite,
)
from player import Cannon, Player, Turret
from surface_factory import SurfaceFactory


class ShooterGame:
    def __init__(
        self, size: tuple[int, int], scale_factor: float, asset_folders: list[str]
    ) -> None:
        self.scale_factor = scale_factor
        self.screen = pygame.Surface(size)
        self.factory = SurfaceFactory(asset_folders)
        self.font = pygame.font.Font(pygame.font.get_default_font(), 12)
        self.player_group = pygame.sprite.RenderPlain()
        self.crosshair_group = pygame.sprite.RenderPlain()
        self.player_bullet_group = pygame.sprite.RenderPlain()
        self.enemy_group = pygame.sprite.RenderPlain()
        self.explosion_group = pygame.sprite.RenderPlain()
        self.enemy_bullet_group = pygame.sprite.RenderPlain()
        self._create_player()
        self._create_crosshair()
        self.score = 0
        self.hi_score = 0
        self.generator = self._main_loop()
        next(self.generator)
        self.menu_generator = self._render_menu()
        next(self.menu_generator)

    def update(self, events: list[pygame.event.Event], dt: float) -> None:
        self.generator.send((events, dt))

    def _create_player(self) -> None:
        keyboard = KeyboardTrajectoryProvider(
            self.screen.get_rect(), self.screen.get_rect().center, 150.0, 180.0
        )
        self.player = Player(
            self.scale_factor, self.factory, keyboard, self.player_group
        )
        self.player.cannon = Cannon(self.factory, self.player_bullet_group)
        self.player.turret = Turret(self.factory, self.player_bullet_group)

    def _create_crosshair(self) -> TrajectorySprite:
        mouse = MouseTrajectoryProvider(
            self.scale_factor, self.screen.get_rect().center
        )
        crosshair_anim = Animation.static(self.factory.surfaces["shots"][0])
        return TrajectorySprite(crosshair_anim, 0.0, mouse, self.crosshair_group)

    def _clean_up_bullets(self) -> None:
        for bullet in self.player_bullet_group:
            if not self.screen.get_rect().colliderect(bullet.rect):
                bullet.kill()
        for bullet in self.enemy_bullet_group:
            if not self.screen.get_rect().colliderect(bullet.rect):
                bullet.kill()

    def _explode(self, sprite: TrajectorySprite, explosion_spped: float = 0.0):
        frames = self.factory.surfaces["explosion"] + list(
            reversed(self.factory.surfaces["explosion"])
        )
        sprite.set_animation(Animation(frames, 0.02))
        sprite.on_animation_end(lambda s: s.kill())
        sprite.trajectory_provider = StraightTrajectoryProvider(
            start=sprite.rect.center,
            end=None,
            angle=sprite.angle,
            speed=explosion_spped,
        )

    def _check_bullet_collision(self) -> None:
        # Check for collisions between bullets and enemies
        enemy_collision_result = pygame.sprite.groupcollide(
            self.player_bullet_group, self.enemy_group, True, False
        )
        for kills in enemy_collision_result.values():
            for enemy_killed in kills:
                self.score += 100
                self._explode(enemy_killed, 40.0)
                self.enemy_group.remove(enemy_killed)
                self.explosion_group.add(enemy_killed)
        # Check for collisions between bullets and player
        player_collision_result = pygame.sprite.groupcollide(
            self.player_group, self.enemy_bullet_group, False, True
        )
        if player_collision_result:
            self.player.controls_enabled = False
            self._explode(self.player, 0.0)
            self.player_group.remove(self.player)
            self.explosion_group.add(self.player)
            self.player = None

    def draw_score(self) -> None:
        color = "white"
        if self.score >= self.hi_score:
            color = "yellow"
        text = self.font.render(f"{self.score}", True, color)
        coord = (self.screen.get_width() - text.get_width() - 5, 5)
        self.screen.blit(text, coord)

    def draw_hi_score(self) -> None:
        text = self.font.render(f"{self.hi_score}", True, (255, 255, 255))
        coord = ((self.screen.get_width() - text.get_width()) // 2, 5)
        self.screen.blit(text, coord)

    def _render_menu(self) -> Generator[None, float, None]:
        mode = 1  # 0: blink, 1: show
        text = self.font.render("Hit the space bar to start.", True, (255, 255, 255))
        coord = (
            self.screen.get_rect().centerx - text.get_width() // 2,
            self.screen.get_rect().centery - text.get_height() // 2,
        )
        frame_count = 100
        while True:
            dt = yield
            if mode == 1:
                self.screen.blit(text, coord)
                if frame_count <= 0:
                    if random.randint(0, 10) < 4:
                        mode = 0
                        blink_timer = 0.1
                    else:
                        frame_count = 100
            else:
                mode = 0
                blink_timer -= dt
                if blink_timer <= 0.0:
                    mode = 1
                    frame_count = 100
            frame_count -= 1
            self.crosshair_group.update(dt)
            self.crosshair_group.draw(self.screen)
            self.draw_hi_score()

    def _main_loop(self) -> Generator[None, float, None]:
        enemy_spawner = EnemySpawner()
        mode = 0  # 0, 1: menu, 10: game, 20, 21: game over
        while True:
            events, dt = yield  # yields dt every time the game is updated
            self.screen.fill((0, 0, 0))
            if mode == 0 or mode == 1:
                self.menu_generator.send(dt)
                for event in events:
                    if (
                        mode == 0
                        and event.type == pygame.KEYDOWN
                        and event.unicode == " "
                    ):
                        mode = 1
                    elif (
                        mode == 1
                        and event.type == pygame.KEYUP
                        and event.unicode == " "
                    ):
                        mode = 10
            elif mode == 10 or mode == 20 or mode == 21:
                enemy_spawner.update(self, dt)
                self.explosion_group.update(dt)
                self.enemy_group.update(dt)
                self.player_group.update(dt)
                self.crosshair_group.update(dt)
                self.enemy_bullet_group.update(dt)
                self.player_bullet_group.update(dt)
                self.enemy_group.draw(self.screen)
                self.player_group.draw(self.screen)
                self.crosshair_group.draw(self.screen)
                self.player_bullet_group.draw(self.screen)
                self.enemy_bullet_group.draw(self.screen)
                self.explosion_group.draw(self.screen)
                self.draw_score()
                self.draw_hi_score()
                # Kill bullets that are out of bounds
                self._clean_up_bullets()
                self._check_bullet_collision()
                if (
                    mode == 10
                    and len(self.player_group) == 0
                    and len(self.explosion_group) == 0
                ):
                    mode = 20
                    game_over_timer = 10.0
                if mode == 20 or mode == 21:
                    text = self.font.render(
                        "Game Over.",
                        True,
                        (255, 255, 255),
                    )
                    self.screen.blit(
                        text,
                        (
                            self.screen.get_rect().centerx - text.get_width() // 2,
                            self.screen.get_rect().centery - text.get_height() // 2,
                        ),
                    )
                    for event in events:
                        if (
                            mode == 20
                            and event.type == pygame.KEYDOWN
                            and event.unicode == " "
                        ):
                            mode = 21
                        elif (
                            mode == 21
                            and event.type == pygame.KEYUP
                            and event.unicode == " "
                        ):
                            return
                    game_over_timer -= dt
                    if game_over_timer <= 0.0:
                        return
            if self.score > self.hi_score:
                self.hi_score = self.score
