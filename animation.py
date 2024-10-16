from pygame import Surface


class Animation:
    def __init__(self, frames: list[Surface], delay: float, loop: bool = False) -> None:
        self.frames = frames
        self.delay = delay
        self.current_frame = 0
        self.current_delay = 0
        self.loop = loop

    def update(self, dt: float) -> None:
        self.current_delay += dt
        if self.current_delay >= self.delay:
            self.current_delay = 0
            if self.loop:
                self.current_frame = (self.current_frame + 1) % len(self.frames)
            else:
                self.current_frame = min(self.current_frame + 1, len(self.frames) - 1)

    def get_current_frame(self) -> Surface:
        return self.frames[self.current_frame]

    def is_done(self) -> bool:
        return not self.loop and self.current_frame >= len(self.frames) - 1

    def reset(self) -> None:
        self.current_frame = 0
        self.current_delay = 0
