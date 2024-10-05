# Example file showing a circle moving on screen
import pygame
from shooter import Shooter

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1080, 1080))
pygame.mouse.set_visible(False)
clock = pygame.time.Clock()

sprite_sheet = pygame.image.load("assets/ships.png").convert_alpha()
bullet_sheet = pygame.image.load("assets/bullet.png").convert_alpha()
bullet2_sheet = pygame.image.load("assets/bullet-2.png").convert_alpha()
laser_sheet = pygame.image.load("assets/laser.png").convert_alpha()
laser2_sheet = pygame.image.load("assets/laser-2.png").convert_alpha()
crosshair_sheet = pygame.image.load("assets/crosshair.png").convert_alpha()
crosshair2_sheet = pygame.image.load("assets/crosshair-2.png").convert_alpha()
game = Shooter(
    screen,
    [
        sprite_sheet,
        bullet_sheet,
        bullet2_sheet,
        laser_sheet,
        laser2_sheet,
        crosshair_sheet,
        crosshair2_sheet,
    ],
)
dt = 0
running = True

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # fill the screen with a color to wipe away anything from last frame
    screen.fill((50, 50, 50))

    game.process_frame(dt)

    # flip() the display to put your work on screen
    pygame.display.flip()

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    dt = clock.tick(60) / 1000

pygame.quit()
