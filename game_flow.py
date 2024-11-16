import random
from typing import TYPE_CHECKING, Generator

import pygame

from enemy import Brain, InsectEnemy, RedEnemy
from engine import (
    KeyboardTrajectoryProvider,
    LinearSegmentsTrajectoryProvider,
    SeekingTrajectoryProvider,
    StraightTrajectoryProvider,
)

if TYPE_CHECKING:
    from shooter_game import ShooterGame


class GameState:
    available_ctrlpoints = [
        [
            (188, -10),
            (30, 135),
            (28, 163),
            (46, 182),
            (73, 175),
            (211, 58),
            (231, 58),
            (244, 75),
            (242, 103),
            (53, 298),
        ],
        list(
            reversed(
                [
                    (188, -10),
                    (30, 135),
                    (28, 163),
                    (46, 182),
                    (73, 175),
                    (211, 58),
                    (231, 58),
                    (244, 75),
                    (242, 103),
                    (53, 298),
                ]
            )
        ),
        [
            (42, -10),
            (42, 123),
            (52, 140),
            (72, 149),
            (228, 149),
            (241, 141),
            (245, 124),
            (245, -10),
        ],
        list(
            reversed(
                [
                    (42, -10),
                    (42, 123),
                    (52, 140),
                    (72, 149),
                    (228, 149),
                    (241, 141),
                    (245, 124),
                    (245, -10),
                ]
            )
        ),
        [
            (298, -10),
            (250, 50),
            (200, 100),
            (150, 150),
            (100, 200),
            (50, 250),
            (50, 250),
            (100, 200),
            (150, 150),
            (200, 100),
            (250, 50),
            (298, -10),
        ],
        [
            (-10, 150),
            (50, 100),
            (100, 50),
            (150, 0),
            (200, 50),
            (250, 100),
            (250, 200),
            (200, 250),
            (150, 268),
            (100, 250),
            (50, 200),
            (-10, 150),
        ],
        [
            (150, -10),
            (100, 50),
            (50, 100),
            (0, 150),
            (50, 200),
            (100, 250),
            (150, 268),
            (200, 250),
            (250, 200),
            (268, 150),
            (250, 100),
            (200, 50),
            (150, -10),
        ],
        [
            (0, -10),
            (50, 50),
            (100, 100),
            (150, 150),
            (200, 200),
            (250, 250),
            (268, 268),
            (250, 250),
            (200, 200),
            (150, 150),
            (100, 100),
            (50, 50),
            (0, -10),
        ],
        [
            (10, -10),
            (50, 50),
            (100, 100),
            (150, 150),
            (200, 200),
            (250, 250),
            (270, 270),
            (250, 250),
            (200, 200),
            (150, 150),
            (100, 100),
            (50, 50),
            (10, -10),
        ],
        [
            (-10, 20),
            (60, 60),
            (110, 110),
            (160, 160),
            (210, 210),
            (260, 260),
            (280, 280),
            (260, 260),
            (210, 210),
            (160, 160),
            (110, 110),
            (60, 60),
            (-10, 20),
        ],
    ]

    def __init__(self, game: "ShooterGame") -> None:
        self.game = game
        self.update_difficulty(0)

    @property
    def difficulty(self) -> float:
        return self._difficulty

    def update_difficulty(self, value: int) -> None:
        self._difficulty = value
        difficulty_factor = min(max(value / 100, 0.0), 1.0)  # clamp between 0 and 1

        self.ctrlpoints = random.choice(self.available_ctrlpoints)
        self.insect_speed = pygame.math.lerp(50.0, 120.0, difficulty_factor)
        self.insect_spawn_timer = 20 / self.insect_speed  # time to fly 20 px
        self.insect_shot_speed = pygame.math.lerp(80.0, 160.0, difficulty_factor)
        self.insect_cannon_timer = pygame.math.lerp(2.0, 0.5, difficulty_factor)
        self.double_squadron = difficulty_factor
        self.squadron_size = round(pygame.math.lerp(5, 15, difficulty_factor))
        self.insect_type = random.randint(
            0, len(self.game.factory.surfaces["insect-enemies"]) - 1
        )


