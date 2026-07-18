"""Tests for the /analyze endpoint — all using the FakePipelineService, no real AI models."""
import app.config as config_module


def test_analyze_returns_expected_fields(client, sample_image_bytes):
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("test.png", sample_image_bytes, "image/png")},
        data={"caption": "a test caption"},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["verdict"] == "adversarial"
    assert body["confidence"] == 0.92
    assert body["attack_type"] == "pgd"
    assert body["attribution_method"] == "gradient_saliency"
    assert "sha256_hash" in body
    assert "processing_time_ms" in body
    assert "explanation_summary" in body
    assert isinstance(body["explanation_details"], list)


def test_analyze_works_without_caption(client, sample_image_bytes):
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("test.png", sample_image_bytes, "image/png")},
    )
    assert response.status_code == 200


def test_analyze_rejects_unsupported_file_type(client):
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("test.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 422
    assert "Unsupported file type" in response.json()["detail"]


def test_analyze_rejects_oversized_file(client, sample_image_bytes, monkeypatch):
    monkeypatch.setattr(config_module.settings, "max_upload_size_mb", 0)
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("test.png", sample_image_bytes, "image/png")},
    )
    assert response.status_code == 413


def test_analyze_returns_503_when_pipeline_not_ready(failing_client, sample_image_bytes):
    response = failing_client.post(
        "/api/v1/analyze",
        files={"file": ("test.png", sample_image_bytes, "image/png")},
    )
    assert response.status_code == 503
    assert "No trained detector" in response.json()["detail"]


def test_analyze_requires_file():
    """Missing the required file entirely should be a 422 from FastAPI's own validation,
    before our code even runs — doesn't need the client fixture since no dependency
    override matters here."""
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        response = c.post("/api/v1/analyze")
    assert response.status_code == 422
