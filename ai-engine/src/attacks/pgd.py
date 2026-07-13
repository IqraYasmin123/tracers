"""
PGD (Projected Gradient Descent) — iterative untargeted adversarial attack.

Reference: Madry et al., "Towards Deep Learning Models Resistant to Adversarial Attacks"
(2018). Effectively FGSM repeated `steps` times with a smaller step size `alpha`, with each
step re-projected back into the epsilon-ball around the original image — this is what keeps
the total perturbation bounded despite taking many steps.
"""
from __future__ import annotations

import torch

from src.vlm.base import BaseVLM

from .base import BaseAttack
from .config import AttackConfig
from .exceptions import AttackGenerationError
from .utils import similarity_loss


class PGDAttack(BaseAttack):
    """Stronger, harder-to-detect attack than FGSM — this is the one your detector's
    accuracy claims should really be measured against."""

    def __init__(self, config: AttackConfig | None = None) -> None:
        self.config = config or AttackConfig()

    def generate(
        self, vlm: BaseVLM, pixel_values: torch.Tensor, text_embeds: torch.Tensor
    ) -> torch.Tensor:
        try:
            original = pixel_values.clone().detach()
            adv = pixel_values.clone().detach()

            for _ in range(self.config.steps):
                adv.requires_grad_(True)
                loss = similarity_loss(vlm, adv, text_embeds)
                grad = torch.autograd.grad(loss, adv)[0]

                adv = adv.detach() + self.config.alpha * grad.sign()
                # Project back into the epsilon-ball around the original image — this is
                # what distinguishes PGD from just running FGSM repeatedly without bound.
                adv = torch.max(
                    torch.min(adv, original + self.config.epsilon),
                    original - self.config.epsilon,
                )

            return adv.detach()
        except Exception as exc:
            raise AttackGenerationError(f"PGD attack failed: {exc}") from exc
