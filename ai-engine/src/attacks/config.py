"""Configuration for adversarial attacks."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AttackConfig:
    """Configuration shared by FGSM and PGD.

    Attributes:
        epsilon: Maximum per-pixel perturbation budget (L-infinity norm). Both FGSM and PGD
            never change any pixel by more than this amount from the original — this is what
            keeps the attack "imperceptible" rather than just replacing the image.
        alpha: Step size per PGD iteration. Unused by FGSM (which takes one full-epsilon
            step). Should be smaller than epsilon so multiple steps can refine the attack.
        steps: Number of PGD iterations. Unused by FGSM.
    """

    epsilon: float = 8 / 255
    alpha: float = 2 / 255
    steps: int = 10

    def __post_init__(self) -> None:
        if self.epsilon <= 0:
            raise ValueError(f"epsilon must be positive, got {self.epsilon}")
        if self.alpha <= 0:
            raise ValueError(f"alpha must be positive, got {self.alpha}")
        if self.steps < 1:
            raise ValueError(f"steps must be >= 1, got {self.steps}")
