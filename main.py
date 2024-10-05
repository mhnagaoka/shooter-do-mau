# Example file showing a circle moving on screen
import pygame
from shooter import Shooter

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1080, 1080))
clock = pygame.time.Clock()

sprite_sheet = pygame.image.load("assets/ships.png").convert_alpha()
shooter = Shooter(screen, sprite_sheet)
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

    shooter.process_frame(dt)

    # flip() the display to put your work on screen
    pygame.display.flip()

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    dt = clock.tick(60) / 1000

pygame.quit()
