from typing import TYPE_CHECKING, Generator

import pygame
from pygame import Vector2
from pygame.sprite import Sprite
from pygame.surface import Surface

from animation import Animation

if TYPE_CHECKING:
    from shooter_game import ShooterGame
import os

SPRITE_DEBUG = os.getenv("SPRITE_DEBUG", "False").lower() in ("true", "1", "t")


class TrajectoryProvider:
    def update(self, dt: float) -> None:
        pass

    def get_current_position(self) -> tuple[int, int]:
        pass

    def get_current_angle(self) -> float:
        pass

    def is_finished(self) -> bool:
        pass


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
        self._distance = 0
        self._position = ctrlpoints[0]
        self._angle = (end - begin).angle_to(Vector2(1, 0))
        self.shift = shift

    def update(self, dt: float) -> None:
        self._distance += round(self._initial_speed * dt)
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
            return (
                Vector2(self._position)
                + Vector2(1, 0).rotate(90 + self._angle) * self.shift
            )
        return self._position

    def get_current_angle(self) -> float:
        return self._angle

    def is_finished(self) -> bool:
        return self._distance >= self._total_length


class StraightTrajectoryProvider(TrajectoryProvider):
    def __init__(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
        angle: float,
        speed: float,
        angular_speed: float = 0.0,
    ) -> None:
        self.start = start
        self.end = end
        self.speed = speed
        self.angle = angle
        self.position = Vector2(start)
        if end is not None:
            self._direction = Vector2(end) - Vector2(start)
            self._distance = Vector2(end).distance_to(Vector2(start))
            self.angle = -self._direction.angle_to(Vector2(1, 0))
        elif angle is not None:
            self._direction = Vector2(1, 0).rotate(angle)
            self._distance = float("Infinity")
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
        self, start: tuple[int, int], angle: float, speed: float, mark: Sprite
    ):
        self.start = start
        self.speed = speed
        self.angle = angle
        self.mark = mark
        self.position = Vector2(start)
        self.direction = Vector2(self.mark.rect.center) - self.position
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
            max_diff = 1.0
            if diff_angle > max_diff:
                new_angle = self.angle + max_diff
            elif diff_angle < -max_diff:
                new_angle = self.angle - max_diff
            self.angle = new_angle
            self.direction = Vector2(1, 0).rotate(new_angle)
        self.position += self.direction * self.speed * dt

    def get_current_position(self) -> tuple[int, int]:
        return (int(self.position.x), int(self.position.y))

    def get_current_angle(self) -> float:
        return self.angle

    def is_finished(self) -> bool:
        return False


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
        self.__gen = self.__create_gen()
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
        new_rect = self.image.get_rect()
        new_rect.center = self.rect.center
        self.rect = new_rect

    def set_animation(
        self, animation: Animation, angle_offset: float | None = 0.0, reset_angle=False
    ) -> "AnimatedSprite":
        self.animation = animation
        if angle_offset is not None:
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
