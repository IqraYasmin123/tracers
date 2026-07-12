"""Configuration for VLM backbones."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VLMConfig:
    """Configuration for loading a Vision-Language Model backbone.

    Attributes:
        model_name: Hugging Face model identifier.
        device: "cuda" or "cpu". Auto-detected at load time if left as None.
        freeze_weights: If True (default), all backbone parameters are frozen — TRACER never
            fine-tunes the VLM itself, it only uses it as a frozen inference target whose
            behavior under attack we're forensically analyzing.
    """

    model_name: str = "openai/clip-vit-base-patch32"
    device: str | None = None
    freeze_weights: bool = True

    def resolved_device(self) -> str:
        """Return the actual device to use, auto-detecting CUDA if none was specified."""
        if self.device is not None:
            return self.device
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
