"""
MS COCO (2017) implementation of the BaseDataset interface.

Expects a flat layout of:
    <root_dir>/images/*.jpg
    <root_dir>/captions_val2017.json   (or captions_train2017.json)

This matches what you get from downloading a COCO subset via fiftyone and moving the
images + the relevant captions_*.json out of its zoo cache — see docs/module3_dataset.md
for the exact commands. Only one caption per image is kept (COCO ships ~5 per image);
same simplification FlickrDataset makes, for the same reason — one (image, caption) pair
is enough for TRACER's purposes, and keeping all 5 would just inflate sample count without
adding distinct images.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image

from .base import BaseDataset
from .config import DatasetConfig
from .exceptions import DatasetLoadError
from .splitter import split_indices

_CAPTION_FILE_CANDIDATES = [
    "captions_val2017.json",
    "captions_train2017.json",
    "captions.json",
]
_IMAGE_DIR_CANDIDATES = ["images", "val2017", "train2017"]


class CocoDataset(BaseDataset):
    """MS COCO dataset: real photos paired with human-written captions."""

    def __init__(
        self,
        config: DatasetConfig,
        split: str | None = None,
        _samples: list[dict] | None = None,
        _indices: list[int] | None = None,
    ) -> None:
        self.config = config
        self._root = Path(config.root_dir)

        if _samples is not None:
            self._samples = _samples
        else:
            self._samples = self._load_samples()
            if config.max_samples is not None:
                self._samples = self._samples[: config.max_samples]

        if _indices is not None:
            self._indices = _indices
        elif split is not None:
            splits = split_indices(
                len(self._samples),
                config.train_ratio,
                config.val_ratio,
                config.test_ratio,
                config.seed,
            )
            if split not in splits:
                raise ValueError(f"split must be one of {list(splits)}, got '{split}'")
            self._indices = splits[split]
        else:
            self._indices = list(range(len(self._samples)))

    def _find_captions_file(self) -> Path:
        for name in _CAPTION_FILE_CANDIDATES:
            candidate = self._root / name
            if candidate.exists():
                return candidate
        raise DatasetLoadError(
            f"Could not find a captions file under '{self._root}'. "
            f"Expected one of {_CAPTION_FILE_CANDIDATES}."
        )

    def _find_images_dir(self) -> Path:
        for name in _IMAGE_DIR_CANDIDATES:
            candidate = self._root / name
            if candidate.exists() and candidate.is_dir():
                return candidate
        raise DatasetLoadError(
            f"Could not find an images directory under '{self._root}'. "
            f"Expected one of {_IMAGE_DIR_CANDIDATES}."
        )

    def _load_samples(self) -> list[dict]:
        if not self._root.exists():
            raise DatasetLoadError(
                f"Dataset root '{self._root}' does not exist. "
                "See docs/module3_dataset.md for download instructions."
            )

        captions_path = self._find_captions_file()
        images_dir = self._find_images_dir()

        with open(captions_path, "r", encoding="utf-8") as f:
            coco = json.load(f)

        id_to_filename = {img["id"]: img["file_name"] for img in coco.get("images", [])}

        seen: dict[str, dict] = {}
        for ann in coco.get("annotations", []):
            image_id = ann.get("image_id")
            filename = id_to_filename.get(image_id)
            if filename is None or filename in seen:
                continue
            image_path = images_dir / filename
            if not image_path.exists():
                continue
            seen[filename] = {
                "filename": filename,
                "path": image_path,
                "caption": ann.get("caption", "").strip(),
            }

        if not seen:
            raise DatasetLoadError(
                f"No valid (image, caption) pairs found under '{self._root}'. "
                f"Check that '{captions_path.name}' references images that actually "
                f"exist in '{images_dir}'."
            )
        return list(seen.values())

    def __len__(self) -> int:
        return len(self._indices)

    def __getitem__(self, index: int) -> dict[str, Any]:
        real_index = self._indices[index]
        sample = self._samples[real_index]
        image = Image.open(sample["path"]).convert("RGB").resize(self.config.image_size)
        return {"image": image, "caption": sample["caption"], "id": sample["filename"]}

    def get_split(self, split: str) -> "CocoDataset":
        splits = split_indices(
            len(self._samples),
            self.config.train_ratio,
            self.config.val_ratio,
            self.config.test_ratio,
            self.config.seed,
        )
        if split not in splits:
            raise ValueError(f"split must be one of {list(splits)}, got '{split}'")
        return CocoDataset(self.config, _samples=self._samples, _indices=splits[split])
