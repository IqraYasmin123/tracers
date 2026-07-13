"""
Flickr8k implementation of the BaseDataset interface.

Handles the real Flickr8k download structure (which varies slightly between mirrors —
"Images/" vs "Flicker8k_Dataset/", "captions.txt" vs "Flickr8k.token.txt") so the rest of
the pipeline never has to know which mirror you used.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image

from .base import BaseDataset
from .config import DatasetConfig
from .exceptions import DatasetLoadError
from .splitter import split_indices

_CAPTION_FILE_CANDIDATES = ["captions.txt", "Flickr8k.token.txt", "Flickr8k.lemma.token.txt"]
_IMAGE_DIR_CANDIDATES = ["Images", "Flicker8k_Dataset", "Flickr8k_Dataset", "images"]


class FlickrDataset(BaseDataset):
    """Flickr8k dataset: real photos paired with human-written captions."""

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
            # Fast path used internally by get_split() — avoids re-parsing the caption file.
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

    # -- discovery helpers -------------------------------------------------

    def _find_captions_file(self) -> Path:
        for name in _CAPTION_FILE_CANDIDATES:
            for candidate in (self._root / name, self._root / "Flickr8k_text" / name):
                if candidate.exists():
                    return candidate
        raise DatasetLoadError(
            f"Could not find a captions file under '{self._root}'. "
            f"Expected one of {_CAPTION_FILE_CANDIDATES}. "
            "Did you extract both the images zip and the text zip into the same folder?"
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

        seen: dict[str, dict] = {}
        with open(captions_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or "\t" not in line:
                    continue
                image_part, caption = line.split("\t", 1)
                filename = image_part.split("#")[0]
                caption_index = image_part.split("#")[1] if "#" in image_part else "0"
                if caption_index != "0":
                    continue  # one caption per image is enough for TRACER's purposes
                image_path = images_dir / filename
                if not image_path.exists():
                    continue
                seen[filename] = {
                    "filename": filename,
                    "path": image_path,
                    "caption": caption.strip(),
                }

        if not seen:
            raise DatasetLoadError(
                f"No valid (image, caption) pairs found under '{self._root}'. "
                "Check that the captions file references images that actually exist "
                f"in '{images_dir}'."
            )
        return list(seen.values())

    # -- BaseDataset interface ----------------------------------------------

    def __len__(self) -> int:
        return len(self._indices)

    def __getitem__(self, index: int) -> dict[str, Any]:
        real_index = self._indices[index]
        sample = self._samples[real_index]
        image = Image.open(sample["path"]).convert("RGB").resize(self.config.image_size)
        return {"image": image, "caption": sample["caption"], "id": sample["filename"]}

    def get_split(self, split: str) -> "FlickrDataset":
        splits = split_indices(
            len(self._samples),
            self.config.train_ratio,
            self.config.val_ratio,
            self.config.test_ratio,
            self.config.seed,
        )
        if split not in splits:
            raise ValueError(f"split must be one of {list(splits)}, got '{split}'")
        return FlickrDataset(self.config, _samples=self._samples, _indices=splits[split])
