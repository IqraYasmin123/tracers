"""Attention analysis and heatmap generation (Module 6).

Public API:
    BaseAttribution     — abstract interface every attribution method implements
    GradientSaliency     — input-gradient sensitivity map ("what matters to the prediction")
    AttentionMap         — raw attention visualization ("what the model is looking at")
    AttributionResult    — common output type, with .resized() for overlay on any image size
    AttributionError      — module-specific exception
    normalize_heatmap    — shared min-max normalization utility
    show_attribution      — visualization helper

Example:
    >>> from src.attribution import GradientSaliency, AttentionMap, show_attribution
    >>> saliency_result = GradientSaliency().generate(vlm, pixel_values, text_embeds)
    >>> attention_result = AttentionMap(layer_index=-1).generate(vlm, pixel_values)
    >>> show_attribution(pil_image, saliency_result)
"""
from .attention_map import AttentionMap
from .base import BaseAttribution
from .exceptions import AttributionError
from .gradient_saliency import GradientSaliency
from .result import AttributionResult, normalize_heatmap
from .visualize import show_attribution

__all__ = [
    "BaseAttribution",
    "GradientSaliency",
    "AttentionMap",
    "AttributionResult",
    "AttributionError",
    "normalize_heatmap",
    "show_attribution",
]
