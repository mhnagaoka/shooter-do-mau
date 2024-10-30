from typing import TYPE_CHECKING, Generator

import pygame
from geomdl import BSpline, utilities
from pygame import Vector2
from pygame.sprite import Sprite
from pygame.surface import Surface

from animation import Animation

if TYPE_CHECKING:
    from shooter_game import ShooterGame


def _interpolate_points(
    points: list[tuple[float, float]],
) -> tuple[list[tuple[int, int]], list[float]]:
    result_points: list[int, int] = []
    result_angles: list[float] = []
    prev_point = None
    for point in points:
        if prev_point is None:
            prev_point = point
            continue
        dx = point[0] - prev_point[0]
        dy = point[1] - prev_point[1]
        angle = Vector2(dx, dy).as_polar()[1]
        if abs(dx) > abs(dy):
            if point[0] >= prev_point[0] and point[1] >= prev_point[1]:
                for x in range(int(dx)):
                    result_points.append(
                        (int(prev_point[0] + x), int(prev_point[1] + (dy / dx) * x))
                    )
                    result_angles.append(angle)
            elif point[0] >= prev_point[0] and point[1] < prev_point[1]:
                for x in range(int(dx)):
                    result_points.append(
                        (int(prev_point[0] + x), int(prev_point[1] + (dy / dx) * x))
                    )
                    result_angles.append(angle)
            elif point[0] < prev_point[0] and point[1] >= prev_point[1]:
                for x in range(0, int(dx), -1):
                    result_points.append(
                        (int(prev_point[0] + x), int(prev_point[1] + (dy / dx) * x))
                    )
                    result_angles.append(angle)
            else:
                for x in range(0, int(dx), -1):
                    result_points.append(
                        (int(prev_point[0] + x), int(prev_point[1] + (dy / dx) * x))
                    )
                    result_angles.append(angle)
        else:
            if point[1] >= prev_point[1] and point[0] >= prev_point[0]:
                for y in range(int(dy)):
                    result_points.append(
                        (int(prev_point[0] + (dx / dy) * y), int(prev_point[1] + y))
                    )
                    result_angles.append(angle)
            elif point[1] >= prev_point[1] and point[0] < prev_point[0]:
                for y in range(int(dy)):
                    result_points.append(
                        (int(prev_point[0] + (dx / dy) * y), int(prev_point[1] + y))
                    )
                    result_angles.append(angle)
            elif point[1] < prev_point[1] and point[0] >= prev_point[0]:
                for y in range(0, int(dy), -1):
                    result_points.append(
                        (int(prev_point[0] + (dx / dy) * y), int(prev_point[1] + y))
                    )
                    result_angles.append(angle)
            else:
                for y in range(0, int(dy), -1):
                    result_points.append(
                        (int(prev_point[0] + (dx / dy) * y), int(prev_point[1] + y))
                    )
                    result_angles.append(angle)
        prev_point = point
    return result_points, result_angles


class TrajectoryProvider:
    def update(self, dt: float) -> None:
        pass

    def get_current_position(self) -> tuple[int, int]:
        pass

    def get_current_angle(self) -> float:
        pass

    def is_finished(self) -> bool:
        pass


class StraightTrajectoryProvider(TrajectoryProvider):
    def __init__(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
        angle: float,
        speed: float,
    ) -> None:
        self.start = start
        self.end = end
        self.speed = speed
        self.angle = angle
        self.position = Vector2(start)
        if end is not None:
            self._direction = Vector2(end) - Vector2(start)
            self._distance = Vector2(end).distance_to(Vector2(start))
        elif angle is not None:
            self._direction = Vector2(1, 0).rotate(angle)
            self._distance = float("Infinity")
        else:
            raise ValueError("Either end or angle must be provided")
        self._direction.normalize_ip()

    def update(self, dt: float) -> None:
        self.position += self._direction * self.speed * dt

    def get_current_position(self) -> tuple[int, int]:
        return (int(self.position.x), int(self.position.y))

    def get_current_angle(self) -> float:
        return self.angle

    def is_finished(self) -> bool:
        return self.position.distance_to(Vector2(self.start)) >= self._distance


