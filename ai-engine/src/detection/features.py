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


def compute_rich_features_from_attentions(attentions: tuple[torch.Tensor, ...]) -> torch.Tensor:
    """Extended feature set built on top of the same per-layer entropy values, adding two
    kinds of signal the plain mean-entropy vector discards:

    1. Per-layer entropy STD (across heads and query tokens) — captures how *uniformly*
       vs *unevenly* attention is distorted within a layer, not just the average distortion.
    2. Layer-to-layer entropy DELTAS (entropy[i+1] - entropy[i]) — captures how the
       distortion pattern changes with network depth, which a flat mean-per-layer vector
       cannot represent at all.

    This is an experiment aimed at closing a measured accuracy gap (particularly on PGD at
    small epsilon, where the plain mean-entropy detector performed near chance) — not a
    guaranteed improvement. It should be evaluated the same way: real data, real numbers.

    Returns:
        Tensor of shape [batch, 3*num_layers - 1]: [mean_entropy (num_layers),
        std_entropy (num_layers), entropy_deltas (num_layers - 1)], concatenated in that order.
    """
    if len(attentions) == 0:
        raise DetectionError(
            "Received an empty attentions tuple — cannot compute entropy. This usually means "
            "the VLM's attention backend doesn't support output_attentions=True (see Module 2's "
            "eager-attention fix)."
        )

    layer_means, layer_stds = [], []
    for layer_attention in attentions:
        probabilities = layer_attention.clamp(min=1e-9)
        entropy = -(probabilities * probabilities.log()).sum(dim=-1)  # [batch, heads, tokens]
        flat = entropy.reshape(entropy.shape[0], -1)  # [batch, heads*tokens]
        layer_means.append(flat.mean(dim=1))  # [batch]
        layer_stds.append(flat.std(dim=1))  # [batch]

    mean_entropy = torch.stack(layer_means, dim=1)  # [batch, num_layers]
    std_entropy = torch.stack(layer_stds, dim=1)  # [batch, num_layers]
    deltas = mean_entropy[:, 1:] - mean_entropy[:, :-1]  # [batch, num_layers - 1]

    return torch.cat([mean_entropy, std_entropy, deltas], dim=1)


def extract_attention_entropy(vlm: BaseVLM, pixel_values: torch.Tensor) -> torch.Tensor:
    """Extract the (plain, mean-only) attention-entropy feature vector for a real image
    via a real VLM."""
    attentions = vlm.get_vision_attentions(pixel_values)
    return compute_entropy_from_attentions(attentions)


def extract_rich_features(vlm: BaseVLM, pixel_values: torch.Tensor) -> torch.Tensor:
    """Extract the extended (mean + std + cross-layer delta) feature vector for a real
    image via a real VLM. See compute_rich_features_from_attentions for details."""
    attentions = vlm.get_vision_attentions(pixel_values)
    return compute_rich_features_from_attentions(attentions)
