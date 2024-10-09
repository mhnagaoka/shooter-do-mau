import pygame
from pygame import Rect, Vector2
from pygame.sprite import Sprite
from pygame.surface import Surface
from geomdl import BSpline
from geomdl import utilities


def _interpolation_points(points: list[(float, float)]) -> list[(float, float)]:
    result = []
    prev_point = None
    for point in points:
        if prev_point is None:
            prev_point = point
            continue
        dx = point[0] - prev_point[0]
        dy = point[1] - prev_point[1]
        if abs(dx) > abs(dy):
            if point[0] >= prev_point[0] and point[1] >= prev_point[1]:
                for x in range(int(dx)):
                    result.append((prev_point[0] + x, prev_point[1] + (dy / dx) * x))
            elif point[0] >= prev_point[0] and point[1] < prev_point[1]:
                for x in range(int(dx)):
                    result.append((prev_point[0] + x, prev_point[1] + (dy / dx) * x))
            elif point[0] < prev_point[0] and point[1] >= prev_point[1]:
                for x in range(0, int(dx), -1):
                    result.append((prev_point[0] + x, prev_point[1] + (dy / dx) * x))
            else:
                for x in range(0, int(dx), -1):
                    result.append((prev_point[0] + x, prev_point[1] + (dy / dx) * x))
        else:
            if point[1] >= prev_point[1] and point[0] >= prev_point[0]:
                for y in range(int(dy)):
                    result.append((prev_point[0] + (dx / dy) * y, prev_point[1] + y))
            elif point[1] >= prev_point[1] and point[0] < prev_point[0]:
                for y in range(int(dy)):
                    result.append((prev_point[0] + (dx / dy) * y, prev_point[1] + y))
            elif point[1] < prev_point[1] and point[0] >= prev_point[0]:
                for y in range(0, int(dy), -1):
                    result.append((prev_point[0] + (dx / dy) * y, prev_point[1] + y))
            else:
                for y in range(0, int(dy), -1):
                    result.append((prev_point[0] + (dx / dy) * y, prev_point[1] + y))
        prev_point = point
    return result


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
        [(150, 12), (145, 1059), (997, 1054), (952, 8)]
    ]

    def trajectory(ctrlpoints: list[tuple[int, int]]) -> list[tuple[int, int]]:
        curve = BSpline.Curve()
        curve.degree = 2
        curve.ctrlpts = ctrlpoints
        curve.knotvector = utilities.generate_knot_vector(
            curve.degree, len(curve.ctrlpts)
        )
        return _interpolation_points(curve.evalpts)

    return [trajectory(ctrlpoints) for ctrlpoints in curve_ctrlpts_options]


class SplineEnemy(Sprite):
    trajectories = _init_spline_trajectories()

    def __init__(self, images: list[Surface], trajectory_number: int, *groups) -> None:
        super().__init__(*groups)
        self.image = images[0]
        self.rect = self.image.get_rect()
        self.rect.top = -self.rect.height
        self.pos = None
        self.current_point = 0
        self.trajectory = SplineEnemy.trajectories[
            trajectory_number % len(SplineEnemy.trajectories)
        ]
        self.pos = Vector2(self.trajectory[0][0], self.trajectory[0][1])

    def update(self, game: "shooter.Shooter") -> None:
        # for i in range(len(self.trajectory)):
        #     pygame.draw.circle(game.screen, "red", self.trajectory[i], 1)
        if self.current_point < len(self.trajectory):
            self.pos = Vector2(
                self.trajectory[self.current_point][0],
                self.trajectory[self.current_point][1],
            )
            self.current_point += int(600 * game.dt)
        else:
            self.kill()
        self.rect.center = self.pos


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

    def update(self, game: "shooter.Shooter") -> None:
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

    def update(self, game: "shooter.Shooter") -> None:
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

    def update(self, game: "shooter.Shooter") -> None:
        all_dead = True
        for f in self.enemy_factories:
            if f.alive():
                f.update(game)
                all_dead = False
        if all_dead:
            self.kill()
