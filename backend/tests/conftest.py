"""Shared pytest fixtures.

The key pattern here: `FakePipelineService` stands in for `TracerPipelineService` via
`app.dependency_overrides`, so every test in this file runs without touching torch, CLIP, or
any heavy model at all — the same dependency-injection testing strategy used throughout the
AI engine (Modules 4-7), now applied at the API layer.
"""
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.dependencies import get_pipeline_service
from app.main import app


class FakePipelineService:
    """Returns a canned, realistic-looking result instantly."""

    def analyze(self, image_bytes: bytes, caption=None) -> dict:
        return {
            "verdict": "adversarial",
            "confidence": 0.92,
            "attack_type": "pgd",
            "attack_type_confidence": 0.71,
            "attribution_method": "gradient_saliency",
            "attribution_heatmap_png_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
            "attribution_peak_fraction": 0.28,
            "explanation_summary": "This image was classified as ADVERSARIAL with 92.0% confidence (high confidence).",
            "explanation_details": ["A supporting detail sentence."],
            "sha256_hash": "deadbeef" * 8,
            "processing_time_ms": 123.4,
        }


class FailingPipelineService:
    """Simulates the AI engine not being ready (e.g. no trained detector present)."""

    def analyze(self, image_bytes: bytes, caption=None) -> dict:
        raise RuntimeError("No trained detector available.")


@pytest.fixture
def client():
    app.dependency_overrides[get_pipeline_service] = lambda: FakePipelineService()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def failing_client():
    app.dependency_overrides[get_pipeline_service] = lambda: FailingPipelineService()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_image_bytes() -> bytes:
    image = Image.new("RGB", (32, 32), color=(100, 150, 200))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
