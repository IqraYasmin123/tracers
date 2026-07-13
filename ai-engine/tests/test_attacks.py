"""Tests for the attacks module (Module 4).

These tests use a minimal in-memory FakeVLM instead of real CLIP — a direct demonstration of
the Liskov Substitution Principle: FGSMAttack/PGDAttack are written against BaseVLM, so they
work correctly against ANY conforming implementation, real or fake. This makes the whole
test suite fast and network-independent, while still genuinely testing the attack math
(gradient direction, epsilon bounding, actual similarity degradation).

Run:
    pytest tests/test_attacks.py -v
"""
from __future__ import annotations

import torch
import pytest

from src.vlm.base import BaseVLM
from src.attacks import AttackConfig, AttackGenerationError, FGSMAttack, PGDAttack


class FakeVLM(BaseVLM):
    """Minimal differentiable stand-in for a real VLM: mean-pools pixel values over spatial
    dimensions and projects to a small embedding space with a fixed linear map. Simple, but
    genuinely differentiable — enough to test real attack gradient math without downloading
    anything."""

    embed_dim = 8

    def preprocess_image(self, image):  # not needed for these tests
        raise NotImplementedError

    def _forward(self, pixel_values: torch.Tensor) -> torch.Tensor:
        pooled = pixel_values.mean(dim=(2, 3))  # [batch, channels]
        if not hasattr(self, "_weight"):
            # A fixed (seeded) but non-degenerate projection. An all-ones or otherwise
            # rank-deficient weight matrix here would make every output dimension identical
            # regardless of input, collapsing to a constant vector after normalization —
            # which gives zero gradient almost everywhere. Random weights avoid that.
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

    def get_vision_attentions(self, pixel_values):  # not needed for these tests
        raise NotImplementedError


@pytest.fixture
def fake_vlm():
    return FakeVLM()


@pytest.fixture
def sample_input(fake_vlm):
    pixel_values = torch.rand(1, 3, 8, 8)
    text_embeds = fake_vlm.encode_text(["a caption describing the image"])
    return pixel_values, text_embeds


# ---------------------------------------------------------------------------
# AttackConfig validation
# ---------------------------------------------------------------------------


def test_attack_config_defaults():
    config = AttackConfig()
    assert config.epsilon > 0
    assert config.alpha > 0
    assert config.steps >= 1


def test_attack_config_rejects_non_positive_epsilon():
    with pytest.raises(ValueError):
        AttackConfig(epsilon=0)


def test_attack_config_rejects_non_positive_alpha():
    with pytest.raises(ValueError):
        AttackConfig(alpha=-0.01)


def test_attack_config_rejects_zero_steps():
    with pytest.raises(ValueError):
        AttackConfig(steps=0)


# ---------------------------------------------------------------------------
# FGSM
# ---------------------------------------------------------------------------


def test_fgsm_perturbation_within_epsilon_bound(fake_vlm, sample_input):
    pixel_values, text_embeds = sample_input
    config = AttackConfig(epsilon=0.05)
    adv = FGSMAttack(config).generate(fake_vlm, pixel_values, text_embeds)

    max_diff = (adv - pixel_values).abs().max().item()
    assert max_diff <= config.epsilon + 1e-6


def test_fgsm_actually_changes_the_image(fake_vlm, sample_input):
    pixel_values, text_embeds = sample_input
    adv = FGSMAttack(AttackConfig(epsilon=0.05)).generate(fake_vlm, pixel_values, text_embeds)
    assert not torch.allclose(adv, pixel_values)


def test_fgsm_reduces_similarity(fake_vlm, sample_input):
    pixel_values, text_embeds = sample_input
    adv = FGSMAttack(AttackConfig(epsilon=0.1)).generate(fake_vlm, pixel_values, text_embeds)

    clean_sim = fake_vlm.similarity(fake_vlm.encode_image(pixel_values), text_embeds).item()
    adv_sim = fake_vlm.similarity(fake_vlm.encode_image(adv), text_embeds).item()

    assert adv_sim < clean_sim  # the whole point of the attack


# ---------------------------------------------------------------------------
# PGD
# ---------------------------------------------------------------------------


def test_pgd_perturbation_within_epsilon_bound(fake_vlm, sample_input):
    pixel_values, text_embeds = sample_input
    config = AttackConfig(epsilon=0.05, alpha=0.01, steps=10)
    adv = PGDAttack(config).generate(fake_vlm, pixel_values, text_embeds)

    max_diff = (adv - pixel_values).abs().max().item()
    assert max_diff <= config.epsilon + 1e-6


def test_pgd_actually_changes_the_image(fake_vlm, sample_input):
    pixel_values, text_embeds = sample_input
    config = AttackConfig(epsilon=0.05, alpha=0.01, steps=10)
    adv = PGDAttack(config).generate(fake_vlm, pixel_values, text_embeds)
    assert not torch.allclose(adv, pixel_values)


def test_pgd_reduces_similarity(fake_vlm, sample_input):
    pixel_values, text_embeds = sample_input
    config = AttackConfig(epsilon=0.1, alpha=0.02, steps=10)
    adv = PGDAttack(config).generate(fake_vlm, pixel_values, text_embeds)

    clean_sim = fake_vlm.similarity(fake_vlm.encode_image(pixel_values), text_embeds).item()
    adv_sim = fake_vlm.similarity(fake_vlm.encode_image(adv), text_embeds).item()

    assert adv_sim < clean_sim


def test_pgd_respects_step_count(fake_vlm, sample_input):
    """More steps with a small alpha should still stay within the epsilon bound —
    regression test for the projection step actually running every iteration."""
    pixel_values, text_embeds = sample_input
    config = AttackConfig(epsilon=0.03, alpha=0.05, steps=20)  # alpha > epsilon on purpose
    adv = PGDAttack(config).generate(fake_vlm, pixel_values, text_embeds)

    max_diff = (adv - pixel_values).abs().max().item()
    assert max_diff <= config.epsilon + 1e-6  # projection must clip even oversized steps
