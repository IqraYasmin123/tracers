"""
Attention-based attribution: visualizes which image patches the vision transformer's CLS
token attends to most, directly from real attention weights — no gradients needed.

This is a complementary signal to GradientSaliency: gradient saliency shows "what changing
this pixel would do to the similarity score," while this shows "what the model is actually
looking at right now." Reported together, they give a more complete forensic picture than
either alone.
"""
from __future__ import annotations

import torch

from src.vlm.base import BaseVLM

from .base import BaseAttribution
from .exceptions import AttributionError
from .result import AttributionResult, normalize_heatmap


class AttentionMap(BaseAttribution):
    """Visualizes the CLS token's attention to image patches at a given layer, reshaped
    into a spatial grid."""

    def __init__(self, layer_index: int = -1) -> None:
        """layer_index: which vision-transformer layer to visualize. -1 (default) uses the
        last layer, generally the most semantically meaningful for CLIP."""
        self.layer_index = layer_index

    def generate(
        self,
        vlm: BaseVLM,
        pixel_values: torch.Tensor,
        text_embeds: torch.Tensor | None = None,  # unused — pure vision-side attribution
    ) -> AttributionResult:
        try:
            attentions = vlm.get_vision_attentions(pixel_values)
            if not attentions:
                raise AttributionError("VLM returned no attention layers.")

            layer_attention = attentions[self.layer_index]  # [batch, heads, tokens, tokens]
            mean_over_heads = layer_attention.mean(dim=1)  # [batch, tokens, tokens]
            cls_to_patches = mean_over_heads[0, 0, 1:]  # CLS token's attention to patches

            num_patches = cls_to_patches.shape[0]
            grid_side = round(num_patches**0.5)
            if grid_side * grid_side != num_patches:
                raise AttributionError(
                    f"Cannot reshape {num_patches} patch tokens into a square grid — this "
                    "VLM's patch layout isn't supported by this attribution method."
                )

            grid = cls_to_patches.reshape(grid_side, grid_side)
            heatmap = normalize_heatmap(grid)
            return AttributionResult(
                heatmap=heatmap.detach().cpu().numpy(),
                method=f"attention_layer_{self.layer_index}",
            )
        except AttributionError:
            raise
        except Exception as exc:
            raise AttributionError(f"Attention map generation failed: {exc}") from exc
