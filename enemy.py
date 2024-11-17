import random
import typing

import pygame

from animation import Animation
from engine import (
    SeekingTrajectoryProvider,
    StraightTrajectoryProvider,
    TrajectoryProvider,
    TrajectorySprite,
)
from player import Player
from shot import Shot
from surface_factory import SurfaceFactory, crop, white_out


class Enemy(TrajectorySprite):
    def __init__(
        self,
        animation: Animation,
        angle_offset: float,
        trajectory_provider: TrajectoryProvider,
        hit_points: float,
        *groups: typing.Any,
    ) -> None:
        super().__init__(animation, angle_offset, trajectory_provider, *groups)
        self.original_frames = animation.frames
        self.white_out_frames = [white_out(frame) for frame in animation.frames]
        self.white_out_timer = 0.0
        self.hit_points = hit_points
        self.health = hit_points
        self.shooting_enabled = True
        self.__generator = self.__main_loop()
        next(self.__generator)

    def draw_power_bar(self, screen: pygame.Surface) -> None:
        pass

    def update(self, dt: float) -> None:
        super().update(dt)
        self.__generator.send(dt)

    def enable_shooting(self) -> "Enemy":
        self.shooting_enabled = True
        return self

    def disable_shooting(self) -> "Enemy":
        self.shooting_enabled = False
        return self

    def hit(self, shot: Shot) -> bool:
        self.health -= shot.damage
        if self.health > 0.0:
            self.white_out_timer = 0.05
            self.animation.frames = self.white_out_frames
            return False
        return True

    def set_animation(self, animation, angle_offset=0, reset_angle=False):
        self.original_frames = animation.frames
        self.white_out_frames = [white_out(frame) for frame in animation.frames]
        return super().set_animation(animation, angle_offset, reset_angle)

    def __main_loop(self) -> typing.Generator[None, float, None]:
        dt: float
        while True:
            while self.white_out_timer <= 0.0:
                dt = yield
            while self.white_out_timer > 0.0:
                dt = yield
                self.white_out_timer -= dt
            self.animation.frames = self.original_frames


class RedEnemy(Enemy):
    def __init__(
        self,
        factory: SurfaceFactory,
        trajectory: TrajectoryProvider,
        player_group: pygame.sprite.AbstractGroup,
        bullet_group: pygame.sprite.AbstractGroup,
        *groups: pygame.sprite.AbstractGroup,
    ) -> None:
        self.neutral_anim = Animation(factory.surfaces["red-enemy"], 0.1, loop=True)
        super().__init__(self.neutral_anim, 90.0, trajectory, 9.0, *groups)
        self.player_group = player_group
        self.bullet_group = bullet_group
        # missile_surfaces = [trim(s) for s in factory.surfaces["missile"]]
        missile_surfaces = [crop(s, 6, 4, 3, 8) for s in factory.surfaces["missile"]]
        self.bullet_anim = Animation(missile_surfaces, 0.05, loop=True)
        self.__generator = self.__main_loop()
        next(self.__generator)

    def update(self, dt: float) -> None:
        super().update(dt)
        self.__generator.send(dt)

    # TODO Do we need the player argument? We have the player group already
    def shoot(self, player: Player) -> None:
        if not self.shooting_enabled:
            return
        initial_pos = self.rect.center
        direction = -pygame.Vector2(
            player.rect.center[0] - initial_pos[0],
            player.rect.center[1] - initial_pos[1],
        ).angle_to(pygame.Vector2(1, 0))
        angle_error = random.uniform(-10.0, 10.0)
        direction += angle_error
        # straight = StraightTrajectoryProvider(initial_pos, None, direction, 150.0)
        # TrajectorySprite(self.bullet_anim, None, straight, self.bullet_group)
        seeking = SeekingTrajectoryProvider(
            initial_pos,
            self.trajectory_provider.get_current_angle(),
            150.0,
            1.0,
            player,
        )
        TrajectorySprite(self.bullet_anim, -90.0, seeking, self.bullet_group)

    def __main_loop(self) -> typing.Generator[None, float, None]:
        cannon_timer = 0.1
        while True:
            dt: float = yield  # yields dt every time the game is updated
            if self.player_group:
                if cannon_timer <= 0.0:
                    self.shoot(self.player_group.sprites()[0])
                    cannon_timer = 1.0
                else:
                    cannon_timer = max(cannon_timer - dt, 0.0)


