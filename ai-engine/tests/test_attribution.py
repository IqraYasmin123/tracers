"""Tests for the attribution module (Module 6).

Same strategy as Module 4/5: a minimal in-memory FakeVLM stands in for real CLIP, so the
attribution logic (gradient computation, attention reshaping, normalization) is fully tested
without any network access or model download.

Run:
    pytest tests/test_attribution.py -v
"""
from __future__ import annotations

import torch
import pytest

from src.vlm.base import BaseVLM
from src.attribution import (
    AttentionMap,
    AttributionError,
    AttributionResult,
    GradientSaliency,
    normalize_heatmap,
)


class FakeVLM(BaseVLM):
    """Differentiable stand-in for CLIP, including synthetic (but correctly-shaped) vision
    attentions so AttentionMap can be tested without real CLIP."""

    embed_dim = 8
    num_patches_side = 4  # 4x4 = 16 patches + 1 CLS = 17 tokens, kept small for fast tests
    num_layers = 3
    num_heads = 2

    def preprocess_image(self, image):
        raise NotImplementedError

    def _forward(self, pixel_values: torch.Tensor) -> torch.Tensor:
        pooled = pixel_values.mean(dim=(2, 3))
        if not hasattr(self, "_weight"):
            generator = torch.Generator().manual_seed(1)
            self._weight = torch.randn(pooled.shape[1], self.embed_dim, generator=generator)
        embeds = pooled @ self._weight
        return embeds / (embeds.norm(dim=-1, keepdim=True) + 1e-9)

    def encode_image(self, pixel_values: torch.Tensor, requires_grad: bool = False) -> torch.Tensor:
        if requires_grad:
            return self._forward(pixel_values)
        with torch.no_grad():
            return self._forward(pixel_values)

    def encode_text(self, texts: list[str], requires_grad: bool = False) -> torch.Tensor:
        generator = torch.Generator().manual_seed(0)
        embeds = torch.randn(len(texts), self.embed_dim, generator=generator)
        return embeds / embeds.norm(dim=-1, keepdim=True)

    def similarity(self, image_embeds: torch.Tensor, text_embeds: torch.Tensor) -> torch.Tensor:
        return image_embeds @ text_embeds.T

    def get_vision_attentions(self, pixel_values: torch.Tensor):
        batch = pixel_values.shape[0]
        tokens = self.num_patches_side**2 + 1
        generator = torch.Generator().manual_seed(2)
        attentions = []
        for _ in range(self.num_layers):
            raw = torch.rand(batch, self.num_heads, tokens, tokens, generator=generator)
            attentions.append(torch.softmax(raw, dim=-1))
        return tuple(attentions)


class FakeVLMNonSquarePatches(FakeVLM):
    """A fake VLM whose patch count is deliberately NOT a perfect square, to test that
    AttentionMap correctly rejects layouts it can't reshape."""

    def get_vision_attentions(self, pixel_values: torch.Tensor):
        batch = pixel_values.shape[0]
        tokens = 11  # 10 patch tokens + 1 CLS — 10 is not a perfect square
        generator = torch.Generator().manual_seed(3)
        raw = torch.rand(batch, 2, tokens, tokens, generator=generator)
        return (torch.softmax(raw, dim=-1),)


@pytest.fixture
def fake_vlm():
    return FakeVLM()


@pytest.fixture
def sample_input(fake_vlm):
    pixel_values = torch.rand(1, 3, 8, 8)
    text_embeds = fake_vlm.encode_text(["a caption"])
    return pixel_values, text_embeds


# ---------------------------------------------------------------------------
# normalize_heatmap
# ---------------------------------------------------------------------------


def test_normalize_heatmap_scales_to_unit_range():
    raw = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
    normalized = normalize_heatmap(raw)
    assert normalized.min().item() == pytest.approx(0.0)
    assert normalized.max().item() == pytest.approx(1.0)


def test_normalize_heatmap_constant_returns_zeros():
    raw = torch.full((3, 3), 5.0)
    normalized = normalize_heatmap(raw)
    assert torch.all(normalized == 0)


# ---------------------------------------------------------------------------
# AttributionResult
# ---------------------------------------------------------------------------


def test_attribution_result_resized():
    import numpy as np

    result = AttributionResult(heatmap=np.random.rand(4, 4).astype("float32"), method="test")
    resized = result.resized((16, 16))
    assert resized.shape == (16, 16)


# ---------------------------------------------------------------------------
# GradientSaliency
# ---------------------------------------------------------------------------


def test_gradient_saliency_requires_text_embeds(fake_vlm, sample_input):
    pixel_values, _ = sample_input
    with pytest.raises(AttributionError):
        GradientSaliency().generate(fake_vlm, pixel_values, text_embeds=None)


def test_gradient_saliency_produces_correct_shape(fake_vlm, sample_input):
    pixel_values, text_embeds = sample_input
    result = GradientSaliency().generate(fake_vlm, pixel_values, text_embeds)

    assert result.heatmap.shape == (8, 8)  # matches pixel_values' spatial dims
    assert result.method == "gradient_saliency"


def test_gradient_saliency_values_in_unit_range(fake_vlm, sample_input):
    pixel_values, text_embeds = sample_input
    result = GradientSaliency().generate(fake_vlm, pixel_values, text_embeds)

    assert result.heatmap.min() >= 0.0
    assert result.heatmap.max() <= 1.0 + 1e-6


# ---------------------------------------------------------------------------
# AttentionMap
# ---------------------------------------------------------------------------


def test_attention_map_produces_correct_grid_shape(fake_vlm, sample_input):
    pixel_values, _ = sample_input
    result = AttentionMap(layer_index=-1).generate(fake_vlm, pixel_values)

    assert result.heatmap.shape == (fake_vlm.num_patches_side, fake_vlm.num_patches_side)
    assert result.method == "attention_layer_-1"


def test_attention_map_values_in_unit_range(fake_vlm, sample_input):
    pixel_values, _ = sample_input
    result = AttentionMap().generate(fake_vlm, pixel_values)

    assert result.heatmap.min() >= 0.0
    assert result.heatmap.max() <= 1.0 + 1e-6


def test_attention_map_specific_layer_index(fake_vlm, sample_input):
    pixel_values, _ = sample_input
    result = AttentionMap(layer_index=0).generate(fake_vlm, pixel_values)
    assert result.method == "attention_layer_0"


def test_attention_map_rejects_non_square_patch_count(sample_input):
    pixel_values, _ = sample_input
    non_square_vlm = FakeVLMNonSquarePatches()
    with pytest.raises(AttributionError):
        AttentionMap().generate(non_square_vlm, pixel_values)
