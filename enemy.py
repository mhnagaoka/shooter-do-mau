import pygame
from pygame import Rect, Vector2
from pygame.sprite import Sprite
from pygame.surface import Surface
from geomdl import BSpline
from geomdl import utilities


def interpolation_points(points: list[(float, float)]) -> list[(float, float)]:
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
            


class Enemy(Sprite):
    def __init__(self, images: list[Surface], *groups) -> None:
        super().__init__(*groups)
        self.image = images[0]
        self.rect = self.image.get_rect()
        self.pos = None

    def update(self, game: "shooter.Shooter") -> None:
        if self.pos is None:
            self.pos = Vector2(
                game.screen.get_width() * 0.1,
                game.screen.get_height() * 0.1,
            )
            self.brand_new = False
        else:
            self.pos.x += 100 * game.dt
        if self.pos.x > game.screen.get_width():
            self.kill()
        self.rect.topleft = self.pos


class DumbEnemy(Sprite):
    def __init__(self, images: list[Surface], *groups) -> None:
        super().__init__(*groups)
        self.image = images[0]
        self.rect = self.image.get_rect()
        self.rect.top = -self.rect.height
        self.pos = None

    def update(self, game: "shooter.Shooter") -> None:
        if self.pos is None:
            self.pos = Vector2(game.player.rect.x, self.rect.top)
        self.pos.y += 600 * game.dt
        if self.pos.y > game.screen.get_height():
            self.kill()
        self.rect.topleft = self.pos

class SplineEnemy(Sprite):
    def __init__(self, images: list[Surface], *groups) -> None:
        super().__init__(*groups)
        self.image = images[0]
        self.rect = self.image.get_rect()
        self.rect.top = -self.rect.height
        self.pos = None
        self.curve = BSpline.Curve()
        self.curve.degree = 2
        # self.curve.ctrlpts = [(2, 82), (1050, 268), (949, 883), (137, 882), (83, 252), (1075, 93)]
        # self.curve.ctrlpts = [(2, 82), (599, 325), (580, 876), (137, 882), (50, 421), (218, 3)]
        # self.curve.ctrlpts = [(1071, 4), (139, 288), (145, 768), (978, 654), (418, 4)]
        self.curve.ctrlpts = [(1071, 4), (614, 484), (643, 751), (1014, 725), (1008, 421), (91, 401), (67, 713), (415, 762), (494, 471), (2, 6)]
        self.curve.knotvector = utilities.generate_knot_vector(self.curve.degree, len(self.curve.ctrlpts))
        self.current_point = 0
        self.pos = Vector2(self.curve.ctrlpts[0][0], self.curve.ctrlpts[0][1])
        self.trajectory = interpolation_points(self.curve.evalpts)

    def update(self, game: "shooter.Shooter") -> None:
        pygame.draw.lines(game.screen, "white",0,self.curve.evalpts,width=10)
        for i in range(len(self.trajectory)):
            pygame.draw.circle(game.screen, "red", self.trajectory[i], 1)
        if self.current_point < len(self.trajectory):
            self.pos = Vector2(self.trajectory[self.current_point][0], self.trajectory[self.current_point][1])
            self.current_point += int(600 * game.dt)
        else:
            self.kill()
        self.rect.center = self.pos


class PeriodicEnemyFactory(Sprite):
    def __init__(self, period: float, *groups) -> None:
        super().__init__(*groups)
        self.count_down = 0
        self.image = Surface((0, 0))
        self.rect = self.image.get_rect()
        self.period = period

    def update(self, game: "shooter.Shooter") -> None:
        if self.count_down <= 0:
            SplineEnemy([game.scaled_sprites[5]], game.enemy_group)
            self.count_down = self.period
        else:
            self.count_down -= game.dt


class SquadronEnemyFactory(Sprite):
    def __init__(self, period: float, size: int, *groups) -> None:
        super().__init__(*groups)
        self.count_down = 0
        self.image = Surface((0, 0))
        self.rect = self.image.get_rect()
        self.period = period
        self.size = size

    def update(self, game: "shooter.Shooter") -> None:
        if self.count_down <= 0:
            if self.size > 0:
                enemy = SplineEnemy([game.scaled_sprites[5]], game.enemy_group)
                enemy.pos = Vector2(game.screen.get_width() * 0.75, -enemy.rect.height)
                self.size -= 1
                self.count_down = self.period
            else:
                self.kill()
        else:
            self.count_down -= game.dt
    