"""Dataset management (Module 3).

Public API:
    BaseDataset      — abstract interface every dataset implements
    FlickrDataset    — Flickr8k implementation of BaseDataset
    DatasetConfig    — configuration dataclass
    DatasetLoadError — module-specific exception
    split_indices    — reusable train/val/test index splitting
    show_samples     — visualization utility

Example:
    >>> from src.dataset import FlickrDataset, DatasetConfig
    >>> config = DatasetConfig(root_dir="/content/drive/MyDrive/TRACER/datasets/flickr8k")
    >>> train_ds = FlickrDataset(config, split="train")
    >>> sample = train_ds[0]
    >>> sample["image"], sample["caption"]
"""
from .base import BaseDataset
from .config import DatasetConfig
from .exceptions import DatasetLoadError
from .flickr_dataset import FlickrDataset
from .splitter import split_indices
from .visualize import show_samples

__all__ = [
    "BaseDataset",
    "FlickrDataset",
    "DatasetConfig",
    "DatasetLoadError",
    "split_indices",
    "show_samples",
]
