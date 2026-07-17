"""Explainable AI / reasoning summaries (Module 8).

Public API:
    BaseExplainer                    — abstract interface
    RuleBasedExplainer                — templated, deterministic implementation
    ExplanationContext                — input: bundles Module 5/6/7 outputs, zero heavy deps
    Explanation                        — output: summary + supporting details
    confidence_level_from_probability — "high"/"medium"/"low" categorization

Example:
    >>> from src.xai import ExplanationContext, RuleBasedExplainer
    >>> context = ExplanationContext(
    ...     detection_verdict="adversarial",
    ...     detection_confidence=0.92,
    ...     attack_type="pgd",
    ...     attack_type_confidence=0.71,
    ...     attribution_method="gradient_saliency",
    ...     attribution_peak_fraction=0.28,
    ...     reconstruction_ssim=0.7729,
    ...     reconstruction_psnr=26.08,
    ...     baseline_ssim=0.9912,
    ... )
    >>> print(RuleBasedExplainer().explain(context).full_text())
"""
from .base import BaseExplainer
from .confidence import confidence_level_from_probability
from .context import ExplanationContext
from .explanation import Explanation
from .rule_based_explainer import RuleBasedExplainer

__all__ = [
    "BaseExplainer",
    "RuleBasedExplainer",
    "ExplanationContext",
    "Explanation",
    "confidence_level_from_probability",
]
