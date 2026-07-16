"""Configuration for image reconstruction."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReconstructionConfig:
    """Configuration for DiffusionReconstructor.

    Attributes:
        model_name: Hugging Face diffusion inpainting model identifier.
        mask_threshold: Heatmap values above this (in [0,1]) are marked for inpainting —
            i.e. treated as the region the attack most likely damaged.
        default_prompt: Text guidance for the diffusion model when no prompt is given —
            deliberately generic ("a clean natural photo") since TRACER doesn't assume it
            knows the specific content of the masked region, only that it should look
            unmanipulated.
        num_inference_steps, guidance_scale: Standard diffusion sampling parameters.
    """

    model_name: str = "runwayml/stable-diffusion-inpainting"
    mask_threshold: float = 0.5
    default_prompt: str = "a clean natural photo, high quality"
    num_inference_steps: int = 30
    guidance_scale: float = 7.5

    def __post_init__(self) -> None:
        if not (0.0 <= self.mask_threshold <= 1.0):
            raise ValueError(f"mask_threshold must be in [0,1], got {self.mask_threshold}")
        if self.num_inference_steps < 1:
            raise ValueError(f"num_inference_steps must be >= 1, got {self.num_inference_steps}")
