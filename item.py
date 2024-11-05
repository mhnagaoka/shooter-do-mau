from animation import Animation
from engine import StraightTrajectoryProvider, TrajectorySprite
from surface_factory import SurfaceFactory


class Item(TrajectorySprite):
    def __init__(
        self, animation: Animation, power: float, trajectory_provider, *groups
    ):
        super().__init__(animation, power, trajectory_provider, *groups)


class PowerCapsule(Item):
    def __init__(
        self,
        factory: SurfaceFactory,
        initial_pos: tuple[int, int],
        angle: float,
        *groups,
    ):
        animation = Animation.static(factory.surfaces["bullet-2"][0])
        trajectory_provider = StraightTrajectoryProvider(initial_pos, None, angle, 40.0)
        super().__init__(animation, None, trajectory_provider, *groups)
        self.power = 10.0
