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
        self,
        factory: SurfaceFactory,
        bullet_group: pygame.sprite.AbstractGroup,
        power_source: "PowerSource" = None,
    ) -> None:
        self.bullet_group = bullet_group
        self.bullet_anim = Animation.static(
            crop(factory.surfaces["shots"][2], 7, 0, 2, 8)
        )
        self.refresh_time = 0.25
        self.power_source = power_source
        self.power_consumption = 10.0

    def shoot(self, initial_pos: tuple[int, int]) -> None:
        if not self.power_source or not self.power_source.available(
            self.power_consumption
        ):
            return
        self.power_source.consume(self.power_consumption)
        straight = StraightTrajectoryProvider(initial_pos, None, -90.0, 600.0)
        TrajectorySprite(self.bullet_anim, None, straight, self.bullet_group)


class Turret:
    def __init__(
        self,
        factory: SurfaceFactory,
        bullet_group: pygame.sprite.AbstractGroup,
        power_source: "PowerSource" = None,
    ) -> None:
        self.bullet_group = bullet_group
        self.bullet_anim = Animation.static(
            crop(factory.surfaces["shots"][1], 7, 7, 2, 2)
        )
        self.refresh_time = 0.2
        self.power_source = power_source
        self.power_consumption = 10.0

    def shoot(self, initial_pos: tuple[int, int], direction: float) -> None:
        if not self.power_source or not self.power_source.available(
            self.power_consumption
        ):
            return
        self.power_source.consume(self.power_consumption)
        straight = StraightTrajectoryProvider(initial_pos, None, direction, 300.0)
        TrajectorySprite(self.bullet_anim, None, straight, self.bullet_group)


class PowerSource:
    def __init__(self):
        self.power = 100.0
        self.power_regen = 10.0

    def charge(self, dt: float):
        self.power = min(self.power + self.power_regen * dt, 100.0)

    def consume(self, amount: float):
        self.power = max(self.power - amount, 0.0)

    def available(self, amount: float):
        return self.power >= amount


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
        self.power_source = PowerSource()
        self._cannon: Cannon = None
        self._turret: Turret = None
        self.controls_enabled = True
        self.generator = self._main_loop()
        next(self.generator)

    def update(self, dt: float) -> None:
        super().update(dt)
        self.generator.send(dt)

    def equip(
        self,
        power_source: PowerSource = None,
        cannon: Cannon = None,
        turret: Turret = None,
    ) -> None:
        if power_source is not None:
            self.power_source = power_source
            if self._cannon is not None:
                self._cannon.power_source = power_source
            if self._turret is not None:
                self._turret.power_source = power_source
        if cannon is not None:
            cannon.power_source = self.power_source
            self._cannon = cannon
        if turret is not None:
            turret.power_source = self.power_source
            self._turret = turret

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
                if self._cannon is not None:
                    if cannon_timer <= 0.0:
                        self._cannon.shoot(self.rect.center)
                        cannon_timer = self._cannon.refresh_time
                    else:
                        cannon_timer = max(cannon_timer - dt, 0.0)
            button, _, _ = pygame.mouse.get_pressed()
            if button:
                # Shoot with the turret
                if self._turret is not None:
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
                        self._turret.shoot(self.rect.center, shooting_angle)
                        turret_timer = self._turret.refresh_time
                    else:
                        turret_timer = max(turret_timer - dt, 0.0)
            print(self.power_source.power)
            self.power_source.charge(dt)
