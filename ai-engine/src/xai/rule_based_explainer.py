"""
Rule-based (templated) natural-language explainer.

Deliberately not LLM-backed — see docs/module8_xai.md for the full rationale. In short:
deterministic, fully unit-testable with plain assertions, no external API dependency or cost,
and keeps the AI engine self-contained.
"""
from __future__ import annotations

from .base import BaseExplainer
from .confidence import confidence_level_from_probability
from .context import ExplanationContext
from .explanation import Explanation


class RuleBasedExplainer(BaseExplainer):
    """Generates a structured explanation from an ExplanationContext using fixed templates."""

    def explain(self, context: ExplanationContext) -> Explanation:
        confidence_level = confidence_level_from_probability(context.detection_confidence)
        verdict_label = context.detection_verdict.upper()

        summary = (
            f"This image was classified as {verdict_label} with "
            f"{context.detection_confidence:.1%} confidence ({confidence_level} confidence)."
        )

        details = [self._explain_detection(context)]

        if context.attack_type is not None:
            details.append(self._explain_attack_type(context))

        if context.attribution_method is not None:
            details.append(self._explain_attribution(context))

        if context.reconstruction_ssim is not None:
            details.append(self._explain_reconstruction(context))

        return Explanation(summary=summary, details=details, confidence_level=confidence_level)

    @staticmethod
    def _explain_detection(context: ExplanationContext) -> str:
        if context.detection_verdict == "adversarial":
            return (
                "This verdict is based on attention-entropy anomaly scoring: the pattern of "
                "how the vision transformer distributed attention across image patches "
                "deviated from what the detector learned to expect from clean images."
            )
        return (
            "This verdict is based on attention-entropy anomaly scoring: the attention "
            "pattern closely matched what the detector learned to expect from clean, "
            "unmanipulated images."
        )

    @staticmethod
    def _explain_attack_type(context: ExplanationContext) -> str:
        confidence_str = (
            f"{context.attack_type_confidence:.1%}"
            if context.attack_type_confidence is not None
            else "an unspecified"
        )
        return (
            f"The attack-type classifier identified this as most consistent with a "
            f"{context.attack_type.upper()} attack ({confidence_str} confidence)."
        )

    @staticmethod
    def _explain_attribution(context: ExplanationContext) -> str:
        if context.attribution_peak_fraction is None:
            return f"Attribution was generated using {context.attribution_method}."

        fraction = context.attribution_peak_fraction
        if fraction < 0.15:
            spread = "tightly concentrated in a small region"
        elif fraction < 0.40:
            spread = "moderately concentrated"
        else:
            spread = "spread across a large portion of the image"

        return (
            f"Attribution ({context.attribution_method}) shows the most forensically "
            f"significant pixels are {spread} ({fraction:.1%} of the image above threshold)."
        )

    @staticmethod
    def _explain_reconstruction(context: ExplanationContext) -> str:
        base = (
            f"Reconstruction achieved SSIM {context.reconstruction_ssim:.4f} vs. the clean "
            f"original"
        )
        if context.reconstruction_psnr is not None:
            base += f", PSNR {context.reconstruction_psnr:.2f} dB"

        if (
            context.baseline_ssim is not None
            and context.reconstruction_ssim < context.baseline_ssim
        ):
            return (
                f"{base}. This is lower than the {context.baseline_ssim:.4f} SSIM of the "
                f"unreconstructed image, suggesting reconstruction did not improve fidelity "
                f"for this image — a known limitation for near-imperceptible perturbations "
                f"(see docs/module7_reconstruction.md)."
            )
        return f"{base}."
