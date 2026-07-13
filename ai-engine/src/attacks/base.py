"""
Abstract base interface for adversarial attacks used by TRACER.

Same Dependency Inversion pattern as Modules 2 and 3: written against BaseVLM, not any
specific VLM implementation — and Module 5's detector training will be written against this
BaseAttack interface, not against FGSMAttack/PGDAttack directly. A new attack type (DeepFool,
or a black-box query attack) added later needs no changes anywhere else.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import torch

from src.vlm.base import BaseVLM


class BaseAttack(ABC):
    """Abstract interface every TRACER-supported adversarial attack must implement."""

    @abstractmethod
    def generate(
        self, vlm: BaseVLM, pixel_values: torch.Tensor, text_embeds: torch.Tensor
    ) -> torch.Tensor:
        """Return an adversarially perturbed version of pixel_values.

        Args:
            vlm: any BaseVLM implementation — the attack must work against real CLIP or any
                future backbone without modification (Liskov Substitution Principle).
            pixel_values: the clean, preprocessed image tensor to attack.
            text_embeds: the (already-encoded) true caption embedding(s) — the attack
                degrades similarity between the image and this caption.
        """
        raise NotImplementedError
