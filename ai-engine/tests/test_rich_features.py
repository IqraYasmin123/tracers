"""Tests for compute_rich_features_from_attentions (Module 5 extension).

Same approach as test_detection.py's entropy tests — hand-crafted attention tensors with
analytically known correct values, no CLIP download or network access needed.

Run:
    pytest tests/test_rich_features.py -v
"""
from __future__ import annotations

import math

import numpy as np
import pytest
import torch

from src.detection import (
    DetectionConfig,
    DetectionError,
    EntropyClassifier,
    compute_rich_features_from_attentions,
)


def test_output_shape_is_3n_minus_1():
    """For num_layers layers, output should be [batch, 3*num_layers - 1]:
    num_layers means + num_layers stds + (num_layers - 1) deltas."""
    batch, heads, tokens, num_layers = 2, 4, 10, 12
    attentions = tuple(
        torch.softmax(torch.randn(batch, heads, tokens, tokens), dim=-1)
        for _ in range(num_layers)
    )
    features = compute_rich_features_from_attentions(attentions)
    assert features.shape == (batch, 3 * num_layers - 1)


def test_uniform_attention_gives_zero_std_and_zero_deltas():
    """If every layer has IDENTICAL uniform attention, each layer's entropy is exactly the
    same constant value everywhere (no spread within a layer -> std=0; no change between
    identical layers -> deltas=0). This isolates the std/delta logic from the mean logic,
    which is already covered by test_detection.py."""
    batch, heads, tokens, num_layers = 1, 4, 8, 3
    uniform = torch.full((batch, heads, tokens, tokens), 1.0 / tokens)
    attentions = tuple(uniform.clone() for _ in range(num_layers))

    features = compute_rich_features_from_attentions(attentions)
    means = features[:, :num_layers]
    stds = features[:, num_layers : 2 * num_layers]
    deltas = features[:, 2 * num_layers :]

    expected_entropy = math.log(tokens)
    assert torch.allclose(means, torch.full((batch, num_layers), expected_entropy), atol=1e-4)
    assert torch.allclose(stds, torch.zeros((batch, num_layers)), atol=1e-4)
    assert torch.allclose(deltas, torch.zeros((batch, num_layers - 1)), atol=1e-4)


def test_mixed_concentration_within_layer_gives_nonzero_std():
    """Half the heads uniform (high entropy), half one-hot (near-zero entropy), within the
    SAME layer -> real spread within that layer -> std should be clearly nonzero, unlike
    the fully-uniform case above."""
    tokens = 8
    uniform_head = torch.full((1, 1, tokens, tokens), 1.0 / tokens)
    one_hot_head = torch.zeros((1, 1, tokens, tokens))
    one_hot_head[..., 0] = 1.0
    mixed_layer = torch.cat([uniform_head, uniform_head, one_hot_head, one_hot_head], dim=1)
    attentions = (mixed_layer,)

    features = compute_rich_features_from_attentions(attentions)
    std = features[0, 1].item()  # num_layers=1, so index 1 is this layer's std

    assert std > 0.5  # two very different entropy values mixed together -> real spread


def test_increasing_entropy_across_layers_gives_positive_deltas():
    """Layer 0 = one-hot (near-zero entropy), layer 1 = uniform (max entropy) ->
    delta[0] = mean[1] - mean[0] should be positive and roughly equal to the max entropy."""
    tokens = 8
    one_hot = torch.zeros((1, 1, tokens, tokens))
    one_hot[..., 0] = 1.0
    uniform = torch.full((1, 1, tokens, tokens), 1.0 / tokens)
    attentions = (one_hot, uniform)

    features = compute_rich_features_from_attentions(attentions)
    delta = features[0, -1].item()  # num_layers=2 -> exactly one delta, the last element

    assert delta > 0
    assert math.isclose(delta, math.log(tokens), abs_tol=1e-3)


def test_empty_attentions_raises_detection_error():
    with pytest.raises(DetectionError):
        compute_rich_features_from_attentions(())


def test_single_layer_gives_zero_deltas():
    """With only one layer there are no adjacent-layer pairs, so the delta portion of the
    feature vector should be empty (shape [batch, 0]), not an error."""
    tokens = 8
    attentions = (torch.full((1, 2, tokens, tokens), 1.0 / tokens),)
    features = compute_rich_features_from_attentions(attentions)
    assert features.shape == (1, 2)  # 1 mean + 1 std + 0 deltas


# ---------------------------------------------------------------------------
# Integration: rich features are just a wider vector -- EntropyClassifier shouldn't care
# ---------------------------------------------------------------------------


def test_classifier_accepts_rich_feature_dimensionality():
    """EntropyClassifier makes no assumption about input width -- confirm a 35-dim rich
    feature vector (matching CLIP ViT-B/32's 12 layers: 12+12+11) trains and predicts fine,
    same as the existing 12-dim mean-only vector does in test_detection.py."""
    rng = np.random.RandomState(42)
    clean = rng.normal(loc=2.0, scale=0.3, size=(40, 35))
    adversarial = rng.normal(loc=-2.0, scale=0.3, size=(40, 35))
    X = np.vstack([clean, adversarial])
    y = np.array(["clean"] * 40 + ["adversarial"] * 40)

    classifier = EntropyClassifier(DetectionConfig(max_iter=500)).fit(X, y)
    predictions = classifier.predict(X)

    assert (predictions == y).mean() > 0.95
