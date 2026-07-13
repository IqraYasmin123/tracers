"""
FGSM (Fast Gradient Sign Method) — single-step untargeted adversarial attack.

Reference: Goodfellow et al., "Explaining and Harnessing Adversarial Examples" (2015).
"""
from __future__ import annotations

import torch

from src.vlm.base import BaseVLM

from .base import BaseAttack
from .config import AttackConfig
from .exceptions import AttackGenerationError
from .utils import similarity_loss


class FGSMAttack(BaseAttack):
    """Nudges every pixel by `epsilon` in the direction that most reduces image-caption
    similarity, computed in a single gradient step. Fast, but a relatively weak/detectable
    attack compared to PGD — useful as a baseline."""

    def __init__(self, config: AttackConfig | None = None) -> None:
        self.config = config or AttackConfig()

    def generate(
        self, vlm: BaseVLM, pixel_values: torch.Tensor, text_embeds: torch.Tensor
    ) -> torch.Tensor:
        try:
            pv = pixel_values.clone().detach().requires_grad_(True)
            loss = similarity_loss(vlm, pv, text_embeds)
            loss.backward()

            if pv.grad is None:
                raise AttackGenerationError(
                    "No gradient was computed for the input image. Check that the VLM's "
                    "encode_image() correctly supports requires_grad=True."
                )

            perturbed = pv + self.config.epsilon * pv.grad.sign()
            return perturbed.detach()
        except AttackGenerationError:
            raise
        except Exception as exc:
            raise AttackGenerationError(f"FGSM attack failed: {exc}") from exc