class InsectEnemy(Enemy):
    def __init__(
        self,
        factory: SurfaceFactory,
        _type: int,
        trajectory: TrajectoryProvider,
        player_group: pygame.sprite.AbstractGroup,
        bullet_group: pygame.sprite.AbstractGroup,
        *groups: pygame.sprite.AbstractGroup,
    ) -> None:
        anim = Animation.static(factory.surfaces["insect-enemies"][_type])
        super().__init__(anim, 90.0, trajectory, 19.0, *groups)
        self.player_group = player_group
        self.bullet_group = bullet_group
        self.bullet_anim = Animation.static(
            crop(factory.surfaces["shots"][3], 7, 7, 2, 2)
        )
        self.shot_speed = 80.0
        self.cannon_timer = 2.0
        self.__generator = self.__main_loop()
        next(self.__generator)

    def update(self, dt: float) -> None:
        super().update(dt)
        self.__generator.send(dt)

    # TODO Do we need the player argument? We have the player group already
    def shoot(self, player: Player) -> None:
        if not self.shooting_enabled:
            return
        initial_pos = self.rect.center
        direction = -pygame.Vector2(
            player.rect.center[0] - initial_pos[0],
            player.rect.center[1] - initial_pos[1],
        ).angle_to(pygame.Vector2(1, 0))
        angle_error = random.uniform(-10.0, 10.0)
        direction += angle_error
        straight = StraightTrajectoryProvider(
            initial_pos, None, direction, self.shot_speed
        )
        TrajectorySprite(self.bullet_anim, None, straight, self.bullet_group)

    def __main_loop(self) -> typing.Generator[None, float, None]:
        cannon_timer = 0.1
        while True:
            dt: float = yield  # yields dt every time the game is updated
            if self.player_group:
                if cannon_timer <= 0.0:
                    self.shoot(self.player_group.sprites()[0])
                    cannon_timer = self.cannon_timer
                else:
                    cannon_timer = max(cannon_timer - dt, 0.0)


class Brain(Enemy):
    def __init__(
        self,
        factory: SurfaceFactory,
        trajectory: TrajectoryProvider,
        player_group: pygame.sprite.AbstractGroup,
        bullet_group: pygame.sprite.AbstractGroup,
        *groups: pygame.sprite.AbstractGroup,
    ) -> None:
        self.neutral_anim = Animation(factory.surfaces["brain-1"], 0.1, loop=True)
        super().__init__(self.neutral_anim, 90.0, trajectory, 100.0, *groups)
        self.player_group = player_group
        self.bullet_group = bullet_group
        # missile_surfaces = [trim(s) for s in factory.surfaces["missile"]]
        missile_surfaces = [crop(s, 6, 4, 3, 8) for s in factory.surfaces["missile"]]
        self.bullet_anim = Animation(missile_surfaces, 0.05, loop=True)
        self.__generator = self.__main_loop()
        next(self.__generator)

    def get_hit_boxes(self) -> list[pygame.Rect]:
        result = pygame.Rect(0, 0, 32, 32)
        result.center = self.image.get_rect().center
        return [result]

    def update(self, dt: float) -> None:
        super().update(dt)
        self.__generator.send(dt)

    def draw_power_bar(self, screen: pygame.Surface) -> None:
        # Define the size and position of the power bar
        bar_width = 20
        reference = self.rect
        # bar_x = reference.x + (reference.width - bar_width) // 2
        bar_x = reference.center[0] - bar_width // 2
        bar_y = reference.center[1] - 18

        # Calculate the width of the filled part of the bar
        filled_width = int(bar_width * self.health / self.hit_points)

        # Draw the background of the bar (empty part)
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_width, 1))

        # Draw the filled part of the bar
        pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, filled_width, 1))

    def shoot(self) -> None:
        if not self.shooting_enabled:
            return
        if not self.player_group:
            return
        player = self.player_group.sprites()[0]
        initial_pos = self.rect.center
        direction = -pygame.Vector2(
            player.rect.center[0] - initial_pos[0],
            player.rect.center[1] - initial_pos[1],
        ).angle_to(pygame.Vector2(1, 0))
        normal = pygame.Vector2(1, 0).rotate(direction).rotate(90)
        base = pygame.Vector2(self.rect.center)
        missile_pos = (base + normal * 12, base - normal * 12)

        seeking = SeekingTrajectoryProvider(
            (missile_pos[0].x, missile_pos[0].y),
            self.trajectory_provider.get_current_angle(),
            150.0,
            1.0,
            player,
        )
        TrajectorySprite(self.bullet_anim, -90.0, seeking, self.bullet_group)
        seeking = SeekingTrajectoryProvider(
            (missile_pos[1].x, missile_pos[1].y),
            self.trajectory_provider.get_current_angle(),
            150.0,
            1.0,
            player,
        )
        TrajectorySprite(self.bullet_anim, -90.0, seeking, self.bullet_group)

    def __main_loop(self) -> typing.Generator[None, float, None]:
        cannon_timer = 0.1
        dt: float = 0.0
        while True:
            while cannon_timer > 0.0:
                cannon_timer -= dt
                dt = yield
            self.shoot()
            cannon_timer = 0.1
            while cannon_timer > 0.0:
                cannon_timer -= dt
                dt = yield
            self.shoot()
            cannon_timer = 0.1
            while cannon_timer > 0.0:
                cannon_timer -= dt
                dt = yield
            self.shoot()
            cannon_timer = 0.75
