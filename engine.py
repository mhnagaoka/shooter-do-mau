from typing import Self
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Flag, auto
from typing import Generator, Optional

import pygame
from pygame import Vector2
from pygame.sprite import Sprite

from animation import Animation

SPRITE_DEBUG = os.getenv("SPRITE_DEBUG", "False").lower() in ("true", "1", "t")


class TrajectoryProvider(ABC):
    @abstractmethod
    def update(self, dt: float) -> None:
        pass

    @abstractmethod
    def get_current_position(self) -> tuple[int, int]:
        pass

    @abstractmethod
    def get_current_angle(self) -> float:
        pass

    @abstractmethod
    def is_finished(self) -> bool:
        pass


class StaticTrajectoryProvider(TrajectoryProvider):
    def __init__(self, position: tuple[int, int], angle: float) -> None:
        super().__init__()
        self._position = position
        self._angle = angle

    def get_current_position(self) -> tuple[int, int]:
        return self._position

    def get_current_angle(self) -> float:
        return self._angle

    def is_finished(self) -> bool:
        return False


class LinearSegmentsTrajectoryProvider(TrajectoryProvider):
    def __init__(
        self,
        ctrlpoints: list[tuple[int, int]],
        initial_speed: float,
        shift: float = 0.0,
    ) -> None:
        super().__init__()
        self._ctrlpoints = ctrlpoints
        self._initial_speed = initial_speed
        # Segment look-up table (distance range -> segment)
        self._segment_lut = []
        self._total_length = 0
        for i in range(len(ctrlpoints) - 1):
            begin = Vector2(ctrlpoints[i])
            end = Vector2(ctrlpoints[i + 1])
            delta = Vector2(end) - Vector2(begin)
            delta_length = round(delta.length())
            self._segment_lut.append(
                (self._total_length, self._total_length + delta_length, begin, end)
            )
            self._total_length += delta_length
        self._distance = 0.0
        self._position = ctrlpoints[0]
        self._angle = -(end - begin).angle_to(Vector2(1, 0))
        self.shift = shift

    def update(self, dt: float) -> None:
        self._distance += self._initial_speed * dt
        if self._distance > self._total_length:
            self._distance = self._total_length
        # find which segment we're in and interpolate
        for initial, final, begin, end in self._segment_lut:
            if initial <= self._distance <= final:
                pos_vec = begin.lerp(
                    end, (self._distance - initial) / (final - initial)
                )
                self._position = (int(pos_vec.x), int(pos_vec.y))
                self._angle = -(end - begin).angle_to(Vector2(1, 0))
                break

    def get_current_position(self) -> tuple[int, int]:
        if self.shift != 0.0:
            pos_vec = (
                Vector2(self._position)
                + Vector2(1, 0).rotate(90 + self._angle) * self.shift
            )
            return (int(pos_vec.x), int(pos_vec.y))
        return self._position

    def get_current_angle(self) -> float:
        return self._angle

    def is_finished(self) -> bool:
        return self._distance >= self._total_length


class StraightTrajectoryProvider(TrajectoryProvider):
    def __init__(
        self,
        start: tuple[int, int],
        end: Optional[tuple[int, int]],
        angle: Optional[float],
        speed: float,
        angular_speed: float = 0.0,
    ) -> None:
        self.start = start
        self.end = end
        self.speed = speed
        self.position = Vector2(start)
        if end is not None:
            self._direction = Vector2(end) - Vector2(start)
            self._distance = Vector2(end).distance_to(Vector2(start))
            self.angle = -self._direction.angle_to(Vector2(1, 0))
        elif angle is not None:
            self._direction = Vector2(1, 0).rotate(angle)
            self._distance = float("Infinity")
            self.angle = angle
        else:
            raise ValueError("Either end or angle must be provided")
        self.angular_speed = angular_speed
        self._direction.normalize_ip()

    def update(self, dt: float) -> None:
        self.position += self._direction * self.speed * dt
        self.angle += self.angular_speed * dt

    def get_current_position(self) -> tuple[int, int]:
        return (int(self.position.x), int(self.position.y))

    def get_current_angle(self) -> float:
        return self.angle

    def get_direction(self) -> Vector2:
        return self._direction

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


