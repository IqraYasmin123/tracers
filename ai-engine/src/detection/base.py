"""
Abstract base interface for TRACER's detection/classification models.

Same interface serves two roles depending on what labels it's trained with: a binary
clean-vs-adversarial detector, or a multi-class attack-type classifier (clean/fgsm/pgd).
Module 9 (backend) will depend on this interface, not on any specific sklearn model — the
underlying classifier could be swapped (e.g. for a small transformer over the entropy
sequence, mentioned as a stretch goal in the FYP guide) without touching calling code.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class BaseDetector(ABC):
    """Abstract interface every TRACER detection/classification model must implement."""

    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray) -> "BaseDetector":
        raise NotImplementedError

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    @abstractmethod
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    @abstractmethod
    def save(self, path: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def load(self, path: str) -> "BaseDetector":
        raise NotImplementedError
