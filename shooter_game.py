import random
from typing import Generator

import pygame
import pygame.event

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
            crop(factory.surfaces["shots"][3], 7, 7, 2, 2)
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
        straight = StraightTrajectoryProvider(initial_pos, None, direction, 150.0)
        TrajectorySprite(self.bullet_anim, None, straight, self.bullet_group)


class InsectEnemy(TrajectorySprite):
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


class EnemySpawner:
    def __init__(self):
        self.generator = self._main_loop()
        next(self.generator)

    def update(self, game: "ShooterGame", dt: float) -> None:
        self.generator.send((game, dt))

    def _main_loop(self) -> Generator[None, float, None]:
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
                mode = 1
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
                            game.scale_factor,
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
