"""
Abstract base interface for image reconstruction methods.

Same Dependency Inversion pattern as every prior module. Also note: unlike BaseVLM/BaseAttack,
this interface doesn't take a BaseVLM at all — reconstruction operates purely on the image and
its attribution heatmap, with no need to re-query the target model.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
from PIL import Image


class BaseReconstructor(ABC):
    """Abstract interface every TRACER reconstruction method must implement."""

    @abstractmethod
    def reconstruct(
        self, image: Image.Image, heatmap: np.ndarray, prompt: str | None = None
    ) -> Image.Image:
        """Return a reconstructed version of `image`, guided by `heatmap` (a [0,1]-normalized
        attribution map indicating which regions to treat as damaged/suspicious)."""
        raise NotImplementedError