class SeekingTrajectoryProvider(TrajectoryProvider):
    def __init__(
        self,
        start: tuple[int, int],
        angle: float,
        speed: float,
        angular_speed: float,
        mark: "AnimatedSprite",
        length: Optional[float] = None,
    ):
        self.start = start
        self.speed = speed
        self.angular_speed = angular_speed
        self.angle = angle
        self.mark = mark
        self.position = Vector2(start)
        self.direction = Vector2(*self.mark.rect.center) - self.position
        self.length = length
        self.distance = 0.0
        super().__init__()

    def update(self, dt: float) -> None:
        if self.mark.alive():
            new_direction = Vector2(self.mark.rect.center) - self.position
            new_angle = -new_direction.angle_to(Vector2(1, 0))
            diff_angle = new_angle - self.angle
            if diff_angle > 180.0:
                diff_angle -= 360.0
            elif diff_angle < -180.0:
                diff_angle += 360.0
            max_diff = self.angular_speed
            if diff_angle > max_diff:
                new_angle = self.angle + max_diff
            elif diff_angle < -max_diff:
                new_angle = self.angle - max_diff
            self.angle = new_angle
            self.direction = Vector2(1, 0).rotate(new_angle)
        self.position += self.direction * self.speed * dt
        self.distance += self.speed * dt

    def get_current_position(self) -> tuple[int, int]:
        return (int(self.position.x), int(self.position.y))

    def get_current_angle(self) -> float:
        return self.angle

    def is_finished(self) -> bool:
        if not self.length:
            return False
        return self.distance >= self.length


class EvadingTrajectoryProvider(TrajectoryProvider):
    def __init__(
        self,
        start: tuple[int, int],
        angle: float,
        speed: float,
        mark: "AnimatedSprite",
        bounds: pygame.Rect,
    ):
        self.start = start
        self.speed = speed
        self.angle = angle
        self.mark = mark
        self.bounds = bounds
        self.position = Vector2(start)
        self.direction = Vector2(0, 0)
        super().__init__()

    def new_heading(self) -> tuple[Vector2, float]:
        goal = Vector2(self.bounds.center) - Vector2(self.mark.rect.center)
        if goal.length() > 0.0:
            goal.normalize_ip()
            goal = goal * (self.bounds.width / 2) + Vector2(self.bounds.center)
            new_direction = goal - self.position
            new_direction.normalize_ip()
            new_angle = -new_direction.angle_to(Vector2(1, 0))
            return (new_direction, new_angle)
        return (self.direction, self.angle)

    def update(self, dt: float) -> None:
        if self.mark.alive():
            self.direction, self.angle = self.new_heading()
        self.position += self.direction * self.speed * dt

    def get_current_position(self) -> tuple[int, int]:
        return (int(self.position.x), int(self.position.y))

    def get_current_angle(self) -> float:
        return self.angle

    def is_finished(self) -> bool:
        return False


class Direction(Flag):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    CW = auto()
    CCW = auto()


@dataclass
class VirtualKeyboard:
    direction: Direction = Direction(0)
    fire: bool = False


Keybindings = dict[int, Direction]

default_keybindings: Keybindings = {
    pygame.K_UP: Direction.UP,
    pygame.K_DOWN: Direction.DOWN,
    pygame.K_LEFT: Direction.LEFT,
    pygame.K_RIGHT: Direction.RIGHT,
    pygame.K_PAGEUP: Direction.CCW,
    pygame.K_PAGEDOWN: Direction.CW,
}


