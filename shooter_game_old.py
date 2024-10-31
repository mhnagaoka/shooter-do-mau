import pygame
from pygame import Surface

import engine
from animation import Animation
from bullet_old import BulletFactory
from crosshair_old import Crosshair
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
        sprite_sheets[3].subsurface((0, 0, 8, 8)),  # 8 bullet-3
        sprite_sheets[4].subsurface((0, 0, 32, 32)),  # 9 laser
        sprite_sheets[5].subsurface((0, 0, 4, 32)),  # 10 laser-2
        sprite_sheets[6].subsurface((0, 0, 11, 11)),  # 11 crosshair
        sprite_sheets[7].subsurface((0, 0, 31, 31)),  # 12 crosshair-2
        sprite_sheets[8].subsurface((0, 0, 16, 16)),  # 13 explosion frame 0
        sprite_sheets[8].subsurface((16, 0, 16, 16)),  # 14 explosion frame 1
        sprite_sheets[8].subsurface((0, 16, 16, 16)),  # 15 explosion frame 2
        sprite_sheets[8].subsurface((16, 16, 16, 16)),  # 16 explosion frame 3
        sprite_sheets[8].subsurface((0, 32, 16, 16)),  # 17 explosion frame 4
        sprite_sheets[8].subsurface((16, 32, 16, 16)),  # 18 explosion frame 5
    ]
    scaled_sprites = [pygame.transform.scale2x(s) for s in cropped_sprites]
    scaled_sprites[13:19] = [pygame.transform.scale2x(s) for s in scaled_sprites[13:19]]
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
        self.crosshair = Crosshair([self.scaled_sprites[12]], self.crosshair_group)
        self.bullet_group = pygame.sprite.RenderPlain()
        self.bullet_factory = BulletFactory([self.scaled_sprites[10]])
        self.turret_bullet_factory = TurretBulletFactory([self.scaled_sprites[7]])
        self.enemy_group = pygame.sprite.RenderPlain()
        self.enemy_factory_group = pygame.sprite.Group()
        engine.SquadronEnemyFactory(0.5, 1, 6, self.enemy_factory_group)

    def create_explosion(self) -> Animation:
        explosion = Animation(self.scaled_sprites[13:19], 0.01, False)
        return explosion

    def process_frame(self, dt: float):
        self.dt = dt

        if not any(sprite.alive() for sprite in self.enemy_factory_group):
            engine.ParallelEnemyFactory(
                [
                    engine.CompositeEnemyFactory(
                        [
                            engine.SquadronEnemyFactory(0.15, 5, 0),
                            engine.SquadronEnemyFactory(0.15, 5, 1),
                            engine.SquadronEnemyFactory(0.15, 5, 2),
                            engine.SquadronEnemyFactory(0.15, 5, 3),
                        ]
                    ),
                    engine.CompositeEnemyFactory(
                        [
                            engine.SquadronEnemyFactory(0.5, 6, 4),
                            engine.SquadronEnemyFactory(0.5, 6, 5),
                            engine.SquadronEnemyFactory(0.5, 6, 6),
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

        collision_result = pygame.sprite.groupcollide(
            self.bullet_group, self.enemy_group, True, False
        )
        for kills in collision_result.values():
            for enemy_killed in kills:
                enemy_killed.set_animation(self.create_explosion(), True)
