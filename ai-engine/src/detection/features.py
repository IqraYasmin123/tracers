"""
Attention-entropy feature extraction — TRACER's core passive-detection methodology.

The intuition: adversarial perturbations distort how attention mass is distributed across
image tokens inside the vision transformer. Shannon entropy of each attention head's
distribution, averaged per layer, captures this as a compact per-image "fingerprint" —
a vector of shape [num_layers] that a lightweight classifier can then learn to distinguish
between clean and adversarial inputs.

`compute_entropy_from_attentions` takes raw attention tensors directly and has zero
dependency on any VLM — this is deliberate, so the actual math can be unit tested with
hand-crafted tensors with no CLIP download required. `extract_attention_entropy` is the thin
wrapper that connects it to a real BaseVLM.
"""
from __future__ import annotations

import torch

from src.vlm.base import BaseVLM

from .exceptions import DetectionError


def compute_entropy_from_attentions(attentions: tuple[torch.Tensor, ...]) -> torch.Tensor:
    """Compute mean attention entropy per layer.

    Args:
        attentions: tuple of length num_layers, each tensor shaped
            [batch, heads, query_tokens, key_tokens] — exactly what
            BaseVLM.get_vision_attentions() returns.

    Returns:
        Tensor of shape [batch, num_layers] — mean Shannon entropy of the attention
        distribution, averaged over heads and query tokens, for each layer.
    """
    if len(attentions) == 0:
        raise DetectionError(
            "Received an empty attentions tuple — cannot compute entropy. This usually means "
            "the VLM's attention backend doesn't support output_attentions=True (see Module 2's "
            "eager-attention fix)."
        )

    layer_entropies = []
    for layer_attention in attentions:
        probabilities = layer_attention.clamp(min=1e-9)
        entropy = -(probabilities * probabilities.log()).sum(dim=-1)  # [batch, heads, tokens]
        layer_entropies.append(entropy.mean(dim=(1, 2)))  # [batch]

    return torch.stack(layer_entropies, dim=1)  # [batch, num_layers]


def extract_attention_entropy(vlm: BaseVLM, pixel_values: torch.Tensor) -> torch.Tensor:
    """Extract the attention-entropy feature vector for a real image via a real VLM."""
    attentions = vlm.get_vision_attentions(pixel_values)
    return compute_entropy_from_attentions(attentions)
