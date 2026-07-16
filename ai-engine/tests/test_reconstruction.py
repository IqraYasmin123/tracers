"""Tests for the reconstruction module (Module 7).

Three independent things get tested, none needing the real multi-GB diffusion model:

1. heatmap_to_mask — pure math, tested with hand-crafted heatmap arrays.
2. compute_reconstruction_metrics — pure math (scikit-image SSIM/PSNR), tested with
   synthetic images where the expected answer is known (identical images -> perfect score;
   very different images -> poor score).
3. DiffusionReconstructor — tested via dependency injection: a lightweight FakePipeline
   stands in for the real Stable Diffusion pipeline, verifying the *plumbing* (mask
   construction, prompt passing) without downloading anything.

Run:
    pytest tests/test_reconstruction.py -v
"""
from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from src.reconstruction import (
    DiffusionReconstructor,
    ReconstructionConfig,
    ReconstructionError,
    compute_reconstruction_metrics,
    heatmap_to_mask,
)

# ---------------------------------------------------------------------------
# heatmap_to_mask
# ---------------------------------------------------------------------------


def test_heatmap_to_mask_basic_thresholding():
    heatmap = np.array([[0.1, 0.9], [0.4, 0.6]], dtype=np.float32)
    mask = heatmap_to_mask(heatmap, threshold=0.5)
    expected = np.array([[0, 255], [0, 255]], dtype=np.uint8)
    assert np.array_equal(mask, expected)


def test_heatmap_to_mask_all_below_threshold_gives_empty_mask():
    heatmap = np.full((4, 4), 0.1, dtype=np.float32)
    mask = heatmap_to_mask(heatmap, threshold=0.5)
    assert np.all(mask == 0)


def test_heatmap_to_mask_all_above_threshold_gives_full_mask():
    heatmap = np.full((4, 4), 0.9, dtype=np.float32)
    mask = heatmap_to_mask(heatmap, threshold=0.5)
    assert np.all(mask == 255)


def test_heatmap_to_mask_rejects_out_of_range_values():
    heatmap = np.array([[0.5, 1.5]], dtype=np.float32)  # 1.5 is out of [0,1]
    with pytest.raises(ReconstructionError):
        heatmap_to_mask(heatmap)


def test_heatmap_to_mask_rejects_invalid_threshold():
    heatmap = np.array([[0.5, 0.5]], dtype=np.float32)
    with pytest.raises(ReconstructionError):
        heatmap_to_mask(heatmap, threshold=1.5)


# ---------------------------------------------------------------------------
# compute_reconstruction_metrics
# ---------------------------------------------------------------------------


def test_metrics_identical_images_give_perfect_scores():
    image = Image.new("RGB", (32, 32), color=(120, 80, 200))
    metrics = compute_reconstruction_metrics(image, image)
    assert metrics["SSIM"] == 1.0
    assert metrics["PSNR"] == 100.0


def test_metrics_very_different_images_give_poor_scores():
    clean = Image.new("RGB", (32, 32), color=(255, 255, 255))
    reconstructed = Image.new("RGB", (32, 32), color=(0, 0, 0))
    metrics = compute_reconstruction_metrics(clean, reconstructed)
    assert metrics["SSIM"] < 0.5
    assert metrics["PSNR"] < 20


def test_metrics_handles_different_sizes_by_resizing():
    clean = Image.new("RGB", (64, 64), color=(100, 100, 100))
    reconstructed = Image.new("RGB", (32, 32), color=(100, 100, 100))
    metrics = compute_reconstruction_metrics(clean, reconstructed)
    assert metrics["SSIM"] == 1.0  # same color, just different original size -> resize matches


def test_metrics_shape_mismatch_after_resize_raises():
    # An RGBA image resized to match an RGB image still won't match on channel count
    clean = Image.new("RGB", (32, 32), color=(100, 100, 100))
    reconstructed = Image.new("RGBA", (32, 32), color=(100, 100, 100, 255))
    with pytest.raises(ReconstructionError):
        compute_reconstruction_metrics(clean, reconstructed)


# ---------------------------------------------------------------------------
# DiffusionReconstructor — tested via a fake injected pipeline, no real model needed
# ---------------------------------------------------------------------------


class FakePipelineResult:
    def __init__(self, images):
        self.images = images


class FakePipeline:
    """Stands in for diffusers' StableDiffusionInpaintPipeline. Records the last call's
    arguments so tests can assert on them, and just echoes the input image back as the
    'reconstruction' (good enough to test plumbing, not image quality)."""

    def __init__(self):
        self.last_call = None

    def __call__(self, prompt, image, mask_image, num_inference_steps=None, guidance_scale=None):
        self.last_call = {
            "prompt": prompt,
            "image": image,
            "mask_image": mask_image,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
        }
        return FakePipelineResult(images=[image])


def test_reconstruct_passes_correct_prompt_to_pipeline():
    fake_pipeline = FakePipeline()
    reconstructor = DiffusionReconstructor(pipeline=fake_pipeline)
    image = Image.new("RGB", (64, 64))
    heatmap = np.random.rand(8, 8).astype(np.float32)

    reconstructor.reconstruct(image, heatmap, prompt="a specific test prompt")

    assert fake_pipeline.last_call["prompt"] == "a specific test prompt"


def test_reconstruct_uses_default_prompt_when_none_given():
    fake_pipeline = FakePipeline()
    config = ReconstructionConfig(default_prompt="the default prompt")
    reconstructor = DiffusionReconstructor(config=config, pipeline=fake_pipeline)
    image = Image.new("RGB", (64, 64))
    heatmap = np.random.rand(8, 8).astype(np.float32)

    reconstructor.reconstruct(image, heatmap)

    assert fake_pipeline.last_call["prompt"] == "the default prompt"


def test_reconstruct_builds_mask_matching_image_size():
    fake_pipeline = FakePipeline()
    reconstructor = DiffusionReconstructor(pipeline=fake_pipeline)
    image = Image.new("RGB", (64, 64))
    heatmap = np.random.rand(8, 8).astype(np.float32)  # smaller than image — must be resized

    reconstructor.reconstruct(image, heatmap)

    mask_image = fake_pipeline.last_call["mask_image"]
    assert mask_image.size == image.size


def test_reconstruct_returns_a_pil_image():
    fake_pipeline = FakePipeline()
    reconstructor = DiffusionReconstructor(pipeline=fake_pipeline)
    image = Image.new("RGB", (64, 64))
    heatmap = np.random.rand(8, 8).astype(np.float32)

    result = reconstructor.reconstruct(image, heatmap)

    assert isinstance(result, Image.Image)


def test_reconstruct_propagates_invalid_heatmap_as_reconstruction_error():
    fake_pipeline = FakePipeline()
    reconstructor = DiffusionReconstructor(pipeline=fake_pipeline)
    image = Image.new("RGB", (64, 64))
    bad_heatmap = np.array([[2.0]], dtype=np.float32)  # out of [0,1] range

    with pytest.raises(ReconstructionError):
        reconstructor.reconstruct(image, bad_heatmap)
