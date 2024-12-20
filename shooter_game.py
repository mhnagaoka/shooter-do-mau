import random
from typing import Generator

import pygame
import pygame.event

import item
from animation import Animation
from enemy import Enemy, RedEnemy
from engine import (
    Keybindings,
    KeyboardTrajectoryProvider,
    MouseTrajectoryProvider,
    StraightTrajectoryProvider,
    TrajectorySprite,
    VirtualKeyboard,
    default_keybindings,
)
from game_flow import GameFlow
from player import Cannon, FlakCannon, Minigun, Player, Shield, TurboLaser, Turret
from shot import Shot
from surface_factory import SurfaceFactory


class CrossHair(TrajectorySprite):
    pass


def hit_box_collide(enemy: Enemy, candidate: pygame.sprite.Sprite) -> bool:
    hb = enemy.get_hit_box()
    hb.center = enemy.rect.center
    return hb.colliderect(candidate.rect)


class ShooterGame:
    def __init__(
        self,
        build_info: str | None,
        size: tuple[int, int],
        scale_factor: float,
        asset_folders: list[str],
        keybindings: Keybindings = default_keybindings,
    ) -> None:
        self.build_info = build_info
        self.scale_factor = scale_factor
        self.screen = pygame.Surface(size)
        self.factory = SurfaceFactory(asset_folders)
        self.keybindings = keybindings
        self.virtual_keyboard = VirtualKeyboard()
        self.font = pygame.font.Font("assets/mystery-font.ttf", 12)
        self.small_font = pygame.font.Font("assets/mystery-font.ttf", 8)
        self.bg = pygame.image.load("bg/nebula_288.png").convert()
        self.bg.set_alpha(96)
        self.player_group = pygame.sprite.RenderPlain()
        self.crosshair_group = pygame.sprite.RenderPlain()
        self.player_bullet_group = pygame.sprite.RenderPlain()
        self.enemy_group = pygame.sprite.RenderPlain()
        self.explosion_group = pygame.sprite.RenderPlain()
        self.enemy_bullet_group = pygame.sprite.RenderPlain()
        self.item_group = pygame.sprite.RenderPlain()
        self._create_player()
        self._create_crosshair()
        self.progress = 0
        self.score = 0
        self.hi_score = 0
        self.player_messages: list[str] = []
        self.generators = [self._virtual_keyboard_loop(), self._main_loop()]
        for g in self.generators:
            next(g)
        self.menu_generator = self._render_menu()
        next(self.menu_generator)

    def update(self, events: list[pygame.event.Event], dt: float, fps: float) -> None:
        for g in self.generators:
            g.send((events, dt, fps))

    def _create_player(self) -> None:
        boundary = self.screen.get_rect().copy()
        boundary.update(10, 10, boundary.width - 20, boundary.height - 22)
        keyboard = KeyboardTrajectoryProvider(
            boundary,
            boundary.center,
            150.0,
            0.0,
            self.keybindings,
            self.virtual_keyboard,
        )
        self.player = Player(
            self.scale_factor,
            self.factory,
            keyboard,
            self.virtual_keyboard,
            self.player_group,
        )
        turret = Turret(self.factory, self.player_bullet_group)
        self.player.equip(
            cannon=Cannon(self.factory, self.player_bullet_group),
            turret=turret,
            turret2=turret,
            shield=Shield(),
        )

    def _create_crosshair(self) -> TrajectorySprite:
        mouse = MouseTrajectoryProvider(
            self.scale_factor, self.screen.get_rect().center
        )
        crosshair_anim = Animation.static(self.factory.surfaces["shots"][0])
        return CrossHair(crosshair_anim, 0.0, mouse, self.crosshair_group)

    def _clean_up_oob_stuff(self) -> None:
        for b in self.player_bullet_group:
            if not self.screen.get_rect().colliderect(b.rect):
                b.kill()
        for b in self.enemy_bullet_group:
            if not self.screen.get_rect().colliderect(b.rect):
                b.kill()
        for i in self.item_group:
            if not self.screen.get_rect().colliderect(i.rect):
                i.kill()

    def _explode(self, sprite: TrajectorySprite, explosion_speed: float = 0.0):
        sprite.kill()
        explosion_frames = self.factory.surfaces["explosion"] + list(
            reversed(self.factory.surfaces["explosion"])
        )
        if isinstance(sprite.trajectory_provider, StraightTrajectoryProvider):
            trajectory_angle = -sprite.trajectory_provider.get_direction().angle_to(
                pygame.Vector2(1, 0)
            )
        else:
            trajectory_angle = None
        straight = StraightTrajectoryProvider(
            start=sprite.rect.center,
            end=None,
            angle=sprite.angle if not trajectory_angle else trajectory_angle,
            speed=explosion_speed,
        )
        TrajectorySprite(
            Animation(explosion_frames, 0.03), None, straight, self.explosion_group
        ).on_animation_end(lambda s: s.kill())
        # Some chance of enemy dropping a power capsule
        if isinstance(sprite, RedEnemy):
            random_angle = random.uniform(-45.0, 45.0)
            items = [
                item.PowerCapsule,
                item.Minigun,
                item.FlakCannon,
                item.TurboLaser,
                item.IceCream,
            ]
            constructor = random.choice(items)
            _item = constructor(
                self.factory,
                sprite.rect.center,
                sprite.angle + random_angle,
                self.item_group,
            )
            if constructor.__name__ == "PowerCapsule":
                _item.power = 100.0
        elif isinstance(sprite, Enemy) and random.random() < 0.5:
            random_angle = random.uniform(-45.0, 45.0)
            item.PowerCapsule(
                self.factory,
                sprite.rect.center,
                sprite.angle + random_angle,
                self.item_group,
            )

    def _check_bullet_collision(self) -> None:
        # Check for collisions between bullets and enemies
        enemy_collision_result = pygame.sprite.groupcollide(
            self.enemy_group, self.player_bullet_group, False, True, hit_box_collide
        )
        enemy: Enemy
        shots: list[Shot]
        for enemy, shots in enemy_collision_result.items():
            for shot in shots:
                if enemy.hit(shot):
                    self.score += 100
                    self._explode(enemy, 40.0)
                    break  # you can die only once
        # Check for collisions between bullets and player
        player_collision_result = pygame.sprite.groupcollide(
            self.player_group, self.enemy_bullet_group, False, True
        )
        # Multiple bullets may hit the player at the same time
        for bullets in player_collision_result.values():
            for _ in bullets:
                if self.player and self.player.hit(10.0):  # bullet damage
                    self.player.controls_enabled = False
                    self._explode(self.player, 0.0)
                    self.player = None
                    break
            if self.player is None:
                break
        # Check for collisions between bullets and items
        item_collision_result = pygame.sprite.groupcollide(
            self.item_group, self.player_bullet_group, False, True
        )
        for item_hit in item_collision_result.keys():
            self.score += 50
            self._explode(item_hit, 40.0)
        # TODO: Check for collisions between enemies and player

    def _check_item_collision(self) -> None:
        player_collision_result = pygame.sprite.groupcollide(
            self.player_group, self.item_group, False, True
        )
        player: Player
        for player, items in player_collision_result.items():
            for _item in items:
                # TODO: Ugly code, refactor
                if isinstance(_item, item.PowerCapsule):
                    player.power_source.charge_from(_item)
                elif isinstance(_item, item.IceCream):
                    player.power_source.supercharge()
                elif isinstance(_item, item.TurboLaser):
                    if player.cannon is not None and isinstance(
                        player.cannon, TurboLaser
                    ):
                        player.cannon.upgrade()
                    else:
                        player.equip(
                            cannon=TurboLaser(self.factory, self.player_bullet_group)
                        )
                elif isinstance(_item, item.Minigun):
                    if player.turret is not None and isinstance(player.turret, Minigun):
                        player.turret.upgrade()
                    else:
                        player.equip(
                            turret=Minigun(self.factory, self.player_bullet_group)
                        )
                elif isinstance(_item, item.FlakCannon):
                    if player.turret2 is not None and isinstance(
                        (player.turret2), FlakCannon
                    ):
                        player.turret2.upgrade()
                    else:
                        player.equip(
                            turret2=FlakCannon(self.factory, self.player_bullet_group)
                        )

    def draw_progress(self) -> None:
        text = self.font.render(f"{self.progress}", False, (255, 255, 255))
        coord = (5, 5)
        self.screen.blit(text, coord)

    def draw_fps(self, fps: float) -> None:
        text = self.small_font.render(f"{fps:.1f}", False, (255, 255, 255))
        coord = (5, 288 - text.get_height())
        self.screen.blit(text, coord)

    def draw_score(self) -> None:
        color = "white"
        if self.score >= self.hi_score:
            color = "yellow"
        text = self.font.render(f"{self.score}", False, color)
        coord = ((self.screen.get_width() - text.get_width()) // 2, 5)
        self.screen.blit(text, coord)

    def draw_hi_score(self) -> None:
        text = self.font.render(f"HI {self.hi_score}", False, (255, 255, 255))
        coord = (self.screen.get_width() - text.get_width() - 5, 5)
        self.screen.blit(text, coord)

    def draw_messages(self) -> None:
        texts = [
            self.font.render(m, False, (255, 255, 255)) for m in self.player_messages
        ]
        gap = 5
        total_height = sum(t.get_height() for t in texts) + gap * (len(texts) - 1)
        top = (self.screen.get_height() - total_height) // 2
        for i, _ in enumerate(self.player_messages):
            text = texts[i]
            left = (self.screen.get_width() - text.get_width()) // 2
            self.screen.blit(text, (left, top))
            top += text.get_height() + gap

    def _render_menu(self) -> Generator[None, float, None]:
        mode = 1  # 0: blink, 1: show
        text = self.font.render("Hit the space bar to start.", False, (255, 255, 255))
        coord = (
            self.screen.get_rect().centerx - text.get_width() // 2,
            self.screen.get_rect().centery - text.get_height() // 2,
        )
        if self.build_info is not None:
            build_info_text = self.small_font.render(
                self.build_info, False, (255, 255, 255)
            )
            build_info_coord = (
                self.screen.get_width() - build_info_text.get_width() - 5,
                self.screen.get_height() - build_info_text.get_height() - 5,
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
            if self.build_info is not None:
                self.screen.blit(build_info_text, build_info_coord)
            frame_count -= 1
            self.crosshair_group.update(dt)
            self.crosshair_group.draw(self.screen)
            self.draw_hi_score()

    def _virtual_keyboard_loop(
        self,
    ) -> Generator[None, tuple[list[pygame.event.Event], float, float], None]:
        while True:
            events, _, _ = yield
            for event in events:
                if event.type == pygame.USEREVENT:
                    if event.direction is not None:
                        self.virtual_keyboard.direction = event.direction
                    if event.fire is not None:
                        self.virtual_keyboard.fire = event.fire
                    print(self.virtual_keyboard)

    def _main_loop(
        self,
    ) -> Generator[None, tuple[list[pygame.event.Event], float, float], None]:
        game_flow = GameFlow(self)
        mode = 0  # 0, 1: menu, 10: game, 20, 21: game over
        while True:
            events, dt, fps = yield  # yields dt every time the game is updated
            self.screen.fill((0, 0, 0))
            self.screen.blit(self.bg, (0, 0))
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
                    elif mode == 0 and self.virtual_keyboard.fire:
                        mode = 1
                    elif mode == 1 and not self.virtual_keyboard.fire:
                        mode = 10
            elif mode == 10 or mode == 20 or mode == 21:
                game_flow.update(dt)
                self.explosion_group.update(dt)
                self.enemy_group.update(dt)
                self.player_group.update(dt)
                self.crosshair_group.update(dt)
                self.enemy_bullet_group.update(dt)
                self.player_bullet_group.update(dt)
                self.item_group.update(dt)
                self.item_group.draw(self.screen)
                self.enemy_group.draw(self.screen)
                self.player_group.draw(self.screen)
                self.crosshair_group.draw(self.screen)
                self.player_bullet_group.draw(self.screen)
                self.enemy_bullet_group.draw(self.screen)
                self.explosion_group.draw(self.screen)
                for enemy in self.enemy_group.sprites():
                    enemy.draw_power_bar(self.screen)
                for player in self.player_group.sprites():
                    player.draw_power_bar(self.screen)
                self.draw_fps(fps)
                self.draw_progress()
                self.draw_score()
                self.draw_hi_score()
                self.draw_messages()
                self._check_bullet_collision()
                self._check_item_collision()
                # Kill bullets that are out of bounds
                self._clean_up_oob_stuff()
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
                        False,
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
