"""Request/response schemas for the inference endpoint."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class AnalysisResponse(BaseModel):
    """Everything the frontend investigation page needs to render one image's analysis."""

    verdict: str = Field(..., description="'clean' or 'adversarial'")
    confidence: float = Field(..., description="Probability of the predicted verdict, in [0,1]")

    attack_type: Optional[str] = Field(
        None, description="e.g. 'fgsm' or 'pgd', if an attack-type classifier is available"
    )
    attack_type_confidence: Optional[float] = None

    attribution_method: str
    attribution_heatmap_png_base64: str = Field(
        ..., description="Base64-encoded PNG of the forensic attribution heatmap overlay"
    )
    attribution_peak_fraction: float

    explanation_summary: str
    explanation_details: list[str]

    sha256_hash: str = Field(..., description="SHA-256 of the uploaded image bytes — evidence integrity hash")
    processing_time_ms: float


class ErrorResponse(BaseModel):
    detail: str
