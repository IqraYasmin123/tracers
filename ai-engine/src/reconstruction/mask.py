"""Convert a normalized attribution heatmap into a binary inpainting mask."""
from __future__ import annotations

import numpy as np

from .exceptions import ReconstructionError


def heatmap_to_mask(heatmap: np.ndarray, threshold: float = 0.5) -> np.ndarray:
    """Binarize a [0,1]-normalized heatmap into a 0/255 uint8 mask.

    Pixels above `threshold` are marked 255 (inpaint this region — the attribution method
    flagged it as forensically significant); everything else is 0 (leave untouched).
    """
    if heatmap.min() < -1e-6 or heatmap.max() > 1 + 1e-6:
        raise ReconstructionError(
            f"heatmap values must be in [0,1] (this function expects the output of "
            f"src.attribution's normalize_heatmap), got range "
            f"[{heatmap.min():.4f}, {heatmap.max():.4f}]"
        )
    if not (0.0 <= threshold <= 1.0):
        raise ReconstructionError(f"threshold must be in [0,1], got {threshold}")

    return (heatmap > threshold).astype(np.uint8) * 255
