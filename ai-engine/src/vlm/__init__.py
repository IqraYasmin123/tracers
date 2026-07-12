"""Vision-Language Model integration (Module 2).

Public API:
    BaseVLM      — abstract interface every VLM backbone implements
    CLIPVLM      — CLIP implementation of BaseVLM
    VLMConfig    — configuration dataclass
    VLMLoadError, VLMInferenceError — module-specific exceptions

Example:
    >>> from src.vlm import CLIPVLM, VLMConfig
    >>> vlm = CLIPVLM(VLMConfig())
    >>> pixel_values = vlm.preprocess_image(some_pil_image)
    >>> image_embeds = vlm.encode_image(pixel_values)
    >>> text_embeds = vlm.encode_text(["a photo of a cat", "a photo of a dog"])
    >>> vlm.similarity(image_embeds, text_embeds)
"""
from .base import BaseVLM
from .clip_vlm import CLIPVLM
from .config import VLMConfig
from .exceptions import VLMInferenceError, VLMLoadError

__all__ = ["BaseVLM", "CLIPVLM", "VLMConfig", "VLMLoadError", "VLMInferenceError"]
