import random
from typing import Generator

import pygame

from animation import Animation
from engine import (
    KeyboardTrajectoryProvider,
    MouseTrajectoryProvider,
    SplineTrajectoryProvider,
    StraightTrajectoryProvider,
    TrajectoryProvider,
    TrajectorySprite,
)
from surface_factory import SurfaceFactory, crop


class Cannon:
    def __init__(
        self, factory: SurfaceFactory, bullet_group: pygame.sprite.AbstractGroup
    ) -> None:
        self.bullet_group = bullet_group
        self.bullet_anim = Animation.static(
            crop(factory.surfaces["shots"][2], 7, 0, 2, 8)
        )
        self.refresh_time = 0.25

    def shoot(self, initial_pos: tuple[int, int]) -> None:
        straight = StraightTrajectoryProvider(initial_pos, None, -90.0, 600.0)
        TrajectorySprite(self.bullet_anim, None, straight, self.bullet_group)


class Turret:
    def __init__(
        self, factory: SurfaceFactory, bullet_group: pygame.sprite.AbstractGroup
    ) -> None:
        self.bullet_group = bullet_group
        self.bullet_anim = Animation.static(
            crop(factory.surfaces["shots"][1], 7, 7, 2, 2)
        )
        self.refresh_time = 0.2

    def shoot(self, initial_pos: tuple[int, int], direction: float) -> None:
        straight = StraightTrajectoryProvider(initial_pos, None, direction, 300.0)
        TrajectorySprite(self.bullet_anim, None, straight, self.bullet_group)


class Player(TrajectorySprite):
    def __init__(
        self,
        scale_factor: float,
        factory: SurfaceFactory,
        keyboard: KeyboardTrajectoryProvider,
        *groups: pygame.sprite.AbstractGroup,
    ) -> None:
        self.scale_factor = scale_factor
        self.left_anim = Animation(factory.surfaces["player-ship-l"], 0.1, loop=True)
        self.neutral_anim = Animation(factory.surfaces["player-ship"], 0.1, loop=True)
        self.right_anim = Animation(factory.surfaces["player-ship-r"], 0.1, loop=True)
        super().__init__(self.neutral_anim, None, keyboard, *groups)
        self.generator = self._main_loop()
        next(self.generator)
        self.cannon: Cannon = None
        self.turret: Turret = None
        self.controls_enabled = True

    def update(self, dt: float) -> None:
        super().update(dt)
        self.generator.send(dt)

    def _main_loop(self) -> Generator[None, float, None]:
        cannon_timer = 0.0
        turret_timer = 0.0
        while True:
            dt: float = yield  # yields dt every time the game is updated
            if not self.controls_enabled:
                continue
            # Ugly hack to update the animation based on the pressed keys
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] and not keys[pygame.K_RIGHT]:
                self.set_animation(self.left_anim)
            elif keys[pygame.K_RIGHT] and not keys[pygame.K_LEFT]:
                self.set_animation(self.right_anim)
            else:
                self.set_animation(self.neutral_anim)
            if keys[pygame.K_SPACE]:
                if self.cannon is not None:
                    if cannon_timer <= 0.0:
                        self.cannon.shoot(self.rect.center)
                        cannon_timer = self.cannon.refresh_time
                    else:
                        cannon_timer = max(cannon_timer - dt, 0.0)
            button, _, _ = pygame.mouse.get_pressed()
            if button:
                # Shoot with the turret
                if self.turret is not None:
                    if turret_timer <= 0.0:
                        mouse_pos = pygame.mouse.get_pos()
                        player_pos = self.rect.center
                        aim_vector = (
                            mouse_pos[0] / self.scale_factor - player_pos[0],
                            mouse_pos[1] / self.scale_factor - player_pos[1],
                        )
                        if aim_vector == (0, 0):
                            aim_vector = (1, 0)
                        shooting_angle = -pygame.Vector2(aim_vector).angle_to(
                            pygame.Vector2(1, 0)
                        )
                        self.turret.shoot(self.rect.center, shooting_angle)
                        turret_timer = self.turret.refresh_time
                    else:
                        turret_timer = max(turret_timer - dt, 0.0)