class KeyboardTrajectoryProvider(TrajectoryProvider):
    def __init__(
        self,
        boundary: pygame.Rect,
        initial_position: tuple[int, int],
        initial_speed: float,
        initial_rotation_speed: float,
        keybindings: Keybindings = default_keybindings,
        virtual_keyboard: VirtualKeyboard = VirtualKeyboard(),
    ) -> None:
        self.boundary = boundary
        self.position = Vector2(initial_position)
        self.angle = 0.0
        self.speed = initial_speed
        self.rotation_speed = initial_rotation_speed
        self.keybindings = keybindings
        self.virtual_keyboard = virtual_keyboard

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        dir_flags = self.virtual_keyboard.direction
        for key, direction in self.keybindings.items():
            if keys[key]:
                dir_flags |= direction
        # Translation
        translation = Vector2(0, 0)
        if dir_flags & Direction.UP:
            translation = translation + Vector2(0, -1)
        if dir_flags & Direction.DOWN:
            translation = translation + Vector2(0, 1)
        if dir_flags & Direction.LEFT:
            translation = translation + Vector2(-1, 0)
        if dir_flags & Direction.RIGHT:
            translation = translation + Vector2(1, 0)
        if translation.length() > 0:
            translation.normalize_ip()
            self.position += translation * self.speed * dt
            if self.position.x < self.boundary.left:
                self.position.x = self.boundary.left
            elif self.position.x > self.boundary.right:
                self.position.x = self.boundary.right
            if self.position.y < self.boundary.top:
                self.position.y = self.boundary.top
            elif self.position.y > self.boundary.bottom:
                self.position.y = self.boundary.bottom
        # Rotation
        if dir_flags & Direction.CW:
            self.angle += self.rotation_speed * dt
        if dir_flags & Direction.CCW:
            self.angle -= self.rotation_speed * dt

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
    def __init__(
        self, animation: Animation, angle_offset: float | None, *groups
    ) -> None:
        super().__init__(*groups)
        self.animation = animation
        self.angle_offset = angle_offset
        self.image = self.animation.get_current_frame().copy()
        self.rect = self.image.get_rect()
        self.rect.top = 0
        self.rect.left = 0
        self.angle = 0.0
        self.animation_end_handler = None
        self.__gen = self.__animation_loop()
        next(self.__gen)

    def _update_image(self) -> None:
        self.image = self.animation.get_current_frame().copy()
        # Rotate the image if necessary
        if self.angle_offset is not None:
            effective_angle = -self.angle + self.angle_offset
            if effective_angle != 0.0:
                self.image = pygame.transform.rotate(self.image, effective_angle)
        # Debug the bounding box
        if SPRITE_DEBUG:
            pygame.draw.rect(self.image, "magenta", self.image.get_rect(), 1)
            hb = self.get_hit_box()
            hb.center = self.image.get_rect().center
            pygame.draw.rect(self.image, "cyan", hb, 1)
        new_rect = self.image.get_rect()
        new_rect.center = self.rect.center
        self.rect = new_rect

    def get_hit_box(self) -> pygame.Rect:
        return self.image.get_rect()

    def set_animation(
        self, animation: Animation, angle_offset: float | None = 0.0, reset_angle=False
    ) -> "AnimatedSprite":
        self.animation = animation
        if angle_offset is not None:
            self.angle_offset = angle_offset
        if reset_angle:
            self.angle = 0.0
        # self._update_image()
        return self

    def on_animation_end(self, handler) -> "AnimatedSprite":
        self.animation_end_handler = handler
        return self

    def __animation_loop(self) -> Generator[None, float, None]:
        while True:
            while not self.animation.is_finished():
                dt = yield
                self.animation.update(dt)
                self._update_image()
            if self.animation_end_handler:
                self.animation_end_handler(self)
            while self.animation.is_finished():
                yield

    def update(self, dt: float) -> None:
        self.__gen.send(dt)


class TrajectorySprite(AnimatedSprite):
    def __init__(
        self,
        animation: Animation,
        angle_offset: Optional[float],
        trajectory_provider: TrajectoryProvider,
        *groups,
    ) -> None:
        super().__init__(animation, angle_offset, *groups)
        self.trajectory_provider = trajectory_provider
        self.rect.center = self.trajectory_provider.get_current_position()
        self.trajectory_end_handler = None
        self.__gen = self.__create_gen()
        next(self.__gen)

    def on_trajectory_end(self, handler) -> Self:
        self.trajectory_end_handler = handler
        return self

    def __create_gen(self) -> Generator[None, float, None]:
        while self.alive():
            dt = yield
            self.trajectory_provider.update(dt)
            self.angle = self.trajectory_provider.get_current_angle()
            self.rect.center = self.trajectory_provider.get_current_position()

    def update(self, dt: float) -> None:
        super().update(dt)
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
