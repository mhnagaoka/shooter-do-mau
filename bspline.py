from geomdl import BSpline
from geomdl import utilities
import pygame, sys

pygame.init()


class Config:
    def __init__(self):
        self.display_size = (1080, 1080)
        self.fill = (20, 20, 30)
        self.width = 1
        self.color = (255, 180, 0)
        self.dark = (50, 50, 60)
        self.bright = (70, 90, 80)
        self.brightred = (120, 70, 70)
        self.restrict = False
        self.restrict_zone = (160, 200, 560, 600)
        self.show_points = True


cfg = Config()


class Spline:
    def __init__(self, degree=2):
        self.degree = degree
        self.curve = BSpline.Curve()
        self.curve.degree = degree

    def draw(self, points):
        self.curve.ctrlpts = points
        self.curve.knotvector = utilities.generate_knot_vector(
            self.curve.degree, len(self.curve.ctrlpts)
        )
        return self.curve.evalpts

    def set_degree(self, d):
        self.curve.degree = d
        self.degree = d


class Canvas:
    def __init__(self, screen):
        self.screen = screen
        self.curve = Spline()
        self.ctrl_points = []
        self.count = 0
        self.selected = None
        self.move_point = False
        self.add_mode = 0

        self.add_button = (20, 370, 50, 20)
        self.del_button = (90, 370, 50, 20)
        self.sel_button = (160, 370, 50, 20)
        self.hide_button = (230, 370, 50, 20)

    def add_points(self, xy):
        self.ctrl_points.append(xy)

    def button_render(self):
        if self.add_mode:
            pygame.draw.rect(self.screen, cfg.bright, self.add_button)
        else:
            pygame.draw.rect(self.screen, cfg.dark, self.add_button)
        if self.selected != None:
            pygame.draw.rect(self.screen, cfg.bright, self.sel_button)
            pygame.draw.rect(self.screen, cfg.brightred, self.del_button)

        pygame.draw.rect(self.screen, cfg.dark, self.hide_button)

    def render(self):
        if cfg.show_points:
            if self.count >= 2:
                pygame.draw.lines(self.screen, (100, 100, 100), 0, self.ctrl_points)
                print(self.ctrl_points)
            for i, point in enumerate(self.ctrl_points):
                if i == 0:
                    pygame.draw.circle(self.screen, (0, 140, 200), point, 5)
                elif i == self.selected:
                    pygame.draw.circle(self.screen, (20, 200, 80), point, 5)
                else:
                    pygame.draw.circle(self.screen, (140, 140, 140), point, 5)
        if self.count >= self.curve.degree + 1:
            pygame.draw.lines(
                self.screen,
                cfg.color,
                0,
                self.curve.draw(self.ctrl_points),
                width=cfg.width,
            )
        self.button_render()

    def region(self, button, x, y):
        bx, by, brx, bry = button
        if bx < x < bx + brx and by < y < by + bry:
            return True
        return False

    def select(self, x, y, r=10):
        can_add = True
        if self.region(self.add_button, x, y):
            self.add_mode = not self.add_mode
            can_add = False
        elif self.region(self.sel_button, x, y):
            self.selected = None
            can_add = False
        elif self.region(self.hide_button, x, y):
            cfg.show_points = not cfg.show_points
            self.selected = None
            can_add = False

        elif self.region(self.del_button, x, y):
            self.ctrl_points.pop(self.selected)
            self.count -= 1
            self.selected = None
            can_add = False
        elif self.count and cfg.show_points:
            for i, points in enumerate(self.ctrl_points):
                px, py = points
                if px - r < x < px + r and py - r < y < py + r:
                    self.selected = i
                    self.move_point = True
                    can_add = False
                    break
        if (self.add_mode and can_add) and cfg.show_points:
            if self.selected != None:
                xpoint, _ = self.ctrl_points[self.selected]
                if xpoint > x:
                    self.ctrl_points.insert(self.selected, (x, y))
                else:
                    self.ctrl_points.insert(self.selected + 1, (x, y))
            else:
                self.ctrl_points.append((x, y))
            self.count += 1

    def move(self, xy):
        if self.move_point and cfg.show_points:
            self.ctrl_points.pop(self.selected)
            self.ctrl_points.insert(self.selected, xy)
            return True


if __name__ == "__main__":
    screen = pygame.display.set_mode(cfg.display_size)
    canvas = Canvas(screen)

    def update():
        screen.fill(cfg.fill)
        canvas.render()
        pygame.display.update()

    update()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                canvas.select(*event.pos)
                update()
            elif event.type == pygame.MOUSEBUTTONUP:
                canvas.move_point = False
            elif event.type == pygame.MOUSEMOTION:
                if canvas.move(event.pos):
                    update()
