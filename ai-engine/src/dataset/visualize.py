"""Visualization utilities for inspecting a dataset."""
from __future__ import annotations

import matplotlib.pyplot as plt

from .base import BaseDataset


def show_samples(dataset: BaseDataset, n: int = 6, cols: int = 3):
    """Display a grid of `n` samples from `dataset`, each with its caption as the title.

    Returns the matplotlib Figure so callers can save it (e.g. for a report) instead of
    only displaying it inline.
    """
    n = min(n, len(dataset))
    if n == 0:
        raise ValueError("Dataset is empty — nothing to show.")

    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 4 * rows))
    axes = axes.flatten() if hasattr(axes, "flatten") else [axes]

    for i in range(n):
        sample = dataset[i]
        axes[i].imshow(sample["image"])
        caption = sample["caption"]
        title = caption if len(caption) <= 40 else caption[:37] + "..."
        axes[i].set_title(title, fontsize=9)
        axes[i].axis("off")

    for j in range(n, len(axes)):
        axes[j].axis("off")

    plt.tight_layout()
    return fig
