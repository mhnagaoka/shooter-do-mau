from typing import Optional

from animation import Animation
from engine import TrajectoryProvider, TrajectorySprite


class Shot(TrajectorySprite):
    def __init__(
        self,
        animation: Animation,
        angle_offset: Optional[float],
        trajectory_provider: TrajectoryProvider,
        damage: float,
        *groups,
    ) -> None:
        super().__init__(animation, angle_offset, trajectory_provider, *groups)
        self.damage = damage
