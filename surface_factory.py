import os
from typing import Generator

import pygame

from animation import Animation


def slice_image(
    image: pygame.Surface,
    target_width: int,
    target_height: int,
    skip_blanks: bool = True,
) -> Generator[pygame.Surface, None, None]:
    height = min(target_height, image.get_height())
    width = min(target_width, image.get_width())
    for y in range(0, image.get_height(), height):
        for x in range(0, image.get_width(), width):
            slice = image.subsurface(pygame.Rect(x, y, width, height))
            if skip_blanks:
                found = False
                # skip blank slices
                for pixel_x in range(slice.get_width()):
                    for pixel_y in range(slice.get_height()):
                        if slice.get_at((pixel_x, pixel_y))[3] != 0:
                            found = True
                if found:
                    yield slice
            else:
                yield slice


def trim(image: pygame.Surface) -> pygame.Surface:
    left = 0
    right = image.get_width()
    top = 0
    bottom = image.get_height()
    for x in range(image.get_width()):
        for y in range(image.get_height()):
            if image.get_at((x, y))[3] != 0:
                left = x
                break
        if left != 0:
            break
    for x in range(image.get_width() - 1, -1, -1):
        for y in range(image.get_height()):
            if image.get_at((x, y))[3] != 0:
                right = x
                break
        if right != image.get_width():
            break
    for y in range(image.get_height()):
        for x in range(image.get_width()):
            if image.get_at((x, y))[3] != 0:
                top = y
                break
        if top != 0:
            break
    for y in range(image.get_height() - 1, -1, -1):
        for x in range(image.get_width()):
            if image.get_at((x, y))[3] != 0:
                bottom = y
                break
        if bottom != image.get_height():
            break
    return image.subsurface(pygame.Rect(left, top, right - left, bottom - top))


def crop(
    image: pygame.Surface, x: int, y: int, width: int, height: int
) -> pygame.Surface:
    return image.subsurface(pygame.Rect(x, y, width, height))


class SurfaceFactory:
    def __init__(self, folders: list[str]) -> None:
        self.raw_surfaces: dict[str, pygame.Surface] = dict()
        self.surfaces: dict[str, list[pygame.Surface]] = dict()
        for folder in folders:
            files = [
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if os.path.isfile(os.path.join(folder, f))
            ]
            png_files = [f for f in files if f.endswith(".png")]
            for name in png_files:
                key = os.path.basename(name)[0:-4]
                image = pygame.image.load(name).convert_alpha()
                self.raw_surfaces[key] = image
                self.surfaces[key] = list(slice_image(image, 16, 16))
