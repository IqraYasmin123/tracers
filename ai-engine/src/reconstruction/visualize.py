"""Visualization utilities for reconstruction results."""
from __future__ import annotations

import matplotlib.pyplot as plt


def compare_images(clean, adversarial, reconstructed, titles: list[str] | None = None):
    """Side-by-side comparison of the clean, adversarial, and reconstructed versions of an
    image — the core visual evidence for whether reconstruction actually worked."""
    titles = titles or ["Clean", "Adversarial", "Reconstructed"]
    images = [clean, adversarial, reconstructed]

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, image, title in zip(axes, images, titles):
        ax.imshow(image)
        ax.set_title(title)
        ax.axis("off")
    plt.tight_layout()
    return fig