class RedEnemy(TrajectorySprite):
    def __init__(
        self,
        scale_factor: float,
        factory: SurfaceFactory,
        trajectory: TrajectoryProvider,
        player_group: pygame.sprite.AbstractGroup,
        bullet_group: pygame.sprite.AbstractGroup,
        *groups: pygame.sprite.AbstractGroup,
    ) -> None:
        self.scale_factor = scale_factor
        self.neutral_anim = Animation(factory.surfaces["red-enemy"], 0.1, loop=True)
        super().__init__(self.neutral_anim, 90.0, trajectory, *groups)
        self.player_group = player_group
        self.bullet_group = bullet_group
        self.bullet_anim = Animation.static(
            crop(factory.surfaces["shots"][1], 7, 7, 2, 2)
        )
        self.generator = self._main_loop()
        next(self.generator)

    def update(self, dt: float) -> None:
        super().update(dt)
        self.generator.send(dt)

    def shoot(self, player: Player) -> None:
        initial_pos = self.rect.center
        direction = -pygame.Vector2(
            player.rect.center[0] - initial_pos[0],
            player.rect.center[1] - initial_pos[1],
        ).angle_to(pygame.Vector2(1, 0))
        angle_error = random.uniform(-10.0, 10.0)
        direction += angle_error
        straight = StraightTrajectoryProvider(initial_pos, None, direction, 200.0)
        TrajectorySprite(self.bullet_anim, None, straight, self.bullet_group)

    def _main_loop(self) -> Generator[None, float, None]:
        cannon_timer = 0.1
        while True:
            dt: float = yield  # yields dt every time the game is updated
            if self.player_group:
                if cannon_timer <= 0.0:
                    self.shoot(self.player_group.sprites()[0])
                    cannon_timer = 1.0
                else:
                    cannon_timer = max(cannon_timer - dt, 0.0)


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
        self.generator = self._main_loop()
        next(self.generator)

    def update(self, dt: float) -> None:
        self.generator.send(dt)

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

    def _explode(self, sprite: TrajectorySprite, speed_after_explosion: float = 100.0):
        frames = self.factory.surfaces["explosion"] + list(
            reversed(self.factory.surfaces["explosion"])
        )
        sprite.set_animation(Animation(frames, 0.02))
        sprite.on_animation_end(lambda s: s.kill())
        sprite.trajectory_provider = StraightTrajectoryProvider(
            start=sprite.rect.center,
            end=None,
            angle=sprite.angle,
            speed=speed_after_explosion,
        )

    def _check_bullet_collision(self) -> None:
        # Check for collisions between bullets and enemies
        enemy_collision_result = pygame.sprite.groupcollide(
            self.player_bullet_group, self.enemy_group, True, False
        )
        for kills in enemy_collision_result.values():
            for enemy_killed in kills:
                self._explode(enemy_killed)
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

    def _enemy_spawner(self) -> Generator[None, float, None]:
        trajectories = [
            ([(38, -10), (39, 132), (140, 133), (257, 133), (257, 298)], 150.0),
            ([(38, -10), (39, 132), (140, 133), (257, 133), (257, -10)], 150.0),
            (
                list(
                    reversed([(38, -10), (39, 132), (140, 133), (257, 133), (257, -10)])
                ),
                150.0,
            ),
        ]

        mode = 0  # 0 = idle, 1 = spawning
        spawn_count = 0
        squadron_size = 5
        enemy_timer = 0.2

        while True:
            dt: float = yield
            enemy_timer -= dt
            if mode == 0 and len(self.enemy_group) == 0:
                mode = 1
                ctrlpoints, initial_speed = trajectories[
                    random.randint(0, len(trajectories) - 1)
                ]
            if mode == 1:
                if spawn_count < squadron_size:
                    if enemy_timer <= 0.0:
                        provider = SplineTrajectoryProvider(ctrlpoints, initial_speed)
                        RedEnemy(
                            self.scale_factor,
                            self.factory,
                            provider,
                            self.player_group,
                            self.enemy_bullet_group,
                            self.enemy_group,
                        ).on_trajectory_end(lambda s: s.kill())
                        enemy_timer = 0.2
                        spawn_count += 1
                else:
                    mode = 0
                    spawn_count = 0

    def _main_loop(self) -> Generator[None, float, None]:
        enemy_generator = self._enemy_spawner()
        next(enemy_generator)
        while True:
            dt: float = yield  # yields dt every time the game is updated
            self.screen.fill((0, 0, 0))

            enemy_generator.send(dt)
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
            # Kill bullets that are out of bounds
            self._clean_up_bullets()
            self._check_bullet_collision()
