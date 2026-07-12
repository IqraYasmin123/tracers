"""
Abstract base interface for Vision-Language Models used by TRACER.

Every downstream module (detection, attribution, reconstruction) depends on this interface,
never on a specific implementation (Dependency Inversion Principle). Swapping CLIP for another
VLM later means writing one new class here — nothing downstream has to change.

See docs/architecture.md and docs/module2_vlm.md for the full design rationale.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import torch


class BaseVLM(ABC):
    """Abstract interface every TRACER-supported VLM backbone must implement."""

    @abstractmethod
    def preprocess_image(self, image: Any) -> torch.Tensor:
        """Convert a PIL image (or batch of images) into a model-ready pixel_values tensor."""
        raise NotImplementedError

    @abstractmethod
    def encode_image(self, pixel_values: torch.Tensor) -> torch.Tensor:
        """Return an L2-normalized image embedding tensor of shape [batch, embed_dim]."""
        raise NotImplementedError

    @abstractmethod
    def encode_text(self, texts: list[str]) -> torch.Tensor:
        """Return an L2-normalized text embedding tensor of shape [batch, embed_dim]."""
        raise NotImplementedError

    @abstractmethod
    def similarity(self, image_embeds: torch.Tensor, text_embeds: torch.Tensor) -> torch.Tensor:
        """Return cosine similarity scores between image and text embeddings."""
        raise NotImplementedError

    @abstractmethod
    def get_vision_attentions(self, pixel_values: torch.Tensor) -> tuple[torch.Tensor, ...]:
        """Return per-layer attention tensors from the vision encoder.

        Needed by Module 5 (detection) and Module 6 (attribution) — defined here now so the
        interface is complete from day one, even though nothing calls it yet.
        """
        raise NotImplementedError
