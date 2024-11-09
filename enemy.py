import random
import typing

import pygame

from animation import Animation
from engine import (
    SeekingTrajectoryProvider,
    SplineTrajectoryProvider,
    StraightTrajectoryProvider,
    TrajectoryProvider,
    TrajectorySprite,
)
from player import Player
from surface_factory import SurfaceFactory, crop, trim

if typing.TYPE_CHECKING:
    from shooter_game import ShooterGame


class Enemy(TrajectorySprite):
    def __init__(
        self,
        animation: Animation,
        angle_offset: float,
        trajectory_provider: TrajectoryProvider,
        *groups: typing.Any,
    ) -> None:
        super().__init__(animation, angle_offset, trajectory_provider, *groups)


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
        super().__init__(self.neutral_anim, 90.0, trajectory, *groups)
        self.player_group = player_group
        self.bullet_group = bullet_group
        # missile_surfaces = [trim(s) for s in factory.surfaces["missile"]]
        missile_surfaces = [crop(s, 6, 4, 3, 8) for s in factory.surfaces["missile"]]
        self.bullet_anim = Animation(missile_surfaces, 0.05, loop=True)
        self.generator = self._main_loop()
        next(self.generator)

    def update(self, dt: float) -> None:
        super().update(dt)
        self.generator.send(dt)

    # TODO Do we need the player argument? We have the player group already
    def shoot(self, player: Player) -> None:
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
            initial_pos, self.trajectory_provider.get_current_angle(), 150.0, player
        )
        TrajectorySprite(self.bullet_anim, -90.0, seeking, self.bullet_group)

    def _main_loop(self) -> typing.Generator[None, float, None]:
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
        trajectory: TrajectoryProvider,
        player_group: pygame.sprite.AbstractGroup,
        bullet_group: pygame.sprite.AbstractGroup,
        *groups: pygame.sprite.AbstractGroup,
    ) -> None:
        self.neutral_anim = Animation.static(factory.surfaces["insect-enemies"][0])
        super().__init__(self.neutral_anim, 90.0, trajectory, *groups)
        self.player_group = player_group
        self.bullet_group = bullet_group
        self.bullet_anim = Animation.static(
            crop(factory.surfaces["shots"][3], 7, 7, 2, 2)
        )
        self.generator = self._main_loop()
        next(self.generator)

    def update(self, dt: float) -> None:
        super().update(dt)
        self.generator.send(dt)

    # TODO Do we need the player argument? We have the player group already
    def shoot(self, player: Player) -> None:
        initial_pos = self.rect.center
        direction = -pygame.Vector2(
            player.rect.center[0] - initial_pos[0],
            player.rect.center[1] - initial_pos[1],
        ).angle_to(pygame.Vector2(1, 0))
        angle_error = random.uniform(-10.0, 10.0)
        direction += angle_error
        straight = StraightTrajectoryProvider(initial_pos, None, direction, 150.0)
        TrajectorySprite(self.bullet_anim, None, straight, self.bullet_group)

    def _main_loop(self) -> typing.Generator[None, float, None]:
        cannon_timer = 0.1
        while True:
            dt: float = yield  # yields dt every time the game is updated
            if self.player_group:
                if cannon_timer <= 0.0:
                    self.shoot(self.player_group.sprites()[0])
                    cannon_timer = 1.0
                else:
                    cannon_timer = max(cannon_timer - dt, 0.0)


class EnemySpawner:
    def __init__(self):
        self.generator = self._main_loop()
        next(self.generator)

    def update(self, game: "ShooterGame", dt: float) -> None:
        self.generator.send((game, dt))

    def _main_loop(self) -> typing.Generator[None, float, None]:
        trajectories = [
            ([(38, -10), (39, 132), (140, 133), (257, 133), (257, 298)]),
            ([(38, -10), (39, 132), (140, 133), (257, 133), (257, -10)]),
            (
                list(
                    reversed([(38, -10), (39, 132), (140, 133), (257, 133), (257, -10)])
                )
            ),
        ]

        mode = 0  # 0 = idle, 1 = spawning
        spawn_count = 0
        squadron_size = 5
        enemy_timer = 0.4

        while True:
            arg: tuple["ShooterGame", float] = yield
            game, dt = arg
            enemy_timer -= dt
            if mode == 0 and len(game.enemy_group) == 0:
                mode = 2
                ctrlpoints = trajectories[random.randint(0, len(trajectories) - 1)]
                initial_speed = 100.0
                insect_type = random.randint(
                    0, len(game.factory.surfaces["insect-enemies"]) - 1
                )
            if mode == 1:
                if spawn_count < squadron_size:
                    if enemy_timer <= 0.0:
                        provider = SplineTrajectoryProvider(ctrlpoints, initial_speed)
                        InsectEnemy(
                            game.factory,
                            provider,
                            game.player_group,
                            game.enemy_bullet_group,
                            game.enemy_group,
                        ).on_trajectory_end(lambda s: s.kill()).set_animation(
                            Animation.static(
                                game.factory.surfaces["insect-enemies"][insect_type],
                            ),
                            None,
                        )
                        enemy_timer = 0.4
                        spawn_count += 1
                else:
                    mode = 0
                    spawn_count = 0
            if mode == 2:
                # TODO Fix magic number
                off_screen_offset = 10
                screen_rect = game.screen.get_rect()
                initial_pos = (screen_rect.centerx, screen_rect.top - off_screen_offset)
                final_pos = (
                    screen_rect.centerx,
                    screen_rect.bottom + off_screen_offset,
                )
                if game.player_group:
                    player_pos = game.player_group.sprites()[0].rect.center
                    # Extrapolate the player position to the bottom of the screen
                    final_pos = (
                        initial_pos[0]
                        + (player_pos[0] - initial_pos[0])
                        * (screen_rect.bottom + off_screen_offset - initial_pos[1])
                        / (player_pos[1] - initial_pos[1]),
                        screen_rect.bottom + off_screen_offset,
                    )
                straight = StraightTrajectoryProvider(
                    initial_pos, final_pos, None, 120.0
                )

                RedEnemy(
                    game.factory,
                    straight,
                    game.player_group,
                    game.enemy_bullet_group,
                    game.enemy_group,
                ).on_trajectory_end(lambda s: s.kill())
                mode = 1
