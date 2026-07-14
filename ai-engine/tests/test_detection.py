"""Tests for the detection module (Module 5).

Two independent things get tested here, both without any CLIP download or network access:

1. The core entropy math (`compute_entropy_from_attentions`) — tested with hand-crafted
   attention tensors where we know the correct entropy value analytically (uniform
   attention = maximum entropy, one-hot attention = zero entropy).
2. The classifier (`EntropyClassifier`) — tested with synthetic, clearly-separable feature
   data, both as a binary detector and as a multi-class attack-type classifier.

Run:
    pytest tests/test_detection.py -v
"""
from __future__ import annotations

import math

import numpy as np
import pytest
import torch

from src.detection import (
    DetectionConfig,
    DetectionError,
    DetectorNotFittedError,
    EntropyClassifier,
    compute_entropy_from_attentions,
)

# ---------------------------------------------------------------------------
# compute_entropy_from_attentions — core methodology, tested with known values
# ---------------------------------------------------------------------------


def test_uniform_attention_gives_maximum_entropy():
    """A uniform attention distribution over N tokens has entropy exactly log(N) —
    the theoretical maximum. This is the simplest possible correctness check for the
    entire detection methodology."""
    batch, heads, tokens = 1, 2, 4
    uniform = torch.full((batch, heads, tokens, tokens), 1.0 / tokens)
    attentions = (uniform,)  # one layer

    entropy = compute_entropy_from_attentions(attentions)

    expected = math.log(tokens)
    assert entropy.shape == (batch, 1)
    assert torch.allclose(entropy, torch.tensor([[expected]]), atol=1e-4)


def test_one_hot_attention_gives_near_zero_entropy():
    """A one-hot (fully concentrated) attention distribution has entropy near zero —
    the theoretical minimum."""
    batch, heads, tokens = 1, 2, 4
    one_hot = torch.zeros((batch, heads, tokens, tokens))
    one_hot[..., 0] = 1.0  # every query attends entirely to the first key token
    attentions = (one_hot,)

    entropy = compute_entropy_from_attentions(attentions)

    assert entropy.shape == (batch, 1)
    assert entropy.item() < 1e-3


def test_multiple_layers_produce_correct_shape():
    batch, heads, tokens, num_layers = 2, 4, 10, 12
    attentions = tuple(
        torch.softmax(torch.randn(batch, heads, tokens, tokens), dim=-1)
        for _ in range(num_layers)
    )
    entropy = compute_entropy_from_attentions(attentions)
    assert entropy.shape == (batch, num_layers)


def test_uniform_entropy_exceeds_one_hot_entropy():
    """Sanity check that the ordering is right: more spread-out attention -> higher entropy."""
    tokens = 8
    uniform = torch.full((1, 1, tokens, tokens), 1.0 / tokens)
    one_hot = torch.zeros((1, 1, tokens, tokens))
    one_hot[..., 0] = 1.0

    uniform_entropy = compute_entropy_from_attentions((uniform,)).item()
    one_hot_entropy = compute_entropy_from_attentions((one_hot,)).item()

    assert uniform_entropy > one_hot_entropy


def test_empty_attentions_raises_detection_error():
    with pytest.raises(DetectionError):
        compute_entropy_from_attentions(())


# ---------------------------------------------------------------------------
# EntropyClassifier — binary detection, tested with synthetic separable data
# ---------------------------------------------------------------------------


@pytest.fixture
def separable_binary_data():
    """Two well-separated Gaussian clusters standing in for clean vs adversarial entropy
    fingerprints. Real detection accuracy is verified in Colab with real CLIP features —
    this only checks the classifier's plumbing (fit/predict/proba/save/load) is correct."""
    rng = np.random.RandomState(42)
    clean = rng.normal(loc=2.0, scale=0.3, size=(60, 12))
    adversarial = rng.normal(loc=-2.0, scale=0.3, size=(60, 12))
    X = np.vstack([clean, adversarial])
    y = np.array(["clean"] * 60 + ["adversarial"] * 60)
    return X, y


def test_predict_before_fit_raises():
    classifier = EntropyClassifier()
    with pytest.raises(DetectorNotFittedError):
        classifier.predict(np.zeros((1, 12)))


def test_fit_on_empty_data_raises():
    classifier = EntropyClassifier()
    with pytest.raises(DetectionError):
        classifier.fit(np.empty((0, 12)), np.array([]))


def test_binary_classifier_achieves_high_accuracy(separable_binary_data):
    X, y = separable_binary_data
    classifier = EntropyClassifier(DetectionConfig(max_iter=500)).fit(X, y)

    predictions = classifier.predict(X)
    accuracy = (predictions == y).mean()

    assert accuracy > 0.95  # well-separated synthetic data should be nearly perfectly learned
    assert set(classifier.classes_) == {"clean", "adversarial"}


def test_predict_proba_shape_and_range(separable_binary_data):
    X, y = separable_binary_data
    classifier = EntropyClassifier(DetectionConfig(max_iter=500)).fit(X, y)

    probs = classifier.predict_proba(X)

    assert probs.shape == (len(X), 2)
    assert np.all(probs >= 0) and np.all(probs <= 1)
    assert np.allclose(probs.sum(axis=1), 1.0, atol=1e-5)


def test_save_and_load_roundtrip(separable_binary_data, tmp_path):
    X, y = separable_binary_data
    classifier = EntropyClassifier(DetectionConfig(max_iter=500)).fit(X, y)
    original_predictions = classifier.predict(X)

    save_path = tmp_path / "detector.joblib"
    classifier.save(str(save_path))

    reloaded = EntropyClassifier().load(str(save_path))
    reloaded_predictions = reloaded.predict(X)

    assert np.array_equal(original_predictions, reloaded_predictions)
    assert reloaded.classes_ == classifier.classes_


# ---------------------------------------------------------------------------
# EntropyClassifier — same class, used as a multi-class attack-type classifier
# ---------------------------------------------------------------------------


@pytest.fixture
def separable_multiclass_data():
    rng = np.random.RandomState(0)
    clean = rng.normal(loc=3.0, scale=0.2, size=(40, 12))
    fgsm = rng.normal(loc=0.0, scale=0.2, size=(40, 12))
    pgd = rng.normal(loc=-3.0, scale=0.2, size=(40, 12))
    X = np.vstack([clean, fgsm, pgd])
    y = np.array(["clean"] * 40 + ["fgsm"] * 40 + ["pgd"] * 40)
    return X, y


def test_multiclass_classifier_achieves_high_accuracy(separable_multiclass_data):
    X, y = separable_multiclass_data
    classifier = EntropyClassifier(DetectionConfig(max_iter=500)).fit(X, y)

    predictions = classifier.predict(X)
    accuracy = (predictions == y).mean()

    assert accuracy > 0.9
    assert set(classifier.classes_) == {"clean", "fgsm", "pgd"}


def test_multiclass_predict_proba_shape(separable_multiclass_data):
    X, y = separable_multiclass_data
    classifier = EntropyClassifier(DetectionConfig(max_iter=500)).fit(X, y)

    probs = classifier.predict_proba(X)
    assert probs.shape == (len(X), 3)
