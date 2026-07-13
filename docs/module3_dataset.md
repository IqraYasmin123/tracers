# Module 3 — Dataset Management

## Goal

Replace the CIFAR-100 stand-in used for early pipeline testing with a real image-caption
dataset (Flickr8k), behind a clean, testable, swappable interface — same pattern as Module 2.

## Design

```
BaseDataset (abstract interface)
    ├── __len__()
    ├── __getitem__(index) -> {"image": PIL.Image, "caption": str, "id": str}
    └── get_split(split) -> BaseDataset restricted to "train"/"val"/"test"

FlickrDataset(BaseDataset)  — real Flickr8k implementation
DatasetConfig               — configuration dataclass (paths, split ratios, seed, image size)
split_indices()             — reusable, seeded train/val/test index splitting
show_samples()               — visualization utility
DatasetLoadError             — module-specific exception
```

### Why Flickr8k over full COCO

Flickr8k is ~8,000 images with 5 human-written captions each — small enough to download and
iterate on within a free Colab session, while still being real photographs with real language
(unlike CIFAR-100's single-word class labels). Full COCO (~120k images) is a reasonable future
extension but adds storage/time cost not justified for an FYP-scale detection/attribution
pipeline. This tradeoff is worth stating explicitly in your report.

### Handling real-world dataset mirror variance

Different Flickr8k mirrors extract to slightly different folder/file names (`Images/` vs
`Flicker8k_Dataset/`, `captions.txt` vs `Flickr8k.token.txt`). `FlickrDataset._find_images_dir()`
and `_find_captions_file()` check a list of known candidate names, so the same code works
regardless of which mirror you used — you don't need to manually rename folders after
extraction.

### Reproducible splitting

`split_indices()` takes a `seed` and always produces the same train/val/test partition for
that seed. This matters because Module 5's detection accuracy needs to be compared across
experiments — if the split changed randomly every run, you couldn't tell whether a change in
accuracy came from your detector or from a different test set.

### Why unit tests need no real download

Unlike Module 2 (which needs real CLIP weights to test anything meaningful), Module 3's logic
— parsing, splitting, error handling — is fully testable against a **fake** 10-image dataset
built inline in `tests/test_dataset.py` via `tmp_path`. This is a deliberate testing strategy:
fast, deterministic, no network dependency for the test suite. The real Flickr8k download only
happens in `notebooks/03_dataset_management.ipynb`, for actual visual inspection with real
photos.

## Testing Strategy

```bash
pytest tests/test_dataset.py -v   # 14 tests, all self-contained, no network needed
```

All tests pass without downloading anything — verified.

## Completion Checklist

- [x] `BaseDataset` interface defined
- [x] `FlickrDataset` implementation complete, handles mirror variance
- [x] `DatasetConfig` with ratio validation
- [x] Reproducible seeded splitting
- [x] 14 unit tests, all passing, no network dependency
- [ ] Real Flickr8k downloaded and visually inspected in Colab (do this yourself — see
      `notebooks/03_dataset_management.ipynb`)