class PredefinedTrajectoryProvider(TrajectoryProvider):
    @staticmethod
    def fixed(coord: tuple[int, int], angle: float) -> "PredefinedTrajectoryProvider":
        return PredefinedTrajectoryProvider(([coord], [angle]), 0)

    def __init__(
        self,
        trajectory: tuple[list[tuple[int, int]], list[float]],
        initial_speed: float,
    ) -> None:
        assert len(trajectory[0]) == len(trajectory[1])
        self.trajectory = trajectory
        self.index = 0
        self._speed = initial_speed

    def __len__(self) -> int:
        return len(self.trajectory[0])

    @property
    def speed(self) -> float:
        return self._speed

    @speed.setter
    def speed(self, value: float) -> "PredefinedTrajectoryProvider":
        self._speed = value
        return self

    def update(self, dt: float) -> None:
        self.index += int((self._speed * dt))

    def get_current_position(self) -> tuple[int, int]:
        return self.trajectory[0][min(self.index, len(self.trajectory[0]) - 1)]

    def get_current_angle(self) -> float:
        return self.trajectory[1][min(self.index, len(self.trajectory[1]) - 1)]

    def is_finished(self) -> bool:
        return self.index >= len(self.trajectory[0])

    def reset(self) -> None:
        self.index = 0


class SplineTrajectoryProvider(PredefinedTrajectoryProvider):
    def __init__(
        self,
        ctrlpoints: list[tuple[int, int]],
        initial_speed: float,
        angle_quantum=18.0,
    ) -> None:
        self._ctrlpoints = ctrlpoints
        self._curve = BSpline.Curve()
        self._curve.degree = 2
        self._curve.ctrlpts = ctrlpoints
        self._curve.delta = max(1 / len(ctrlpoints) / 4, 0.01)  # heuristically chosen
        self._curve.knotvector = utilities.generate_knot_vector(
            self._curve.degree, len(self._curve.ctrlpts)
        )
        positions, angles = _interpolate_points(self._curve.evalpts)
        # (hacky) make sure the last control point is included
        if positions[-1] != ctrlpoints[-1]:
            positions.append(ctrlpoints[-1])
            angles.append(angles[-1])
        if angle_quantum > 0.0:
            for i in range(len(angles)):
                angles[i] = round(angles[i] / angle_quantum) * angle_quantum
        super().__init__((positions, angles), initial_speed)


class KeyboardTrajectoryProvider(TrajectoryProvider):
    def __init__(
        self,
        boundary: pygame.Rect,
        initial_position: tuple[int, int],
        initial_speed: float,
        initial_rotation_speed: float,
    ) -> None:
        self.boundary = boundary
        self.position = Vector2(initial_position)
        self.angle = 0.0
        self.speed = initial_speed
        self.rotation_speed = initial_rotation_speed

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.position.y -= self.speed * dt
            if self.position.y < self.boundary.top:
                self.position.y = self.boundary.top
        if keys[pygame.K_DOWN]:
            self.position.y += self.speed * dt
            if self.position.y > self.boundary.bottom:
                self.position.y = self.boundary.bottom
        if keys[pygame.K_LEFT]:
            self.position.x -= self.speed * dt
            if self.position.x < self.boundary.left:
                self.position.x = self.boundary.left
        if keys[pygame.K_RIGHT]:
            self.position.x += self.speed * dt
            if self.position.x > self.boundary.right:
                self.position.x = self.boundary.right
        if keys[pygame.K_PAGEUP]:
            self.angle -= self.rotation_speed * dt
        if keys[pygame.K_PAGEDOWN]:
            self.angle += self.rotation_speed * dt

    def get_current_position(self) -> tuple[int, int]:
        return (int(self.position.x), int(self.position.y))

    def get_current_angle(self) -> float:
        return self.angle

    def is_finished(self) -> bool:
        return False


class MouseTrajectoryProvider(TrajectoryProvider):
    def __init__(
        self, scale_factor: float, initial_position: tuple[int, int] = (0, 0)
    ) -> None:
        self.scale_factor = scale_factor
        self.position = initial_position
        self.angle = 0.0

    def update(self, dt: float) -> None:
        mouse_pos = pygame.mouse.get_pos()
        self.position = (
            round(mouse_pos[0] / self.scale_factor),
            round(mouse_pos[1] / self.scale_factor),
        )

    def get_current_position(self) -> tuple[int, int]:
        return self.position

    def get_current_angle(self) -> float:
        return self.angle

    def is_finished(self) -> bool:
        return False


