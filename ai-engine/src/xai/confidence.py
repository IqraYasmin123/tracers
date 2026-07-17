"""Confidence-level categorization for explanations."""
from __future__ import annotations


def confidence_level_from_probability(probability: float) -> str:
    """Map a raw probability to a human-readable confidence category.

    Thresholds (0.85 / 0.60) are a deliberate, simple, documented choice — not derived from
    any calibration study. If your report needs calibrated confidence categories, that would
    be a reasonable future-work extension (e.g. via a held-out calibration set).
    """
    if not (0.0 <= probability <= 1.0):
        raise ValueError(f"probability must be in [0,1], got {probability}")
    if probability >= 0.85:
        return "high"
    if probability >= 0.60:
        return "medium"
    return "low"
