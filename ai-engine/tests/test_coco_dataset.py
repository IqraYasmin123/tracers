"""Tests for CocoDataset (Module 3 extension).

Same approach as test_dataset.py — a `tmp_path` fixture builds a tiny fake COCO-structured
folder (images/ + captions_val2017.json in real COCO annotation format) so these tests need
no network access and no real ~20GB download.

Run:
    pytest tests/test_coco_dataset.py -v
"""
import json

import pytest
from PIL import Image

from src.dataset import CocoDataset, DatasetConfig, DatasetLoadError


@pytest.fixture
def fake_coco_dir(tmp_path):
    """Build a minimal fake COCO-structured folder: images/ + captions_val2017.json."""
    images_dir = tmp_path / "images"
    images_dir.mkdir()

    images = []
    annotations = []
    for i in range(10):
        filename = f"{i:012d}.jpg"
        Image.new("RGB", (64, 64), color=(i * 20 % 255, 100, 150)).save(images_dir / filename)
        images.append({"id": i, "file_name": filename})
        annotations.append({"image_id": i, "id": i * 2, "caption": f"caption number {i}"})
        annotations.append(
            {"image_id": i, "id": i * 2 + 1, "caption": "a second caption that should be ignored"}
        )

    coco_json = {"images": images, "annotations": annotations}
    (tmp_path / "captions_val2017.json").write_text(json.dumps(coco_json), encoding="utf-8")
    return tmp_path


def test_dataset_load_error_on_missing_root():
    config = DatasetConfig(root_dir="/this/path/does/not/exist")
    with pytest.raises(DatasetLoadError):
        CocoDataset(config)


def test_dataset_load_error_on_empty_dir(tmp_path):
    config = DatasetConfig(root_dir=str(tmp_path))
    with pytest.raises(DatasetLoadError):
        CocoDataset(config)


def test_dataset_load_error_when_captions_reference_missing_images(tmp_path):
    coco_json = {
        "images": [{"id": 0, "file_name": "000000000000.jpg"}],
        "annotations": [{"image_id": 0, "id": 0, "caption": "a caption"}],
    }
    (tmp_path / "captions_val2017.json").write_text(json.dumps(coco_json), encoding="utf-8")
    (tmp_path / "images").mkdir()
    config = DatasetConfig(root_dir=str(tmp_path))
    with pytest.raises(DatasetLoadError):
        CocoDataset(config)


def test_dataset_loads_correct_length(fake_coco_dir):
    config = DatasetConfig(root_dir=str(fake_coco_dir))
    ds = CocoDataset(config)
    assert len(ds) == 10


def test_dataset_getitem_shape_and_keys(fake_coco_dir):
    config = DatasetConfig(root_dir=str(fake_coco_dir), image_size=(224, 224))
    ds = CocoDataset(config)
    sample = ds[0]
    assert set(sample.keys()) == {"image", "caption", "id"}
    assert sample["image"].size == (224, 224)
    assert isinstance(sample["caption"], str) and len(sample["caption"]) > 0


def test_dataset_keeps_first_caption_only(fake_coco_dir):
    config = DatasetConfig(root_dir=str(fake_coco_dir))
    ds = CocoDataset(config)
    captions = {ds[i]["caption"] for i in range(len(ds))}
    assert "a second caption that should be ignored" not in captions


def test_dataset_respects_max_samples(fake_coco_dir):
    config = DatasetConfig(root_dir=str(fake_coco_dir), max_samples=4)
    ds = CocoDataset(config)
    assert len(ds) == 4


def test_dataset_skips_images_not_on_disk(tmp_path):
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    images, annotations = [], []
    for i in range(5):
        filename = f"{i:012d}.jpg"
        images.append({"id": i, "file_name": filename})
        annotations.append({"image_id": i, "id": i, "caption": f"caption {i}"})
        if i < 3:
            Image.new("RGB", (64, 64)).save(images_dir / filename)
    (tmp_path / "captions_val2017.json").write_text(
        json.dumps({"images": images, "annotations": annotations}), encoding="utf-8"
    )
    config = DatasetConfig(root_dir=str(tmp_path))
    ds = CocoDataset(config)
    assert len(ds) == 3


def test_get_split_covers_all_samples_without_overlap(fake_coco_dir):
    config = DatasetConfig(
        root_dir=str(fake_coco_dir), train_ratio=0.6, val_ratio=0.2, test_ratio=0.2
    )
    ds = CocoDataset(config)
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


def test_get_split_invalid_name_raises(fake_coco_dir):
    config = DatasetConfig(root_dir=str(fake_coco_dir))
    ds = CocoDataset(config)
    with pytest.raises(ValueError):
        ds.get_split("not_a_real_split")


def test_falls_back_to_train_captions_filename(tmp_path):
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    filename = "000000000001.jpg"
    Image.new("RGB", (64, 64)).save(images_dir / filename)
    coco_json = {
        "images": [{"id": 1, "file_name": filename}],
        "annotations": [{"image_id": 1, "id": 1, "caption": "a caption"}],
    }
    (tmp_path / "captions_train2017.json").write_text(json.dumps(coco_json), encoding="utf-8")
    config = DatasetConfig(root_dir=str(tmp_path))
    ds = CocoDataset(config)
    assert len(ds) == 1
