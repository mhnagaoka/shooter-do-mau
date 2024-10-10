import pygame
from pygame import Surface

import enemy
from bullet import BulletFactory
from crosshair import Crosshair
from player import Player
from turret_bullet import TurretBulletFactory


def _crop_sprites(sprite_sheets: list[Surface]):
    # https://ezgif.com/crop/ezgif-1-7dc8bcb030.png
    cropped_sprites = [
        sprite_sheets[0].subsurface((48, 38, 35, 37)),  # 0 player banking left 2
        sprite_sheets[0].subsurface((88, 38, 35, 37)),  # 1 player banking left 1
        sprite_sheets[0].subsurface((134, 38, 35, 37)),  # 2 player neutral
        sprite_sheets[0].subsurface((182, 38, 35, 37)),  # 3 player banking right 1
        sprite_sheets[0].subsurface((222, 38, 35, 37)),  # 4 player banking right 2
        sprite_sheets[0].subsurface((40, 147, 45, 37)),  # 5 green enemy
        sprite_sheets[1].subsurface((0, 0, 6, 8)),  # 6 bullet
        sprite_sheets[2].subsurface((0, 0, 8, 8)),  # 7 bullet-2
        sprite_sheets[3].subsurface((0, 0, 32, 32)),  # 8 laser
        sprite_sheets[4].subsurface((0, 0, 4, 32)),  # 9 laser-2
        sprite_sheets[5].subsurface((0, 0, 11, 11)),  # 10 crosshair
        sprite_sheets[6].subsurface((0, 0, 31, 31)),  # 11 crosshair-2
    ]
    scaled_sprites = [pygame.transform.scale2x(s) for s in cropped_sprites]
    # scaled_sprites = [pygame.transform.scale(s, (s.get_width() * 1.5, s.get_height() * 1.5)) for s in cropped_sprites]
    # scaled_sprites = cropped_sprites[:]
    return (cropped_sprites, scaled_sprites)


class ShooterGame:
    def __init__(self, screen: Surface, sprite_sheets: list[Surface]) -> None:
        self.screen = screen
        self.running = True
        self.dt = 0.0
        self.cropped_sprites, self.scaled_sprites = _crop_sprites(sprite_sheets)
        self.player_pos = pygame.Vector2(
            screen.get_width() / 2, screen.get_height() * 0.75
        )
        self.player_group = pygame.sprite.GroupSingle()
        self.player = Player(self.scaled_sprites, self.player_group)
        self.crosshair_group = pygame.sprite.GroupSingle()
        self.crosshair = Crosshair([self.scaled_sprites[11]], self.crosshair_group)
        self.bullet_group = pygame.sprite.RenderPlain()
        self.bullet_factory = BulletFactory([self.scaled_sprites[9]])
        self.turret_bullet_factory = TurretBulletFactory([self.scaled_sprites[7]])
        self.enemy_group = pygame.sprite.RenderPlain()
        self.enemy_factory_group = pygame.sprite.Group()
        enemy.SquadronEnemyFactory(0.5, 1, 6, self.enemy_factory_group)

    def process_frame(self, dt: float):
        self.dt = dt

        if not any(sprite.alive() for sprite in self.enemy_factory_group):
            enemy.ParallelEnemyFactory(
                [
                    enemy.CompositeEnemyFactory(
                        [
                            enemy.SquadronEnemyFactory(0.15, 5, 0),
                            enemy.SquadronEnemyFactory(0.15, 5, 1),
                            enemy.SquadronEnemyFactory(0.15, 5, 2),
                            enemy.SquadronEnemyFactory(0.15, 5, 3),
                        ]
                    ),
                    enemy.CompositeEnemyFactory(
                        [
                            enemy.SquadronEnemyFactory(0.5, 6, 4),
                            enemy.SquadronEnemyFactory(0.5, 6, 5),
                            enemy.SquadronEnemyFactory(0.5, 6, 6),
                        ]
                    ),
                ],
                self.enemy_factory_group,
            )

        self.player_group.update(self)
        self.crosshair_group.update(self)
        self.bullet_group.update(self)
        self.enemy_group.update(self)
        self.enemy_factory_group.update(self)

        self.player_group.draw(self.screen)
        self.crosshair_group.draw(self.screen)
        self.bullet_group.draw(self.screen)
        self.enemy_group.draw(self.screen)

        pygame.sprite.groupcollide(self.bullet_group, self.enemy_group, True, True)
