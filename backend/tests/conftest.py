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
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.config as config_module
from app.auth.security import create_access_token, hash_password
from app.db import get_db
from app.dependencies import get_pipeline_service
from app.main import app
from database.models import Base, User, UserRole


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
def test_db_session():
    """A fresh in-memory SQLite database per test. StaticPool keeps the same connection
    alive across the multiple get_db() calls one request can trigger (FastAPI's TestClient
    otherwise opens a new, empty in-memory database per connection)."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    yield override_get_db


def _make_authenticated_test_client(app_instance, get_db_override) -> TestClient:
    """Creates a real ADMIN user directly in the test database and returns a TestClient
    that sends its token on every request by default (as `Authorization: Bearer ...`).

    Module 16 requires auth on every case/report route — tests written before Module 16
    existed call these endpoints with no token at all. Rather than rewrite every one of
    those tests individually, every request through this client is pre-authenticated as an
    admin (the highest-privilege role, so no existing test's assumed permissions change).
    Tests that specifically need to exercise 401/403/role behavior override this per-request
    (e.g. `client.get(url, headers={})` for "no token", or build their own lower-privilege
    token via `create_access_token` directly)."""
    db_gen = get_db_override()
    db = next(db_gen)
    try:
        user = User(
            username="test-admin",
            email="test-admin@tracer.local",
            password_hash=hash_password("not-used-directly-in-tests"),
            role=UserRole.ADMIN,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token(user_id=user.id, username=user.username, role=user.role.value)
    finally:
        db.close()

    test_client = TestClient(app_instance)
    test_client.headers.update({"Authorization": f"Bearer {token}"})
    return test_client


@pytest.fixture
def client(test_db_session, tmp_path, monkeypatch):
    # Isolate file storage to pytest's own tmp dir — otherwise every test run writes real
    # files into backend/data/, which is gitignored but still pollutes the working copy.
    monkeypatch.setattr(config_module.settings, "evidence_storage_dir", str(tmp_path / "evidence"))
    monkeypatch.setattr(config_module.settings, "report_storage_dir", str(tmp_path / "reports"))
    app.dependency_overrides[get_pipeline_service] = lambda: FakePipelineService()
    app.dependency_overrides[get_db] = test_db_session
    with _make_authenticated_test_client(app, test_db_session) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def failing_client(test_db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(config_module.settings, "evidence_storage_dir", str(tmp_path / "evidence"))
    monkeypatch.setattr(config_module.settings, "report_storage_dir", str(tmp_path / "reports"))
    app.dependency_overrides[get_pipeline_service] = lambda: FailingPipelineService()
    app.dependency_overrides[get_db] = test_db_session
    with _make_authenticated_test_client(app, test_db_session) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_image_bytes() -> bytes:
    image = Image.new("RGB", (32, 32), color=(100, 150, 200))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
