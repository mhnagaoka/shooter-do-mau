from pygame import Surface


class Animation:
    @staticmethod
    def static(surface: Surface) -> "Animation":
        return Animation([surface], float("Infinity"), loop=True)

    def __init__(self, frames: list[Surface], delay: float, loop: bool = False) -> None:
        self.frames = frames
        self.delay = delay
        self.current_frame = 0
        self.current_delay = 0
        self.loop = loop
        self._finished = False

    def update(self, dt: float) -> None:
        self.current_delay += dt
        if self.current_delay >= self.delay:
            self.current_delay = 0
            if self.loop:
                if self.current_frame >= len(self.frames) - 1:
                    self.current_frame = 0
                else:
                    self.current_frame += 1
            else:
                if self.current_frame < len(self.frames) - 1:
                    self.current_frame += 1
                else:
                    self._finished = True

    def get_current_frame(self) -> Surface:
        return self.frames[min(self.current_frame, len(self.frames) - 1)]

    def is_finished(self) -> bool:
        return self._finished

    def reset(self) -> None:
        self.current_frame = 0
        self.current_delay = 0