class GameFlow:
    def __init__(self, game: "ShooterGame") -> None:
        self.game = game
        self.generator = self._game_script()
        next(self.generator)

    def update(self, dt: float) -> None:
        try:
            self.generator.send(dt)
        except StopIteration:
            # The game has ended \o/
            if self.game.player.alive():
                self.game.player.kill()

    def show_messages(self, *messages: str) -> None:
        self.game.player_messages.clear()
        self.game.player_messages.extend(messages)

    def create_insect_enemy(
        self,
        state: GameState,
    ) -> None:
        if random.random() < state.double_squadron:
            provider = LinearSegmentsTrajectoryProvider(
                state.ctrlpoints, state.insect_speed, -8
            )
            insect_enemy = InsectEnemy(
                self.game.factory,
                state.insect_type,
                provider,
                self.game.player_group,
                self.game.enemy_bullet_group,
                self.game.enemy_group,
            ).on_trajectory_end(lambda s: s.kill())
            insect_enemy.shot_speed = state.insect_shot_speed
            insect_enemy.cannon_timer = state.insect_cannon_timer

            provider = LinearSegmentsTrajectoryProvider(
                state.ctrlpoints, state.insect_speed, 8
            )
            insect_enemy = InsectEnemy(
                self.game.factory,
                state.insect_type,
                provider,
                self.game.player_group,
                self.game.enemy_bullet_group,
                self.game.enemy_group,
            ).on_trajectory_end(lambda s: s.kill())
            insect_enemy.shot_speed = state.insect_shot_speed
            insect_enemy.cannon_timer = state.insect_cannon_timer
        else:
            provider = LinearSegmentsTrajectoryProvider(
                state.ctrlpoints, state.insect_speed, 0
            )
            insect_enemy = InsectEnemy(
                self.game.factory,
                state.insect_type,
                provider,
                self.game.player_group,
                self.game.enemy_bullet_group,
                self.game.enemy_group,
            ).on_trajectory_end(lambda s: s.kill())
            insect_enemy.shot_speed = state.insect_shot_speed
            insect_enemy.cannon_timer = state.insect_cannon_timer

    def create_red_enemy(self, state: GameState) -> None:
        off_screen_offset = 10
        screen_rect = self.game.screen.get_rect()
        initial_pos = (screen_rect.centerx, screen_rect.top - off_screen_offset)
        final_pos = (
            screen_rect.centerx,
            screen_rect.bottom + off_screen_offset,
        )
        # If there is a player, move towards it
        if self.game.player_group:
            player_pos = self.game.player_group.sprites()[0].rect.center
            # Extrapolate the player position to the bottom of the screen
            final_pos = (
                initial_pos[0]
                + (player_pos[0] - initial_pos[0])
                * (screen_rect.bottom + off_screen_offset - initial_pos[1])
                / (player_pos[1] - initial_pos[1]),
                screen_rect.bottom + off_screen_offset,
            )
        straight = StraightTrajectoryProvider(initial_pos, final_pos, None, 120.0)

        RedEnemy(
            self.game.factory,
            straight,
            self.game.player_group,
            self.game.enemy_bullet_group,
            self.game.enemy_group,
        ).on_trajectory_end(lambda s: s.kill())

    def create_bonus_red_enemy(self) -> None:
        off_screen_offset = 10
        screen_rect = self.game.screen.get_rect()
        random_x = random.randint(0, screen_rect.width)
        initial_pos = (random_x, screen_rect.top - off_screen_offset)
        final_pos = (
            random_x,
            screen_rect.bottom + off_screen_offset,
        )
        straight = StraightTrajectoryProvider(initial_pos, final_pos, None, 160.0)

        RedEnemy(
            self.game.factory,
            straight,
            self.game.player_group,
            self.game.enemy_bullet_group,
            self.game.enemy_group,
        ).on_trajectory_end(lambda s: s.kill())

    def create_boss(self, state: GameState) -> list[Brain]:
        result: list[Brain] = []
        if state.difficulty < 40:
            return result
        elif 40 <= state.difficulty < 60:
            # one more
            trajectory = SeekingTrajectoryProvider(
                (144, 288), 0, 20.0, 2.0, self.game.player
            )
            result.append(
                Brain(
                    self.game.factory,
                    trajectory,
                    self.game.player_group,
                    self.game.enemy_bullet_group,
                    self.game.enemy_group,
                )
            )
        elif 60 <= state.difficulty < 80:
            # two more
            trajectory = SeekingTrajectoryProvider(
                (-20, 144), 0, 20.0, 2.0, self.game.player
            )
            Brain(
                self.game.factory,
                trajectory,
                self.game.player_group,
                self.game.enemy_bullet_group,
                self.game.enemy_group,
            )
            trajectory = SeekingTrajectoryProvider(
                (288, 144), 0, 20.0, 2.0, self.game.player
            )
            Brain(
                self.game.factory,
                trajectory,
                self.game.player_group,
                self.game.enemy_bullet_group,
                self.game.enemy_group,
            )
        else:
            # three more
            trajectory = SeekingTrajectoryProvider(
                (144, 288), 0, 20.0, 2.0, self.game.player
            )
            result.append(
                Brain(
                    self.game.factory,
                    trajectory,
                    self.game.player_group,
                    self.game.enemy_bullet_group,
                    self.game.enemy_group,
                )
            )
            trajectory = SeekingTrajectoryProvider(
                (-20, 144), 0, 20.0, 2.0, self.game.player
            )
            result.append(
                Brain(
                    self.game.factory,
                    trajectory,
                    self.game.player_group,
                    self.game.enemy_bullet_group,
                    self.game.enemy_group,
                )
            )
            trajectory = SeekingTrajectoryProvider(
                (288, 144), 0, 20.0, 2.0, self.game.player
            )
            result.append(
                Brain(
                    self.game.factory,
                    trajectory,
                    self.game.player_group,
                    self.game.enemy_bullet_group,
                    self.game.enemy_group,
                )
            )
        return result

    def _wait(self, duration: float) -> Generator[None, float, None]:
        timer = duration
        while timer > 0:
            dt: float = yield
            timer -= dt

    def _wait_enemies_to_die(self) -> Generator[None, float, None]:
        while self.game.enemy_group:
            yield

    def _wave(self, state: GameState) -> Generator[None, float, None]:
        self.create_red_enemy(state)
        for _ in range(state.squadron_size):
            self.create_insect_enemy(state)
            yield from self._wait(state.insect_spawn_timer)

    def _bonus_round(self) -> Generator[None, float, None]:
        self.show_messages("Bonus round")
        yield from self._wait(1.0)
        self.show_messages()
        yield from self._wait(0.5)
        for _ in range(10):
            self.create_bonus_red_enemy()
            yield from self._wait(1.0)
        # wait for all enemies to be defeated or go away
        while self.game.enemy_group:
            dt: float = yield
        self.show_messages("Bonus round completed")
        yield from self._wait(1.0)
        self.show_messages()
        yield from self._wait(0.5)

    def _intro(self) -> Generator[None, float, None]:
        # Move the player ship to the center of the screen
        self.show_messages("Get ready!", "", "")
        keyboard: KeyboardTrajectoryProvider = self.game.player.trajectory_provider
        self.game.player.trajectory_provider = StraightTrajectoryProvider(
            (keyboard.position.x, self.game.screen.get_height() + 10),
            (keyboard.position.x, keyboard.position.y),
            None,
            80.0,
        )
        while not self.game.player.trajectory_provider.is_finished():
            yield
        # Give control back to the player
        self.game.player.trajectory_provider = keyboard
        self.show_messages("GO! GO! GO!", "", "")
        yield from self._wait(1.0)
        self.show_messages()
        yield from self._wait(0.5)

    def _boss_cut_scene(self) -> Generator[None, float, None]:
        self.game.player.disable_shooting()
        self.show_messages("Boss incoming!", "", "")
        yield from self._wait(1.0)
        self.show_messages()
        yield from self._wait(0.5)
        keyboard: KeyboardTrajectoryProvider = self.game.player.trajectory_provider
        self.game.player.trajectory_provider = LinearSegmentsTrajectoryProvider(
            [self.game.player.rect.center, self.game.screen.get_rect().center], 80.0, 0
        )
        keyboard.position = pygame.Vector2(self.game.screen.get_rect().center)
        trajectory = LinearSegmentsTrajectoryProvider([(144, -16), (144, 32)], 20.0, 0)
        brain = Brain(
            self.game.factory,
            trajectory,
            self.game.player_group,
            self.game.enemy_bullet_group,
            self.game.enemy_group,
        )
        brain.disable_shooting()
        while not self.game.player.trajectory_provider.is_finished():
            yield
        while not trajectory.is_finished():
            yield
        self.show_messages("Prepare to die!", "", "")
        yield from self._wait(1.0)
        self.show_messages()
        yield from self._wait(0.5)
        brain.trajectory_provider = SeekingTrajectoryProvider(
            (144, 32), 90, 20.0, 2.0, self.game.player
        )

        brain.enable_shooting()
        self.game.player.enable_shooting()
        self.game.player.trajectory_provider = keyboard

    def _game_script(self) -> Generator[None, float, None]:
        state = GameState(self.game)

        # # Boss test
        # cannon = TurboLaser(self.game.factory, self.game.player_bullet_group, None)
        # cannon.upgrade()
        # cannon.upgrade()
        # cannon.upgrade()
        # cannon.upgrade()
        # cannon.upgrade()
        # self.game.player.equip(cannon=cannon)
        # state.update_difficulty(90)
        # yield from self._boss_cut_scene()
        # self.create_boss(state)
        # yield from self._wait_enemies_to_die()
        # yield from self._wait(2.0)
        # return

        # Intro
        yield from self._intro()

        # Main gameplay loop
        while state.difficulty <= 100:
            # Send 10 waves of enemies
            for wave in range(10):
                if wave == 5:
                    yield from self._bonus_round()
                yield from self._wave(state)
                yield from self._wait_enemies_to_die()
                state.update_difficulty(state.difficulty + 2)
            # Send a boss
            yield from self._boss_cut_scene()
            self.create_boss(state)
            yield from self._wait_enemies_to_die()
            yield from self._wait(1.0)
            self.show_messages("Get ready!", "", "")
            yield from self._wait(1.0)
            self.show_messages()
            yield from self._wait(0.5)

        # End game
        self.show_messages(
            "You did it!", "You defeated the enemy!", "Congratulations!!!"
        )
        yield from self._wait(5.0)
        self.show_messages()
