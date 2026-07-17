"""Tests for the XAI module (Module 8).

This module has zero dependency on torch, CLIP, or any heavy model — these tests run in
milliseconds and need nothing beyond plain Python.

Run:
    pytest tests/test_xai.py -v
"""
import pytest

from src.xai import (
    Explanation,
    ExplanationContext,
    RuleBasedExplainer,
    confidence_level_from_probability,
)

# ---------------------------------------------------------------------------
# confidence_level_from_probability — boundary-tested
# ---------------------------------------------------------------------------


def test_confidence_level_high_at_and_above_085():
    assert confidence_level_from_probability(0.85) == "high"
    assert confidence_level_from_probability(1.0) == "high"


def test_confidence_level_medium_just_below_085():
    assert confidence_level_from_probability(0.849) == "medium"


def test_confidence_level_medium_at_and_above_060():
    assert confidence_level_from_probability(0.60) == "medium"
    assert confidence_level_from_probability(0.84) == "medium"


def test_confidence_level_low_just_below_060():
    assert confidence_level_from_probability(0.599) == "low"


def test_confidence_level_low_at_zero():
    assert confidence_level_from_probability(0.0) == "low"


def test_confidence_level_rejects_out_of_range():
    with pytest.raises(ValueError):
        confidence_level_from_probability(1.5)
    with pytest.raises(ValueError):
        confidence_level_from_probability(-0.1)


# ---------------------------------------------------------------------------
# ExplanationContext validation
# ---------------------------------------------------------------------------


def test_context_accepts_valid_minimal_input():
    context = ExplanationContext(detection_verdict="clean", detection_confidence=0.9)
    assert context.detection_verdict == "clean"


def test_context_rejects_invalid_verdict():
    with pytest.raises(ValueError):
        ExplanationContext(detection_verdict="maybe", detection_confidence=0.9)


def test_context_rejects_out_of_range_confidence():
    with pytest.raises(ValueError):
        ExplanationContext(detection_verdict="clean", detection_confidence=1.5)


# ---------------------------------------------------------------------------
# Explanation.full_text
# ---------------------------------------------------------------------------


def test_full_text_with_no_details_returns_just_summary():
    explanation = Explanation(summary="A summary.", details=[])
    assert explanation.full_text() == "A summary."


def test_full_text_formats_bullets():
    explanation = Explanation(summary="A summary.", details=["First point.", "Second point."])
    text = explanation.full_text()
    assert text.startswith("A summary.")
    assert "- First point." in text
    assert "- Second point." in text


# ---------------------------------------------------------------------------
# RuleBasedExplainer — minimal case
# ---------------------------------------------------------------------------


def test_explainer_clean_case_minimal():
    context = ExplanationContext(detection_verdict="clean", detection_confidence=0.95)
    explanation = RuleBasedExplainer().explain(context)

    assert "CLEAN" in explanation.summary
    assert "95.0%" in explanation.summary
    assert explanation.confidence_level == "high"
    assert len(explanation.details) == 1  # only the detection explanation, nothing else


def test_explainer_adversarial_case_minimal():
    context = ExplanationContext(detection_verdict="adversarial", detection_confidence=0.92)
    explanation = RuleBasedExplainer().explain(context)

    assert "ADVERSARIAL" in explanation.summary
    assert explanation.confidence_level == "high"


# ---------------------------------------------------------------------------
# RuleBasedExplainer — optional sections appear only when data is present
# ---------------------------------------------------------------------------


def test_explainer_omits_attack_type_when_absent():
    context = ExplanationContext(detection_verdict="adversarial", detection_confidence=0.9)
    explanation = RuleBasedExplainer().explain(context)
    assert not any("attack-type classifier" in d.lower() for d in explanation.details)


def test_explainer_includes_attack_type_when_present():
    context = ExplanationContext(
        detection_verdict="adversarial",
        detection_confidence=0.9,
        attack_type="pgd",
        attack_type_confidence=0.71,
    )
    explanation = RuleBasedExplainer().explain(context)
    combined = " ".join(explanation.details)
    assert "PGD" in combined
    assert "71.0%" in combined


def test_explainer_attribution_concentrated_wording():
    context = ExplanationContext(
        detection_verdict="adversarial",
        detection_confidence=0.9,
        attribution_method="gradient_saliency",
        attribution_peak_fraction=0.05,
    )
    explanation = RuleBasedExplainer().explain(context)
    combined = " ".join(explanation.details)
    assert "tightly concentrated" in combined


def test_explainer_attribution_spread_wording():
    context = ExplanationContext(
        detection_verdict="adversarial",
        detection_confidence=0.9,
        attribution_method="gradient_saliency",
        attribution_peak_fraction=0.6,
    )
    explanation = RuleBasedExplainer().explain(context)
    combined = " ".join(explanation.details)
    assert "spread across a large portion" in combined


def test_explainer_flags_reconstruction_that_did_not_improve():
    """Matches the real Module 7 finding: reconstruction SSIM lower than the
    no-reconstruction baseline should be explicitly flagged, not silently reported as if it
    were an improvement."""
    context = ExplanationContext(
        detection_verdict="adversarial",
        detection_confidence=0.9,
        reconstruction_ssim=0.7729,
        reconstruction_psnr=26.08,
        baseline_ssim=0.9912,
    )
    explanation = RuleBasedExplainer().explain(context)
    combined = " ".join(explanation.details)
    assert "did not improve fidelity" in combined


def test_explainer_does_not_flag_reconstruction_that_improved():
    context = ExplanationContext(
        detection_verdict="adversarial",
        detection_confidence=0.9,
        reconstruction_ssim=0.95,
        reconstruction_psnr=35.0,
        baseline_ssim=0.80,
    )
    explanation = RuleBasedExplainer().explain(context)
    combined = " ".join(explanation.details)
    assert "did not improve fidelity" not in combined


def test_explainer_full_pipeline_all_sections_present():
    context = ExplanationContext(
        detection_verdict="adversarial",
        detection_confidence=0.92,
        attack_type="pgd",
        attack_type_confidence=0.71,
        attribution_method="gradient_saliency",
        attribution_peak_fraction=0.28,
        reconstruction_ssim=0.7729,
        reconstruction_psnr=26.08,
        baseline_ssim=0.9912,
    )
    explanation = RuleBasedExplainer().explain(context)
    assert len(explanation.details) == 4  # detection, attack type, attribution, reconstruction
