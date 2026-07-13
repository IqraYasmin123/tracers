"""Configuration for TRACER datasets."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DatasetConfig:
    """Configuration for loading and splitting a dataset.

    Attributes:
        root_dir: Path to the extracted dataset (images + captions file).
        image_size: Target (width, height) all images are resized to.
        train_ratio, val_ratio, test_ratio: Must sum to 1.0.
        seed: Random seed for the train/val/test split — fixed by default so results are
            reproducible across runs (important for comparing detector accuracy later).
        max_samples: If set, only the first N samples are used — useful for a fast smoke
            test of the pipeline before committing to loading the full dataset.
    """

    root_dir: str
    image_size: tuple[int, int] = (224, 224)
    train_ratio: float = 0.8
    val_ratio: float = 0.1
    test_ratio: float = 0.1
    seed: int = 42
    max_samples: int | None = None

    def __post_init__(self) -> None:
        total = self.train_ratio + self.val_ratio + self.test_ratio
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"train_ratio + val_ratio + test_ratio must sum to 1.0, got {total}"
            )
        if any(r < 0 for r in (self.train_ratio, self.val_ratio, self.test_ratio)):
            raise ValueError("Split ratios must be non-negative.")
