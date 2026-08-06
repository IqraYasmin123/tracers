"""Tests for /cases/{id}/reports (Module 14) — real PDF/DOCX files generated into pytest's
own tmp_path (see conftest.py's client fixture), never the real backend/data/ directory."""


def _create_case(client, title="Report test case"):
    response = client.post("/api/v1/cases", json={"title": title, "description": None})
    assert response.status_code == 201
    return response.json()


def _attach_evidence(client, case_id, sample_image_bytes, filename="photo.png"):
    response = client.post(
        f"/api/v1/cases/{case_id}/evidence",
        files={"file": (filename, sample_image_bytes, "image/png")},
    )
    assert response.status_code == 201
    return response.json()


def test_generate_pdf_report_creates_a_real_file(client, sample_image_bytes):
    case = _create_case(client)
    _attach_evidence(client, case["id"], sample_image_bytes)

    response = client.post(f"/api/v1/cases/{case['id']}/reports", json={"format": "pdf"})
    assert response.status_code == 201
    body = response.json()
    assert body["format"] == "pdf"
    assert body["case_id"] == case["id"]
    assert body["file_size_bytes"] > 0


def test_generate_docx_report_creates_a_real_file(client, sample_image_bytes):
    case = _create_case(client)
    _attach_evidence(client, case["id"], sample_image_bytes)

    response = client.post(f"/api/v1/cases/{case['id']}/reports", json={"format": "docx"})
    assert response.status_code == 201
    body = response.json()
    assert body["format"] == "docx"
    assert body["file_size_bytes"] > 0


def test_generate_report_defaults_to_pdf(client, sample_image_bytes):
    case = _create_case(client)
    _attach_evidence(client, case["id"], sample_image_bytes)

    response = client.post(f"/api/v1/cases/{case['id']}/reports", json={})
    assert response.status_code == 201
    assert response.json()["format"] == "pdf"


def test_generate_report_works_for_a_case_with_no_evidence(client):
    case = _create_case(client)
    response = client.post(f"/api/v1/cases/{case['id']}/reports", json={"format": "pdf"})
    assert response.status_code == 201
    assert response.json()["file_size_bytes"] > 0


def test_generate_report_returns_404_for_missing_case(client):
    response = client.post("/api/v1/cases/does-not-exist/reports", json={"format": "pdf"})
    assert response.status_code == 404


def test_list_reports_returns_generated_reports(client, sample_image_bytes):
    case = _create_case(client)
    _attach_evidence(client, case["id"], sample_image_bytes)
    client.post(f"/api/v1/cases/{case['id']}/reports", json={"format": "pdf"})
    client.post(f"/api/v1/cases/{case['id']}/reports", json={"format": "docx"})

    response = client.get(f"/api/v1/cases/{case['id']}/reports")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert {r["format"] for r in body} == {"pdf", "docx"}


def test_list_reports_returns_404_for_missing_case(client):
    response = client.get("/api/v1/cases/does-not-exist/reports")
    assert response.status_code == 404


def test_download_report_returns_the_real_file_bytes(client, sample_image_bytes):
    case = _create_case(client)
    _attach_evidence(client, case["id"], sample_image_bytes)
    created = client.post(f"/api/v1/cases/{case['id']}/reports", json={"format": "pdf"}).json()

    response = client.get(f"/api/v1/cases/{case['id']}/reports/{created['id']}/download")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) == created["file_size_bytes"]
    assert response.content.startswith(b"%PDF")  # a real PDF, not a stub


def test_download_report_returns_404_for_missing_report(client):
    case = _create_case(client)
    response = client.get(f"/api/v1/cases/{case['id']}/reports/does-not-exist/download")
    assert response.status_code == 404


def test_report_embeds_the_real_attribution_heatmap(client, sample_image_bytes):
    """Guards the Module 13 gap this module fixed: attribution_heatmap_path must actually
    be populated and point at a real file, or the report silently omits the image.
    Verified indirectly: a report for a case with evidence (heatmap embedded) must be
    larger than a report for a case with no evidence at all (no image to embed)."""
    case = _create_case(client)
    evidence = _attach_evidence(client, case["id"], sample_image_bytes)
    assert evidence["ai_result"] is not None

    empty_case = _create_case(client, title="Empty case")
    with_evidence_size = client.post(
        f"/api/v1/cases/{case['id']}/reports", json={"format": "pdf"}
    ).json()["file_size_bytes"]
    empty_size = client.post(
        f"/api/v1/cases/{empty_case['id']}/reports", json={"format": "pdf"}
    ).json()["file_size_bytes"]
    assert with_evidence_size > empty_size
