"""
Gradient-based saliency attribution (Grad-CAM style, at the input level).

Reuses `similarity_loss` from Module 4's attacks — the same gradient that tells an attacker
which direction to perturb pixels in also tells us, at the clean or adversarial image, which
pixels the image-caption similarity is most sensitive to. High-gradient-magnitude regions are
the forensic "trigger zone" this module surfaces.

Limitation worth noting in your report: this is a sensitivity map, not a ground-truth
localization of exactly which pixels an attacker changed. For a rigorous localization metric,
compare this heatmap against the actual known perturbation mask
(|adversarial_pixels - clean_pixels| > threshold) via IoU — listed as a stretch-goal
evaluation in the Module 4/5 notebooks, since only synthetic attacks (where you generated the
attack yourself) have that ground truth available.
"""
from __future__ import annotations

import torch

from src.attacks.utils import similarity_loss
from src.vlm.base import BaseVLM

from .base import BaseAttribution
from .exceptions import AttributionError
from .result import AttributionResult, normalize_heatmap


class GradientSaliency(BaseAttribution):
    """Input-gradient saliency: |d(similarity)/d(pixel)|, averaged over color channels."""

    def generate(
        self,
        vlm: BaseVLM,
        pixel_values: torch.Tensor,
        text_embeds: torch.Tensor | None = None,
    ) -> AttributionResult:
        if text_embeds is None:
            raise AttributionError(
                "GradientSaliency requires text_embeds (the caption to compute similarity "
                "gradients against) — pass the image's true or expected caption embedding."
            )

        try:
            pv = pixel_values.clone().detach().requires_grad_(True)
            loss = similarity_loss(vlm, pv, text_embeds)
            loss.backward()

            if pv.grad is None:
                raise AttributionError(
                    "No gradient was computed for the input image — check that the VLM's "
                    "encode_image() correctly supports requires_grad=True."
                )

            # Average absolute gradient over color channels -> a single-channel spatial map
            raw_map = pv.grad.abs().mean(dim=1).squeeze(0)  # [H, W]
            heatmap = normalize_heatmap(raw_map)
            return AttributionResult(
                heatmap=heatmap.detach().cpu().numpy(), method="gradient_saliency"
            )
        except AttributionError:
            raise
        except Exception as exc:
            raise AttributionError(f"Gradient saliency generation failed: {exc}") from exc
