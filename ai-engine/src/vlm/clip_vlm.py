"""
CLIP implementation of the BaseVLM interface.

CLIP is a dual-encoder Vision-Language Model: a vision transformer and a text transformer
whose outputs are only compared via cosine similarity, never fused into one shared attention
stack. That separation is what keeps the vision encoder's attention weights inspectable in
isolation from the text branch — a requirement for TRACER's later detection (Module 5) and
attribution (Module 6) modules. A fused/unified multimodal model would blur that boundary.
See docs/architecture.md for the full comparison against fused alternatives (BLIP-2, LLaVA).
"""
from __future__ import annotations

import logging
from typing import Any

import torch
from transformers import CLIPModel, CLIPProcessor

from .base import BaseVLM
from .config import VLMConfig
from .exceptions import VLMInferenceError, VLMLoadError

logger = logging.getLogger(__name__)


class CLIPVLM(BaseVLM):
    """Frozen, pretrained CLIP backbone wrapped behind the BaseVLM interface."""

    def __init__(self, config: VLMConfig | None = None) -> None:
        self.config = config or VLMConfig()
        self.device = self.config.resolved_device()
        self._model: CLIPModel | None = None
        self._processor: CLIPProcessor | None = None
        self._load()

    def _load(self) -> None:
        try:
            logger.info(
                "Loading CLIP model '%s' on device '%s'", self.config.model_name, self.device
            )
            self._model = CLIPModel.from_pretrained(self.config.model_name).to(self.device)
            self._processor = CLIPProcessor.from_pretrained(self.config.model_name)
            self._model.eval()
            if self.config.freeze_weights:
                for param in self._model.parameters():
                    param.requires_grad_(False)
            logger.info("CLIP model loaded successfully.")
        except Exception as exc:
            raise VLMLoadError(
                f"Failed to load CLIP model '{self.config.model_name}': {exc}"
            ) from exc

    @property
    def model(self) -> CLIPModel:
        """The underlying transformers CLIPModel. Exposed for modules that need direct access
        (e.g. Module 5's attention entropy extraction)."""
        assert self._model is not None, "Model accessed before successful load."
        return self._model

    @property
    def processor(self) -> CLIPProcessor:
        assert self._processor is not None, "Processor accessed before successful load."
        return self._processor

    def preprocess_image(self, image: Any) -> torch.Tensor:
        try:
            inputs = self.processor(images=image, return_tensors="pt")
            return inputs["pixel_values"].to(self.device)
        except Exception as exc:
            raise VLMInferenceError(f"Image preprocessing failed: {exc}") from exc

    @staticmethod
    def _extract_embeds(output: Any, tensor_attr_names: tuple[str, ...]) -> torch.Tensor:
        """Handle the fact that different transformers versions return either a plain Tensor
        or a ModelOutput object from get_image_features/get_text_features."""
        if isinstance(output, torch.Tensor):
            return output
        for attr in tensor_attr_names:
            value = getattr(output, attr, None)
            if value is not None:
                return value
        raise VLMInferenceError(
            f"Unrecognized feature output type from CLIP: {type(output)}. "
            f"Expected a Tensor or an object with one of {tensor_attr_names}."
        )

    def encode_image(self, pixel_values: torch.Tensor) -> torch.Tensor:
        try:
            with torch.no_grad():
                raw = self.model.get_image_features(pixel_values=pixel_values)
            embeds = self._extract_embeds(raw, ("pooler_output", "image_embeds"))
            return embeds / embeds.norm(dim=-1, keepdim=True)
        except VLMInferenceError:
            raise
        except Exception as exc:
            raise VLMInferenceError(f"Image encoding failed: {exc}") from exc

    def encode_text(self, texts: list[str]) -> torch.Tensor:
        try:
            inputs = self.processor(text=texts, return_tensors="pt", padding=True).to(
                self.device
            )
            with torch.no_grad():
                raw = self.model.get_text_features(**inputs)
            embeds = self._extract_embeds(raw, ("pooler_output", "text_embeds"))
            return embeds / embeds.norm(dim=-1, keepdim=True)
        except VLMInferenceError:
            raise
        except Exception as exc:
            raise VLMInferenceError(f"Text encoding failed: {exc}") from exc

    def similarity(self, image_embeds: torch.Tensor, text_embeds: torch.Tensor) -> torch.Tensor:
        """Cosine similarity — both inputs are already L2-normalized by encode_image/encode_text,
        so a plain dot product is sufficient."""
        return image_embeds @ text_embeds.T

    def get_vision_attentions(self, pixel_values: torch.Tensor) -> tuple[torch.Tensor, ...]:
        try:
            with torch.no_grad():
                outputs = self.model.vision_model(
                    pixel_values=pixel_values, output_attentions=True
                )
            return outputs.attentions
        except Exception as exc:
            raise VLMInferenceError(f"Attention extraction failed: {exc}") from exc
