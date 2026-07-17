"""
ExplanationContext — the input to every explainer.

Deliberately a plain dataclass with no dependency on src.vlm/attacks/detection/attribution/
reconstruction. This module only ever sees already-computed numbers and strings; whoever
calls it (the notebook, later the FastAPI backend) is responsible for actually running the
pipeline and populating this context. This keeps XAI the cleanest-dependency module in the
project — it can be fully tested and reasoned about without touching CLIP, PyTorch, or any
heavy model at all.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ExplanationContext:
    """Everything an explainer needs to describe one image's forensic analysis.

    Only `detection_verdict` and `detection_confidence` are required — every other field is
    optional, since not every analysis will have run attack-type classification, attribution,
    or reconstruction (e.g. a clean image correctly identified as clean has no need for a
    reconstruction step).
    """

    detection_verdict: str  # "clean" or "adversarial"
    detection_confidence: float  # probability of the predicted class, in [0,1]

    attack_type: str | None = None  # e.g. "fgsm", "pgd"
    attack_type_confidence: float | None = None

    attribution_method: str | None = None  # e.g. "gradient_saliency", "attention_layer_-1"
    attribution_peak_fraction: float | None = None  # fraction of heatmap above threshold

    reconstruction_ssim: float | None = None
    reconstruction_psnr: float | None = None
    baseline_ssim: float | None = None  # adversarial-vs-clean SSIM without reconstruction

    def __post_init__(self) -> None:
        if self.detection_verdict not in ("clean", "adversarial"):
            raise ValueError(
                f"detection_verdict must be 'clean' or 'adversarial', got "
                f"'{self.detection_verdict}'"
            )
        if not (0.0 <= self.detection_confidence <= 1.0):
            raise ValueError(
                f"detection_confidence must be in [0,1], got {self.detection_confidence}"
            )
