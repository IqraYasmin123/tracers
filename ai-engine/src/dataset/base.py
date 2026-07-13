"""
Abstract base interface for datasets used by TRACER.

Same Dependency Inversion pattern as Module 2's BaseVLM: downstream modules (attack
generation, detection training) depend on this interface, not on FlickrDataset directly.
Adding a second dataset (a COCO subset, or your own collected data) later means writing one
new class here — nothing downstream has to change.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseDataset(ABC):
    """Abstract interface every TRACER-supported dataset must implement."""

    @abstractmethod
    def __len__(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def __getitem__(self, index: int) -> dict[str, Any]:
        """Return a dict with at least {'image': PIL.Image, 'caption': str, 'id': str}."""
        raise NotImplementedError

    @abstractmethod
    def get_split(self, split: str) -> "BaseDataset":
        """Return a new BaseDataset instance restricted to 'train', 'val', or 'test'."""
        raise NotImplementedError
