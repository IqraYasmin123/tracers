"""Configuration for TRACER's entropy-based classifier."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DetectionConfig:
    """Configuration for EntropyClassifier.

    Attributes:
        hidden_layer_sizes: MLP architecture. Small on purpose — the input is only a
            per-layer entropy vector (12 numbers for CLIP ViT-B/32), not raw pixels, so a
            large network would just overfit.
        max_iter: Training iterations cap.
        random_state: Fixed seed for reproducible training results across runs.
    """

    hidden_layer_sizes: tuple = field(default_factory=lambda: (32, 16))
    max_iter: int = 1000
    random_state: int = 42
