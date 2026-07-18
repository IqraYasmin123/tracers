"""Image upload + AI inference endpoint."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ...config import settings
from ...dependencies import get_pipeline_service
from ...schemas.inference import AnalysisResponse
from ...services.pipeline_service import TracerPipelineService

router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_image(
    file: UploadFile = File(..., description="Image to analyze"),
    caption: Optional[str] = Form(
        default=None, description="Expected caption/label — improves attribution accuracy"
    ),
    pipeline: TracerPipelineService = Depends(get_pipeline_service),
) -> AnalysisResponse:
    """Detect whether an image shows signs of adversarial manipulation, localize where via
    a forensic heatmap, and generate a human-readable explanation.

    Does NOT run reconstruction — that stays a Colab-only capability for now (multi-GB model,
    30-60s per image; a production deployment would run it via a background job queue rather
    than blocking this request). See docs/module9_backend.md.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {sorted(ALLOWED_CONTENT_TYPES)}",
        )

    image_bytes = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {settings.max_upload_size_mb}MB upload limit.",
        )

    result = pipeline.analyze(image_bytes, caption=caption)
    return AnalysisResponse(**result)
