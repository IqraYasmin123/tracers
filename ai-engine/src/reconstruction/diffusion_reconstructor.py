"""
Diffusion-guided image reconstruction.

Uses a pretrained Stable Diffusion inpainting pipeline, masked by the attribution heatmap
from Module 6, to "heal" the region flagged as forensically significant.

Designed for dependency injection: `pipeline` can be supplied directly (used by tests with a
lightweight fake, since the real pipeline is several GB and can't reasonably be downloaded in
a unit test) or left as None, in which case the real pipeline is lazily loaded from Hugging
Face on first use — this only happens in Colab, never during `pytest`.
"""
from __future__ import annotations

from typing import Any

import numpy as np
from PIL import Image

from .base import BaseReconstructor
from .config import ReconstructionConfig
from .exceptions import ReconstructionError
from .mask import heatmap_to_mask


class DiffusionReconstructor(BaseReconstructor):
    """Stable Diffusion inpainting, guided by a TRACER attribution heatmap."""

    def __init__(
        self, config: ReconstructionConfig | None = None, pipeline: Any = None
    ) -> None:
        self.config = config or ReconstructionConfig()
        self._pipeline = pipeline  # injected for tests; lazily loaded otherwise

    def _get_pipeline(self) -> Any:
        if self._pipeline is None:
            try:
                import torch
                from diffusers import StableDiffusionInpaintPipeline

                self._pipeline = StableDiffusionInpaintPipeline.from_pretrained(
                    self.config.model_name, torch_dtype=torch.float16
                )
            except Exception as exc:
                raise ReconstructionError(
                    f"Failed to load diffusion pipeline '{self.config.model_name}': {exc}"
                ) from exc
        return self._pipeline

    def reconstruct(
        self, image: Image.Image, heatmap: np.ndarray, prompt: str | None = None
    ) -> Image.Image:
        try:
            binary_mask = heatmap_to_mask(heatmap, self.config.mask_threshold)
            mask_image = Image.fromarray(binary_mask).resize(image.size)

            pipeline = self._get_pipeline()
            resolved_prompt = prompt or self.config.default_prompt

            result = pipeline(
                prompt=resolved_prompt,
                image=image,
                mask_image=mask_image,
                num_inference_steps=self.config.num_inference_steps,
                guidance_scale=self.config.guidance_scale,
            )
            return result.images[0]
        except ReconstructionError:
            raise
        except Exception as exc:
            raise ReconstructionError(f"Reconstruction failed: {exc}") from exc
