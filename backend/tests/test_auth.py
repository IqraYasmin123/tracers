"""Tests for /auth endpoints (Module 16). Uses a fresh, unauthenticated TestClient per test
(not the `client` fixture, which pre-authenticates as an admin — auth flows need to control
their own tokens from scratch)."""
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token, hash_password
from app.db import get_db
from app.dependencies import get_pipeline_service
from app.main import app
from database.models import Base, User, UserRole


class FakePipelineService:
    """Returns a canned, realistic-looking result instantly. Duplicated from conftest.py
    rather than imported cross-file — pytest's import mode for a `tests/` dir without an
    `__init__.py` makes `from tests.conftest import ...` fragile/environment-dependent."""

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


def _fresh_db_and_client(monkeypatch, config_module, tmp_path):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(config_module.settings, "evidence_storage_dir", str(tmp_path / "evidence"))
    monkeypatch.setattr(config_module.settings, "report_storage_dir", str(tmp_path / "reports"))
    app.dependency_overrides[get_pipeline_service] = lambda: FakePipelineService()
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client, SessionLocal


def _create_user(SessionLocal, username="alice", email="alice@example.com", password="correcthorse", role=UserRole.INVESTIGATOR):
    db = SessionLocal()
    try:
        user = User(username=username, email=email, password_hash=hash_password(password), role=role)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def test_login_with_correct_username_and_password_returns_a_token(monkeypatch, tmp_path):
    import app.config as config_module

    client, SessionLocal = _fresh_db_and_client(monkeypatch, config_module, tmp_path)
    _create_user(SessionLocal, username="alice", password="correcthorse")

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "alice", "password": "correcthorse"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20
    app.dependency_overrides.clear()


def test_login_accepts_email_in_the_username_field(monkeypatch, tmp_path):
    import app.config as config_module

    client, SessionLocal = _fresh_db_and_client(monkeypatch, config_module, tmp_path)
    _create_user(SessionLocal, username="alice", email="alice@example.com", password="correcthorse")

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "alice@example.com", "password": "correcthorse"},
    )
    assert response.status_code == 200
    app.dependency_overrides.clear()


def test_login_with_wrong_password_returns_401_with_generic_message(monkeypatch, tmp_path):
    import app.config as config_module

    client, SessionLocal = _fresh_db_and_client(monkeypatch, config_module, tmp_path)
    _create_user(SessionLocal, username="alice", password="correcthorse")

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "alice", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password."
    app.dependency_overrides.clear()


def test_login_with_nonexistent_username_returns_the_same_generic_message(monkeypatch, tmp_path):
    """Same error either way — a different message would let an attacker enumerate
    valid usernames."""
    import app.config as config_module

    client, _ = _fresh_db_and_client(monkeypatch, config_module, tmp_path)

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "nobody", "password": "whatever"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password."
    app.dependency_overrides.clear()


def test_protected_route_returns_401_with_no_token(monkeypatch, tmp_path):
    import app.config as config_module

    client, _ = _fresh_db_and_client(monkeypatch, config_module, tmp_path)
    response = client.get("/api/v1/cases")
    assert response.status_code == 401
    app.dependency_overrides.clear()


def test_get_me_returns_the_authenticated_user(monkeypatch, tmp_path):
    import app.config as config_module

    client, SessionLocal = _fresh_db_and_client(monkeypatch, config_module, tmp_path)
    user = _create_user(SessionLocal, username="alice", role=UserRole.INVESTIGATOR)
    token = create_access_token(user_id=user.id, username=user.username, role=user.role.value)

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "alice"
    assert body["role"] == "investigator"
    app.dependency_overrides.clear()


