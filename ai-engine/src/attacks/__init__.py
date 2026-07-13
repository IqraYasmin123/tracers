"""Adversarial attack generation (Module 4).

Public API:
    BaseAttack           — abstract interface every attack implements
    FGSMAttack           — single-step attack
    PGDAttack            — iterative attack (stronger, harder to detect)
    AttackConfig         — configuration dataclass (epsilon, alpha, steps)
    AttackGenerationError — module-specific exception
    similarity_loss      — shared untargeted attack loss

Example:
    >>> from src.vlm import CLIPVLM, VLMConfig
    >>> from src.attacks import PGDAttack, AttackConfig
    >>> vlm = CLIPVLM(VLMConfig())
    >>> pixel_values = vlm.preprocess_image(some_pil_image)
    >>> text_embeds = vlm.encode_text(["a photo of a dog"])
    >>> attack = PGDAttack(AttackConfig(epsilon=8/255, alpha=2/255, steps=10))
    >>> adversarial_pixel_values = attack.generate(vlm, pixel_values, text_embeds)
"""
from .base import BaseAttack
from .config import AttackConfig
from .exceptions import AttackGenerationError
from .fgsm import FGSMAttack
from .pgd import PGDAttack
from .utils import similarity_loss

__all__ = [
    "BaseAttack",
    "FGSMAttack",
    "PGDAttack",
    "AttackConfig",
    "AttackGenerationError",
    "similarity_loss",
]
