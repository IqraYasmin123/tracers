"""AttributionResult — the common output type for every attribution method."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch


def normalize_heatmap(raw: torch.Tensor) -> torch.Tensor:
    """Min-max normalize a heatmap tensor to [0, 1].

    Handles the degenerate case where the heatmap is perfectly constant (e.g. a fully
    uniform attention distribution) — without this guard, dividing by a zero range would
    produce NaNs instead of a meaningful (all-zero, "nothing stands out") heatmap.
    """
    minimum = raw.min()
    maximum = raw.max()
    if (maximum - minimum).item() < 1e-9:
        return torch.zeros_like(raw)
    return (raw - minimum) / (maximum - minimum)


@dataclass
class AttributionResult:
    """A forensic attribution heatmap, plus which method produced it.

    `heatmap` may be a different resolution than the original image (e.g. a 7x7 attention
    grid vs. a 224x224 gradient map) — use `.resized()` to get it at any target resolution
    for overlaying on the original image.
    """

    heatmap: np.ndarray  # 2D array, values in [0, 1]
    method: str

    def resized(self, size: tuple[int, int]) -> np.ndarray:
        """Bilinearly resize the heatmap to (height, width)."""
        tensor = torch.tensor(self.heatmap, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
        resized = torch.nn.functional.interpolate(
            tensor, size=size, mode="bilinear", align_corners=False
        )
        return resized.squeeze().numpy()
