from typing import Generator

import pygame

from engine import (
    KeyboardTrajectoryProvider,
    StraightTrajectoryProvider,
    TrajectorySprite,
)
from surface_factory import Animation, SurfaceFactory, crop


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