class AnimatedSprite(Sprite):
    def __init__(self, animation: Animation, angle_offset: float, *groups) -> None:
        super().__init__(*groups)
        self.animation = animation
        self.angle_offset = angle_offset
        self.image = self.animation.get_current_frame()
        self.rect = self.image.get_rect()
        self.rect.top = 0
        self.rect.left = 0
        self.angle = 0.0
        self.animation_end_handler = None
        self.__gen = self.__create_gen()
        next(self.__gen)

    def _update_image(self) -> None:
        self.image = self.animation.get_current_frame()
        effective_angle = -self.angle + self.angle_offset
        if effective_angle != 0.0:
            self.image = pygame.transform.rotate(self.image, effective_angle)
        new_rect = self.image.get_rect()
        new_rect.center = self.rect.center
        self.rect = new_rect

    def set_animation(
        self, animation: Animation, angle_offset=0.0, reset_angle=False
    ) -> "AnimatedSprite":
        self.animation = animation
        self.angle_offset = angle_offset
        if reset_angle:
            self.angle = 0.0
        self._update_image()
        return self

    def on_animation_end(self, handler) -> "AnimatedSprite":
        self.animation_end_handler = handler
        return self

    def __create_gen(self) -> Generator[None, float, None]:
        while not self.animation.is_finished():
            dt = yield
            self.animation.update(dt)
            self._update_image()

    def update(self, dt: float) -> None:
        try:
            self.__gen.send(dt)
        except StopIteration:
            if self.animation_end_handler:
                self.animation_end_handler(self)


class TrajectorySprite(AnimatedSprite):
    def __init__(
        self,
        animation: Animation,
        angle_offset: float,
        trajectory_provider: TrajectoryProvider,
        *groups,
    ) -> None:
        super().__init__(animation, angle_offset, *groups)
        self.trajectory_provider = trajectory_provider
        self.rect.center = self.trajectory_provider.get_current_position()
        self.trajectory_end_handler = None
        self.__gen = self.__create_gen()
        next(self.__gen)

    def on_trajectory_end(self, handler) -> "TrajectorySprite":
        self.trajectory_end_handler = handler
        return self

    def __create_gen(self) -> Generator[None, float, None]:
        while self.alive():
            dt = yield
            self.trajectory_provider.update(dt)
            self.angle = self.trajectory_provider.get_current_angle()
            self.rect.center = self.trajectory_provider.get_current_position()
            super().update(dt)

    def update(self, dt: float) -> None:
        had_finished = self.trajectory_provider.is_finished()
        try:
            self.__gen.send(dt)
        except StopIteration:
            # Generator has ended, nothing to do about it
            pass
        finally:
            if (
                not had_finished
                and self.trajectory_provider.is_finished()
                and self.trajectory_end_handler
            ):
                self.trajectory_end_handler(self)

    def kill(self):
        super().kill()


class SquadronEnemyFactory(Sprite):
    def __init__(
        self, period: float, size: int, trajectory_number: int, *groups
    ) -> None:
        super().__init__(*groups)
        self.count_down = 0
        self.image = Surface((0, 0))
        self.rect = self.image.get_rect()
        self.period = period
        self.size = size
        self.trajectory_number = trajectory_number
        self.spawned = []

    def update(self, game: "ShooterGame") -> None:
        if self.count_down <= 0:
            if self.size > 0:
                self.spawned.append(
                    SplineEnemy(
                        [game.scaled_sprites[5]],
                        self.trajectory_number,
                        game.enemy_group,
                    )
                )
                self.size -= 1
                self.count_down = self.period
            else:
                if all(not enemy.alive() for enemy in self.spawned):
                    self.kill()
        else:
            self.count_down -= game.dt


class CompositeEnemyFactory(Sprite):
    def __init__(self, enemy_factories: list[Sprite], *groups) -> None:
        super().__init__(*groups)
        self.image = Surface((0, 0))
        self.rect = self.image.get_rect()
        self.enemy_factories = enemy_factories[:]
        self.current_factory = 0
        dummy_group = pygame.sprite.Group()
        for f in self.enemy_factories:
            dummy_group.add(f)

    def add_factory(self, factory: Sprite) -> None:
        self.enemy_factories.append(factory)

    def update(self, game: "ShooterGame") -> None:
        if self.current_factory < len(self.enemy_factories):
            self.enemy_factories[self.current_factory].update(game)
            if not self.enemy_factories[self.current_factory].alive():
                self.current_factory += 1
        else:
            self.kill()


class ParallelEnemyFactory(Sprite):
    def __init__(self, enemy_factories: list[Sprite], *groups) -> None:
        super().__init__(*groups)
        self.image = Surface((0, 0))
        self.rect = self.image.get_rect()
        self.enemy_factories = enemy_factories[:]
        self.current_factory = 0
        dummy_group = pygame.sprite.Group()
        for f in self.enemy_factories:
            dummy_group.add(f)

    def add_factory(self, factory: Sprite) -> None:
        self.enemy_factories.append(factory)

    def update(self, game: "ShooterGame") -> None:
        all_dead = True
        for f in self.enemy_factories:
            if f.alive():
                f.update(game)
                all_dead = False
        if all_dead:
            self.kill()