def test_viewer_cannot_create_a_case(monkeypatch, tmp_path):
    import app.config as config_module

    client, SessionLocal = _fresh_db_and_client(monkeypatch, config_module, tmp_path)
    viewer = _create_user(SessionLocal, username="viewer1", role=UserRole.VIEWER)
    token = create_access_token(user_id=viewer.id, username=viewer.username, role=viewer.role.value)

    response = client.post(
        "/api/v1/cases",
        json={"title": "Should be blocked"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    app.dependency_overrides.clear()


def test_viewer_can_read_cases(monkeypatch, tmp_path):
    import app.config as config_module

    client, SessionLocal = _fresh_db_and_client(monkeypatch, config_module, tmp_path)
    viewer = _create_user(SessionLocal, username="viewer1", role=UserRole.VIEWER)
    token = create_access_token(user_id=viewer.id, username=viewer.username, role=viewer.role.value)

    response = client.get("/api/v1/cases", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    app.dependency_overrides.clear()


def test_investigator_can_create_a_case(monkeypatch, tmp_path):
    import app.config as config_module

    client, SessionLocal = _fresh_db_and_client(monkeypatch, config_module, tmp_path)
    investigator = _create_user(SessionLocal, username="inv1", role=UserRole.INVESTIGATOR)
    token = create_access_token(
        user_id=investigator.id, username=investigator.username, role=investigator.role.value
    )

    response = client.post(
        "/api/v1/cases",
        json={"title": "A real case"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    app.dependency_overrides.clear()


def test_only_admin_can_create_users(monkeypatch, tmp_path):
    import app.config as config_module

    client, SessionLocal = _fresh_db_and_client(monkeypatch, config_module, tmp_path)
    investigator = _create_user(SessionLocal, username="inv1", role=UserRole.INVESTIGATOR)
    token = create_access_token(
        user_id=investigator.id, username=investigator.username, role=investigator.role.value
    )

    response = client.post(
        "/api/v1/auth/users",
        json={"username": "newperson", "email": "new@example.com", "password": "longenoughpass"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    app.dependency_overrides.clear()


def test_admin_can_create_a_new_user(monkeypatch, tmp_path):
    import app.config as config_module

    client, SessionLocal = _fresh_db_and_client(monkeypatch, config_module, tmp_path)
    admin = _create_user(SessionLocal, username="admin1", role=UserRole.ADMIN)
    token = create_access_token(user_id=admin.id, username=admin.username, role=admin.role.value)

    response = client.post(
        "/api/v1/auth/users",
        json={"username": "newperson", "email": "new@example.com", "password": "longenoughpass", "role": "viewer"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "newperson"
    assert body["role"] == "viewer"
    app.dependency_overrides.clear()


def test_cannot_create_a_duplicate_username(monkeypatch, tmp_path):
    import app.config as config_module

    client, SessionLocal = _fresh_db_and_client(monkeypatch, config_module, tmp_path)
    admin = _create_user(SessionLocal, username="admin1", role=UserRole.ADMIN)
    _create_user(SessionLocal, username="existing", email="existing@example.com")
    token = create_access_token(user_id=admin.id, username=admin.username, role=admin.role.value)

    response = client.post(
        "/api/v1/auth/users",
        json={"username": "existing", "email": "different@example.com", "password": "longenoughpass"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409
    app.dependency_overrides.clear()


def test_change_own_password_requires_correct_current_password(monkeypatch, tmp_path):
    import app.config as config_module

    client, SessionLocal = _fresh_db_and_client(monkeypatch, config_module, tmp_path)
    user = _create_user(SessionLocal, username="alice", password="oldpassword")
    token = create_access_token(user_id=user.id, username=user.username, role=user.role.value)

    response = client.patch(
        "/api/v1/auth/me/password",
        json={"current_password": "wrongoldpassword", "new_password": "brandnewpassword"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    app.dependency_overrides.clear()


def test_change_own_password_succeeds_and_new_password_works(monkeypatch, tmp_path):
    import app.config as config_module

    client, SessionLocal = _fresh_db_and_client(monkeypatch, config_module, tmp_path)
    user = _create_user(SessionLocal, username="alice", password="oldpassword")
    token = create_access_token(user_id=user.id, username=user.username, role=user.role.value)

    response = client.patch(
        "/api/v1/auth/me/password",
        json={"current_password": "oldpassword", "new_password": "brandnewpassword"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "alice", "password": "brandnewpassword"},
    )
    assert login_response.status_code == 200
    app.dependency_overrides.clear()
