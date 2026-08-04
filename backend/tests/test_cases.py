"""Tests for the /cases endpoints (Module 13) — all using FakePipelineService and a fresh
in-memory SQLite database per test, no real AI models or persistent state."""
import pytest


def _create_case(client, title="Suspicious upload investigation", description=None):
    response = client.post(
        "/api/v1/cases",
        json={"title": title, "description": description},
    )
    assert response.status_code == 201
    return response.json()


def test_create_case_returns_expected_fields(client):
    body = _create_case(client, title="First case", description="Some notes")

    assert body["title"] == "First case"
    assert body["description"] == "Some notes"
    assert body["status"] == "open"
    assert body["case_number"].startswith("CASE-")
    assert body["evidence_count"] == 0
    assert "id" in body and "created_at" in body


def test_create_case_without_description(client):
    body = _create_case(client, title="No description case", description=None)
    assert body["description"] is None


def test_create_case_generates_unique_case_numbers(client):
    first = _create_case(client, title="Case A")
    second = _create_case(client, title="Case B")
    assert first["case_number"] != second["case_number"]


def test_list_cases_returns_created_cases(client):
    _create_case(client, title="Case one")
    _create_case(client, title="Case two")

    response = client.get("/api/v1/cases")
    assert response.status_code == 200
    titles = {case["title"] for case in response.json()}
    assert titles == {"Case one", "Case two"}


def test_list_cases_filters_by_status(client):
    case = _create_case(client, title="Will be closed")
    _create_case(client, title="Stays open")

    client.patch(f"/api/v1/cases/{case['id']}", json={"status": "closed"})

    response = client.get("/api/v1/cases", params={"status": "closed"})
    assert response.status_code == 200
    titles = {c["title"] for c in response.json()}
    assert titles == {"Will be closed"}


def test_get_case_detail_returns_404_for_missing_case(client):
    response = client.get("/api/v1/cases/does-not-exist")
    assert response.status_code == 404


def test_get_case_detail_includes_empty_evidence_list(client):
    case = _create_case(client)
    response = client.get(f"/api/v1/cases/{case['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["evidence"] == []
    assert body["evidence_count"] == 0


def test_update_case_partial_update(client):
    case = _create_case(client, title="Original title")

    response = client.patch(
        f"/api/v1/cases/{case['id']}",
        json={"status": "in_progress"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "in_progress"
    assert body["title"] == "Original title"  # untouched field stays as-is


def test_update_case_returns_404_for_missing_case(client):
    response = client.patch("/api/v1/cases/does-not-exist", json={"status": "closed"})
    assert response.status_code == 404


def test_attach_evidence_creates_evidence_and_ai_result(client, sample_image_bytes):
    case = _create_case(client)

    response = client.post(
        f"/api/v1/cases/{case['id']}/evidence",
        files={"file": ("photo.png", sample_image_bytes, "image/png")},
        data={"caption": "a test caption"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["original_filename"] == "photo.png"
    assert body["ai_result"]["verdict"] == "adversarial"
    assert body["ai_result"]["confidence"] == 0.92
    assert body["ai_result"]["attack_type"] == "pgd"

    # The case's evidence_count and detail view should now reflect this attachment.
    detail = client.get(f"/api/v1/cases/{case['id']}").json()
    assert detail["evidence_count"] == 1
    assert detail["evidence"][0]["ai_result"]["verdict"] == "adversarial"


def test_attach_evidence_returns_404_for_missing_case(client, sample_image_bytes):
    response = client.post(
        "/api/v1/cases/does-not-exist/evidence",
        files={"file": ("photo.png", sample_image_bytes, "image/png")},
    )
    assert response.status_code == 404


def test_attach_evidence_rejects_unsupported_file_type(client):
    case = _create_case(client)
    response = client.post(
        f"/api/v1/cases/{case['id']}/evidence",
        files={"file": ("notes.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 422


def test_attach_evidence_returns_503_when_pipeline_not_ready(failing_client, sample_image_bytes):
    case = _create_case(failing_client)
    response = failing_client.post(
        f"/api/v1/cases/{case['id']}/evidence",
        files={"file": ("photo.png", sample_image_bytes, "image/png")},
    )
    assert response.status_code == 503


def test_case_stats_reflects_created_cases(client):
    a = _create_case(client, title="A")
    _create_case(client, title="B")
    client.patch(f"/api/v1/cases/{a['id']}", json={"status": "closed"})

    response = client.get("/api/v1/cases/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["total_cases"] == 2
    assert body["closed_cases"] == 1
    assert body["open_cases"] == 1


def test_case_stats_with_no_cases(client):
    response = client.get("/api/v1/cases/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["total_cases"] == 0
    assert body["open_cases"] == 0
    assert body["total_evidence"] == 0
    assert body["avg_confidence"] is None


def test_case_stats_reflects_attached_evidence(client, sample_image_bytes):
    case = _create_case(client)
    client.post(
        f"/api/v1/cases/{case['id']}/evidence",
        files={"file": ("photo.png", sample_image_bytes, "image/png")},
    )

    response = client.get("/api/v1/cases/stats")
    body = response.json()
    assert body["total_evidence"] == 1
    assert body["adversarial_verdicts"] == 1  # FakePipelineService always returns adversarial
    assert body["clean_verdicts"] == 0
    assert body["avg_confidence"] == pytest.approx(0.92)
