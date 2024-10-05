# Example file showing a circle moving on screen
import pygame

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1080, 1080))
clock = pygame.time.Clock()
running = True
dt = 0

# https://ezgif.com/crop/ezgif-1-7dc8bcb030.png
raw_ships = pygame.image.load("assets/ships.png").convert_alpha()
cropped_ships = [
    raw_ships.subsurface((48, 38, 35, 37)),  # player banking left 2
    raw_ships.subsurface((88, 38, 35, 37)),  # player banking left 1
    raw_ships.subsurface((134, 38, 35, 37)),  # player neutral
    raw_ships.subsurface((182, 38, 35, 37)),  # player banking right 1
    raw_ships.subsurface((222, 38, 35, 37)),  # player banking right 2
    raw_ships.subsurface((40, 147, 45, 37)),  # green enemy
]
scaled_ships = [pygame.transform.scale2x(s) for s in cropped_ships]

player_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)
player_ship = scaled_ships[2]

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # fill the screen with a color to wipe away anything from last frame
    screen.fill((50, 50, 50))

    mouse_pos = pygame.mouse.get_pos()
    pygame.draw.line(
        screen,
        "white",
        (
            player_pos.x + player_ship.get_width() / 2,
            player_pos.y + player_ship.get_height() / 2,
        ),
        mouse_pos,
    )
    print(mouse_pos)

    pygame.draw.rect(screen, "red", player_ship.get_rect(topleft=player_pos), 2)
    screen.blit(player_ship, player_pos)

    player_ship = scaled_ships[2]
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        player_pos.y -= 450 * dt
        if player_pos.y < 0:
            player_pos.y = 0
    if keys[pygame.K_s]:
        player_pos.y += 450 * dt
        if player_pos.y > screen.get_height() - player_ship.get_height():
            player_pos.y = screen.get_height() - player_ship.get_height()
    if keys[pygame.K_a]:
        player_pos.x -= 450 * dt
        player_ship = scaled_ships[0]
        if player_pos.x < 0:
            player_pos.x = 0
            player_ship = scaled_ships[2]
    if keys[pygame.K_d]:
        player_pos.x += 450 * dt
        player_ship = scaled_ships[3]
        if player_pos.x > screen.get_width() - player_ship.get_width():
            player_pos.x = screen.get_width() - player_ship.get_width()
            player_ship = scaled_ships[2]

    # flip() the display to put your work on screen
    pygame.display.flip()

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    dt = clock.tick(60) / 1000

pygame.quit()
