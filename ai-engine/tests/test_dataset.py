"""Tests for the dataset module (Module 3).

Unlike Module 2, these tests need no network access and no real Flickr8k download — a
`tmp_path` fixture builds a tiny fake dataset (10 images + a captions file) that mimics the
real structure closely enough to exercise every code path.

Run:
    pytest tests/test_dataset.py -v
"""
import pytest
from PIL import Image

from src.dataset import DatasetConfig, DatasetLoadError, FlickrDataset, split_indices


@pytest.fixture
def fake_flickr_dir(tmp_path):
    """Build a minimal fake Flickr8k-structured folder: Images/ + captions.txt."""
    images_dir = tmp_path / "Images"
    images_dir.mkdir()

    lines = []
    for i in range(10):
        filename = f"img{i}.jpg"
        Image.new("RGB", (64, 64), color=(i * 20 % 255, 100, 150)).save(images_dir / filename)
        lines.append(f"{filename}#0\tcaption number {i}")
        lines.append(f"{filename}#1\ta second caption that should be ignored")

    (tmp_path / "captions.txt").write_text("\n".join(lines), encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------------------
# DatasetConfig validation
# ---------------------------------------------------------------------------


def test_config_accepts_valid_ratios():
    config = DatasetConfig(root_dir=".", train_ratio=0.8, val_ratio=0.1, test_ratio=0.1)
    assert config.train_ratio == 0.8


def test_config_rejects_ratios_not_summing_to_one():
    with pytest.raises(ValueError):
        DatasetConfig(root_dir=".", train_ratio=0.5, val_ratio=0.3, test_ratio=0.3)


def test_config_rejects_negative_ratio():
    with pytest.raises(ValueError):
        DatasetConfig(root_dir=".", train_ratio=1.2, val_ratio=-0.1, test_ratio=-0.1)


# ---------------------------------------------------------------------------
# split_indices
# ---------------------------------------------------------------------------


def test_split_indices_proportions():
    splits = split_indices(100, 0.8, 0.1, 0.1, seed=42)
    assert len(splits["train"]) == 80
    assert len(splits["val"]) == 10
    assert len(splits["test"]) == 10


def test_split_indices_no_overlap_and_covers_all():
    splits = split_indices(100, 0.8, 0.1, 0.1, seed=42)
    all_indices = splits["train"] + splits["val"] + splits["test"]
    assert sorted(all_indices) == list(range(100))


def test_split_indices_reproducible_with_same_seed():
    splits_a = split_indices(50, 0.7, 0.15, 0.15, seed=7)
    splits_b = split_indices(50, 0.7, 0.15, 0.15, seed=7)
    assert splits_a == splits_b


def test_split_indices_differs_with_different_seed():
    splits_a = split_indices(50, 0.7, 0.15, 0.15, seed=1)
    splits_b = split_indices(50, 0.7, 0.15, 0.15, seed=2)
    assert splits_a != splits_b


# ---------------------------------------------------------------------------
# FlickrDataset — error handling
# ---------------------------------------------------------------------------


def test_dataset_load_error_on_missing_root():
    config = DatasetConfig(root_dir="/this/path/does/not/exist")
    with pytest.raises(DatasetLoadError):
        FlickrDataset(config)


def test_dataset_load_error_on_empty_dir(tmp_path):
    config = DatasetConfig(root_dir=str(tmp_path))  # exists but has no captions/images
    with pytest.raises(DatasetLoadError):
        FlickrDataset(config)


# ---------------------------------------------------------------------------
# FlickrDataset — happy path
# ---------------------------------------------------------------------------


def test_dataset_loads_correct_length(fake_flickr_dir):
    config = DatasetConfig(root_dir=str(fake_flickr_dir))
    ds = FlickrDataset(config)
    assert len(ds) == 10  # 10 unique images, second caption (#1) correctly ignored


def test_dataset_getitem_shape_and_keys(fake_flickr_dir):
    config = DatasetConfig(root_dir=str(fake_flickr_dir), image_size=(224, 224))
    ds = FlickrDataset(config)
    sample = ds[0]
    assert set(sample.keys()) == {"image", "caption", "id"}
    assert sample["image"].size == (224, 224)
    assert isinstance(sample["caption"], str) and len(sample["caption"]) > 0


def test_dataset_respects_max_samples(fake_flickr_dir):
    config = DatasetConfig(root_dir=str(fake_flickr_dir), max_samples=4)
    ds = FlickrDataset(config)
    assert len(ds) == 4


def test_get_split_covers_all_samples_without_overlap(fake_flickr_dir):
    config = DatasetConfig(
        root_dir=str(fake_flickr_dir), train_ratio=0.6, val_ratio=0.2, test_ratio=0.2
    )
    ds = FlickrDataset(config)
    train_ds = ds.get_split("train")
    val_ds = ds.get_split("val")
    test_ds = ds.get_split("test")

    assert len(train_ds) + len(val_ds) + len(test_ds) == len(ds)

    train_ids = {train_ds[i]["id"] for i in range(len(train_ds))}
    val_ids = {val_ds[i]["id"] for i in range(len(val_ds))}
    test_ids = {test_ds[i]["id"] for i in range(len(test_ds))}
    assert train_ids.isdisjoint(val_ids)
    assert train_ids.isdisjoint(test_ids)
    assert val_ids.isdisjoint(test_ids)


def test_get_split_invalid_name_raises(fake_flickr_dir):
    config = DatasetConfig(root_dir=str(fake_flickr_dir))
    ds = FlickrDataset(config)
    with pytest.raises(ValueError):
        ds.get_split("not_a_real_split")
