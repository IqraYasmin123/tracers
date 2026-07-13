"""Reproducible train/val/test index splitting.

Separated from FlickrDataset itself so the split logic can be unit tested in isolation, and
reused by any future dataset implementation without duplicating it.
"""
from __future__ import annotations

import random


def split_indices(
    n: int, train_ratio: float, val_ratio: float, test_ratio: float, seed: int
) -> dict[str, list[int]]:
    """Shuffle and partition `range(n)` into train/val/test index lists.

    Uses a seeded RNG so the same config always produces the same split — this matters for
    TRACER because detection accuracy comparisons across experiments need a stable split,
    not a different random one every run.
    """
    indices = list(range(n))
    random.Random(seed).shuffle(indices)

    n_train = int(round(n * train_ratio))
    n_val = int(round(n * val_ratio))

    return {
        "train": indices[:n_train],
        "val": indices[n_train : n_train + n_val],
        "test": indices[n_train + n_val :],
    }
