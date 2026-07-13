"""Shared utilities for adversarial attacks."""
from __future__ import annotations

import torch

from src.vlm.base import BaseVLM


def similarity_loss(
    vlm: BaseVLM, pixel_values: torch.Tensor, text_embeds: torch.Tensor
) -> torch.Tensor:
    """Untargeted attack loss: negative mean cosine similarity between the image and its
    true caption embedding(s).

    Ascending this loss via gradient (i.e. what FGSM/PGD do) pushes the image AWAY from
    matching its caption — this is TRACER's realistic threat model: an attacker degrading
    correct image-text understanding generally, not targeting a specific wrong label.

    Always calls encode_image with requires_grad=True since this helper only exists to be
    used inside attacks, which need gradients flowing back to pixel_values.
    """
    image_embeds = vlm.encode_image(pixel_values, requires_grad=True)
    similarity = vlm.similarity(image_embeds, text_embeds)
    return -similarity.mean()
