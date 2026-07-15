"""Visualization utilities for attribution results."""
from __future__ import annotations

import matplotlib.pyplot as plt

from .result import AttributionResult


def show_attribution(image, result: AttributionResult, alpha: float = 0.5):
    """Show the original image next to it with the heatmap overlaid.

    `image` should be a PIL Image (has .width/.height, used to resize the heatmap to match).
    """
    heatmap_resized = result.resized((image.height, image.width))

    fig, ax = plt.subplots(1, 2, figsize=(8, 4))
    ax[0].imshow(image)
    ax[0].set_title("Image")
    ax[0].axis("off")

    ax[1].imshow(image)
    ax[1].imshow(heatmap_resized, cmap="jet", alpha=alpha)
    ax[1].set_title(f"Attribution ({result.method})")
    ax[1].axis("off")

    plt.tight_layout()
    return fig
