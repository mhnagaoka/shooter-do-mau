import random
from animation import Animation
from engine import StraightTrajectoryProvider, TrajectorySprite
from surface_factory import SurfaceFactory, trim


class Item(TrajectorySprite):
    def __init__(
        self, animation: Animation, angle_offset: float, trajectory_provider, *groups
    ):
        super().__init__(animation, angle_offset, trajectory_provider, *groups)


class PowerCapsule(Item):
    def __init__(
        self,
        factory: SurfaceFactory,
        initial_pos: tuple[int, int],
        angle: float,
        *groups,
    ):
        animation = Animation.static(trim(factory.surfaces["items"][0]))
        rotation_speed = random.choice([360, -360])
        trajectory_provider = StraightTrajectoryProvider(
            initial_pos, None, angle, 40.0, rotation_speed
        )
        super().__init__(animation, 0.0, trajectory_provider, *groups)
        self.power = 50.0
