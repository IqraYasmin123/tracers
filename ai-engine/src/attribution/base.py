"""
Abstract base interface for attribution/heatmap-generation methods.

Same Dependency Inversion pattern as every prior module: written against BaseVLM, and
Module 9's backend will call this interface without knowing whether it's getting
gradient-based saliency, attention-based visualization, or a future third method.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import torch

from src.vlm.base import BaseVLM

from .result import AttributionResult


class BaseAttribution(ABC):
    """Abstract interface every TRACER attribution method must implement."""

    @abstractmethod
    def generate(
        self,
        vlm: BaseVLM,
        pixel_values: torch.Tensor,
        text_embeds: torch.Tensor | None = None,
    ) -> AttributionResult:
        """Produce a forensic attribution heatmap for the given image.

        text_embeds is optional because not every method needs it — gradient-based saliency
        requires a caption to compute similarity gradients against, while pure
        attention-visualization methods only need the image.
        """
        raise NotImplementedError
