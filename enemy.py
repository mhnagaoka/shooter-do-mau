from typing import TYPE_CHECKING

import pygame
from geomdl import BSpline, utilities
from pygame import Vector2
from pygame.sprite import Sprite
from pygame.surface import Surface

from animation import Animation

if TYPE_CHECKING:
    from shooter_game import ShooterGame


def _interpolation_points(
    points: list[tuple[float, float]],
) -> tuple[list[tuple[int, int]], list[float]]:
    result_points: list[int, int] = []
    result_speeds: list[float] = []
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
                    result_speeds.append(angle)
            elif point[0] >= prev_point[0] and point[1] < prev_point[1]:
                for x in range(int(dx)):
                    result_points.append(
                        (int(prev_point[0] + x), int(prev_point[1] + (dy / dx) * x))
                    )
                    result_speeds.append(angle)
            elif point[0] < prev_point[0] and point[1] >= prev_point[1]:
                for x in range(0, int(dx), -1):
                    result_points.append(
                        (int(prev_point[0] + x), int(prev_point[1] + (dy / dx) * x))
                    )
                    result_speeds.append(angle)
            else:
                for x in range(0, int(dx), -1):
                    result_points.append(
                        (int(prev_point[0] + x), int(prev_point[1] + (dy / dx) * x))
                    )
                    result_speeds.append(angle)
        else:
            if point[1] >= prev_point[1] and point[0] >= prev_point[0]:
                for y in range(int(dy)):
                    result_points.append(
                        (int(prev_point[0] + (dx / dy) * y), int(prev_point[1] + y))
                    )
                    result_speeds.append(angle)
            elif point[1] >= prev_point[1] and point[0] < prev_point[0]:
                for y in range(int(dy)):
                    result_points.append(
                        (int(prev_point[0] + (dx / dy) * y), int(prev_point[1] + y))
                    )
                    result_speeds.append(angle)
            elif point[1] < prev_point[1] and point[0] >= prev_point[0]:
                for y in range(0, int(dy), -1):
                    result_points.append(
                        (int(prev_point[0] + (dx / dy) * y), int(prev_point[1] + y))
                    )
                    result_speeds.append(angle)
            else:
                for y in range(0, int(dy), -1):
                    result_points.append(
                        (int(prev_point[0] + (dx / dy) * y), int(prev_point[1] + y))
                    )
                    result_speeds.append(angle)
        prev_point = point
    return result_points, result_speeds


def trajectory(
    ctrlpoints: list[tuple[int, int]],
) -> tuple[list[tuple[int, int]], list[float]]:
    curve = BSpline.Curve()
    curve.degree = 2
    curve.ctrlpts = ctrlpoints
    curve.delta = max(1 / len(ctrlpoints) / 4, 0.01)  # heuristically chosen
    curve.knotvector = utilities.generate_knot_vector(curve.degree, len(curve.ctrlpts))
    result_points, result_angles = _interpolation_points(curve.evalpts)
    if result_points[-1] != ctrlpoints[-1]:
        result_points.append(
            ctrlpoints[-1]
        )  # (hacky) add the last point if it's not already there
        result_angles.append(result_angles[-1])
    return result_points, result_angles


class Trajectory:
    def __init__(self, ctrlpoints: list[tuple[int, int]]) -> None:
        self.ctrlpoints = ctrlpoints
        self._curve = BSpline.Curve()
        self._curve.degree = 2
        self._curve.ctrlpts = ctrlpoints
        self._curve.delta = max(1 / len(ctrlpoints) / 4, 0.01)  # heuristically chosen
        self._curve.knotvector = utilities.generate_knot_vector(
            self._curve.degree, len(self._curve.ctrlpts)
        )
        self.points, self.angles = _interpolation_points(self._curve.evalpts)
        # (hacky) make sure the last control point is included
        if self.points[-1] != ctrlpoints[-1]:
            self.points.append(ctrlpoints[-1])
            self.angles.append(self.angles[-1])
        assert len(self.points) == len(self.angles)


def _init_spline_trajectories():
    curve_ctrlpts_options = [
        [(2, 82), (1050, 268), (949, 883), (137, 882), (83, 252), (1075, 93)],
        [(2, 82), (599, 325), (580, 876), (137, 882), (50, 421), (218, 3)],
        [(1071, 4), (139, 288), (145, 768), (978, 654), (418, 4)],
        [
            (1071, 4),
            (614, 484),
            (643, 751),
            (1014, 725),
            (1008, 421),
            (91, 401),
            (67, 713),
            (415, 762),
            (494, 471),
            (2, 6),
        ],
        [(779, 3), (559, 263), (908, 511), (543, 817), (804, 1080)],
        [(228, 0), (371, 127), (140, 500), (371, 764), (195, 1078)],
        [(150, 12), (145, 1059), (997, 1054), (952, 8)],
    ]

    return [trajectory(ctrlpoints) for ctrlpoints in curve_ctrlpts_options]


class AnimatedSprite(Sprite):
    def __init__(self, animation: Animation, *groups) -> None:
        super().__init__(*groups)
        self.animation = animation
        self.image = self.animation.get_current_frame()
        self.rect = self.image.get_rect()
        self.rect.top = 0
        self.rect.left = 0
        self.angle = 0.0
        self.animation_end_handler = None

    def set_animation(self, animation: Animation, reset_angle=False) -> None:
        self.animation = animation
        if reset_angle:
            self.angle = 0.0
        self.image = self.animation.get_current_frame()
        if self.angle != 0:
            self.image = pygame.transform.rotate(self.image, self.angle)
        new_rect = self.image.get_rect()
        new_rect.center = self.rect.center
        self.rect = new_rect

    def on_animation_end(self, handler) -> "AnimatedSprite":
        self.animation_end_handler = handler
        return self

    def update(self, dt: float) -> None:
        if self.animation.is_finished():
            if self.animation_end_handler:
                self.animation_end_handler(self)
            return
        self.animation.update(dt)
        self.image = self.animation.get_current_frame()
        if self.angle != 0:
            self.image = pygame.transform.rotate(self.image, self.angle)
        new_rect = self.image.get_rect()
        new_rect.center = self.rect.center
        self.rect = new_rect


class TrajectorySprite(AnimatedSprite):
    def __init__(self, animation: Animation, trajectory: Trajectory, *groups) -> None:
        super().__init__(animation, *groups)
        self.trajectory = trajectory
        self.trajectory_idx = 0
        self.rect.center = self.trajectory.points[self.trajectory_idx]
        self.trajectory_end_handler = None

    def on_trajectory_end(self, handler) -> "TrajectorySprite":
        self.trajectory_end_handler = handler
        return self

    def update(self, dt: float) -> None:
        prev_idx = self.trajectory_idx
        self.trajectory_idx += int((150 * dt))
        if self.trajectory_idx < len(self.trajectory.points):
            self.angle = (
                round((-self.trajectory.angles[self.trajectory_idx] + 90) / 18) * 18
            )
            super().update(dt)
            self.rect.center = self.trajectory.points[self.trajectory_idx]
        else:
            self.angle = round((-self.trajectory.angles[-1] + 90) / 18) * 18
            super().update(dt)
            self.rect.center = self.trajectory.points[-1]
            if prev_idx < len(self.trajectory.points) and self.trajectory_end_handler:
                self.trajectory_end_handler(self)


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
