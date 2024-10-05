import pygame
from pygame import Surface

def _crop_sprites(sprite_sheet: Surface):
    # https://ezgif.com/crop/ezgif-1-7dc8bcb030.png
    cropped_sprites = [
        sprite_sheet.subsurface((48, 38, 35, 37)),  # player banking left 2
        sprite_sheet.subsurface((88, 38, 35, 37)),  # player banking left 1
        sprite_sheet.subsurface((134, 38, 35, 37)),  # player neutral
        sprite_sheet.subsurface((182, 38, 35, 37)),  # player banking right 1
        sprite_sheet.subsurface((222, 38, 35, 37)),  # player banking right 2
        sprite_sheet.subsurface((40, 147, 45, 37)),  # green enemy
    ]
    scaled_sprites = [pygame.transform.scale2x(s) for s in cropped_sprites]
    return (cropped_sprites, scaled_sprites)

class Shooter:
    def __init__(self, screen: Surface, sprite_sheet: Surface):
        self.screen = screen
        self.sprite_sheet = sprite_sheet
        self.running = True
        self.dt = 0
        self.cropped_sprites, self.scaled_sprites = _crop_sprites(sprite_sheet)
        self.player_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)
        self.player_ship = self.scaled_sprites[2]

    def process_frame(self, dt: float):
            # fill the screen with a color to wipe away anything from last frame
        self.screen.fill((50, 50, 50))

        mouse_pos = pygame.mouse.get_pos()
        pygame.draw.line(
            self.screen,
            "white",
            (
                self.player_pos.x + self.player_ship.get_width() / 2,
                self.player_pos.y + self.player_ship.get_height() / 2,
            ),
            mouse_pos,
        )
        print(mouse_pos)

        pygame.draw.rect(self.screen, "red", self.player_ship.get_rect(topleft=self.player_pos), 2)
        self.screen.blit(self.player_ship, self.player_pos)

        self.player_ship = self.scaled_sprites[2]
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.player_pos.y -= 450 * dt
            if self.player_pos.y < 0:
                self.player_pos.y = 0
        if keys[pygame.K_s]:
            self.player_pos.y += 450 * dt
            if self.player_pos.y > self.screen.get_height() - self.player_ship.get_height():
                self.player_pos.y = self.screen.get_height() - self.player_ship.get_height()
        if keys[pygame.K_a]:
            self.player_pos.x -= 450 * dt
            self.player_ship = self.scaled_sprites[0]
            if self.player_pos.x < 0:
                self.player_pos.x = 0
                self.player_ship = self.scaled_sprites[2]
        if keys[pygame.K_d]:
            self.player_pos.x += 450 * dt
            self.player_ship = self.scaled_sprites[3]
            if self.player_pos.x > self.screen.get_width() - self.player_ship.get_width():
                self.player_pos.x = self.screen.get_width() - self.player_ship.get_width()
                self.player_ship = self.scaled_sprites[2]
