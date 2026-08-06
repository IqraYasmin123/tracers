"""Case Management endpoints (Module 13).

Route order matters here: `/cases/stats` is registered before `/cases/{case_id}` so FastAPI
doesn't try to parse the literal string "stats" as a case_id path parameter.
"""
from __future__ import annotations

import base64
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ... import db as _db  # noqa: F401  (imported first for its sys.path side effect —
# `database` isn't importable until this runs; see app/db.py's docstring)
from database.models import AIResult, Case, CaseStatus, Evidence, Verdict

from ...config import settings
from ...db import get_db
from ...dependencies import get_pipeline_service
from ...schemas.cases import (
    CaseCreate,
    CaseDetailResponse,
    CaseResponse,
    CaseStatsResponse,
    CaseUpdate,
    EvidenceSummary,
)
from ...services.pipeline_service import TracerPipelineService
from ...services.system_user import get_or_create_system_user

router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _to_case_response(case: Case) -> CaseResponse:
    return CaseResponse.model_validate(
        {
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
            "description": case.description,
            "status": case.status,
            "created_at": case.created_at,
            "updated_at": case.updated_at,
            "evidence_count": len(case.evidence),
        }
    )


@router.get("/cases/stats", response_model=CaseStatsResponse)
def get_case_stats(db: Session = Depends(get_db)) -> CaseStatsResponse:
    rows = db.query(Case.status, func.count(Case.id)).group_by(Case.status).all()
    counts = {status.value: 0 for status in CaseStatus}
    for status, count in rows:
        counts[status.value if hasattr(status, "value") else status] = count

    verdict_rows = db.query(AIResult.verdict, func.count(AIResult.id)).group_by(AIResult.verdict).all()
    verdict_counts = {verdict.value: 0 for verdict in Verdict}
    for verdict, count in verdict_rows:
        verdict_counts[verdict.value if hasattr(verdict, "value") else verdict] = count

    avg_confidence = db.query(func.avg(AIResult.confidence)).scalar()

    return CaseStatsResponse(
        total_cases=sum(counts.values()),
        open_cases=counts[CaseStatus.OPEN.value],
        in_progress_cases=counts[CaseStatus.IN_PROGRESS.value],
        closed_cases=counts[CaseStatus.CLOSED.value],
        archived_cases=counts[CaseStatus.ARCHIVED.value],
        total_evidence=sum(verdict_counts.values()),
        clean_verdicts=verdict_counts[Verdict.CLEAN.value],
        adversarial_verdicts=verdict_counts[Verdict.ADVERSARIAL.value],
        avg_confidence=float(avg_confidence) if avg_confidence is not None else None,
    )


@router.post("/cases", response_model=CaseResponse, status_code=201)
def create_case(payload: CaseCreate, db: Session = Depends(get_db)) -> CaseResponse:
    system_user = get_or_create_system_user(db)

    case = Case(
        case_number=f"CASE-{uuid.uuid4().hex[:8].upper()}",
        title=payload.title,
        description=payload.description,
        status=CaseStatus.OPEN,
        created_by=system_user.id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return _to_case_response(case)


@router.get("/cases", response_model=list[CaseResponse])
def list_cases(
    status: Optional[CaseStatus] = Query(None, description="Filter by case status"),
    db: Session = Depends(get_db),
) -> list[CaseResponse]:
    query = db.query(Case).options(joinedload(Case.evidence))
    if status is not None:
        query = query.filter(Case.status == status)
    cases = query.order_by(Case.created_at.desc()).all()
    return [_to_case_response(case) for case in cases]


@router.get("/cases/{case_id}", response_model=CaseDetailResponse)
def get_case(case_id: str, db: Session = Depends(get_db)) -> CaseDetailResponse:
    case = (
        db.query(Case)
        .options(joinedload(Case.evidence).joinedload(Evidence.ai_result))
        .filter(Case.id == case_id)
        .first()
    )
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    evidence_sorted = sorted(case.evidence, key=lambda e: e.uploaded_at, reverse=True)
    return CaseDetailResponse.model_validate(
        {
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
            "description": case.description,
            "status": case.status,
            "created_at": case.created_at,
            "updated_at": case.updated_at,
            "evidence_count": len(case.evidence),
            "evidence": evidence_sorted,
        }
    )


@router.patch("/cases/{case_id}", response_model=CaseResponse)
def update_case(case_id: str, payload: CaseUpdate, db: Session = Depends(get_db)) -> CaseResponse:
    case = db.query(Case).options(joinedload(Case.evidence)).filter(Case.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(case, field, value)

    db.commit()
    db.refresh(case)
    return _to_case_response(case)


@router.post("/cases/{case_id}/evidence", response_model=EvidenceSummary, status_code=201)
async def attach_evidence(
    case_id: str,
    file: UploadFile = File(..., description="Image to analyze and attach as evidence"),
    caption: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
    pipeline: TracerPipelineService = Depends(get_pipeline_service),
) -> EvidenceSummary:
    """Runs the real AI pipeline server-side and persists both the evidence file and its
    AI result — the verdict is always computed here, never accepted from the client, so a
    case's forensic record can't be tampered with by a client sending arbitrary results."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

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

    system_user = get_or_create_system_user(db)

    case_dir = Path(settings.evidence_storage_dir) / case.id
    case_dir.mkdir(parents=True, exist_ok=True)
    original_name = file.filename or "upload"
    suffix = Path(original_name).suffix or ".bin"
    stored_filename = f"{uuid.uuid4().hex}{suffix}"
    storage_path = case_dir / stored_filename
    storage_path.write_bytes(image_bytes)

    # Persist the attribution heatmap too (previously only returned to the client and
    # discarded — a real gap, since Module 14's reports need the actual image, not just
    # the attribution_method/peak_fraction numbers).
    heatmap_path = None
    heatmap_b64 = result.get("attribution_heatmap_png_base64")
    if heatmap_b64:
        heatmap_filename = f"{uuid.uuid4().hex}_heatmap.png"
        heatmap_full_path = case_dir / heatmap_filename
        heatmap_full_path.write_bytes(base64.b64decode(heatmap_b64))
        heatmap_path = str(heatmap_full_path)

    evidence = Evidence(
        case_id=case.id,
        original_filename=original_name,
        storage_path=str(storage_path),
        sha256_hash=result["sha256_hash"],
        mime_type=file.content_type,
        file_size_bytes=len(image_bytes),
        uploaded_by=system_user.id,
    )
    db.add(evidence)
    db.flush()  # assigns evidence.id without ending the transaction

    ai_result = AIResult(
        evidence_id=evidence.id,
        verdict=Verdict(result["verdict"]),
        confidence=result["confidence"],
        attack_type=result["attack_type"],
        attack_type_confidence=result["attack_type_confidence"],
        attribution_method=result["attribution_method"],
        attribution_heatmap_path=heatmap_path,
        attribution_peak_fraction=result["attribution_peak_fraction"],
        explanation_summary=result["explanation_summary"],
        explanation_details=result["explanation_details"],
        processing_time_ms=result["processing_time_ms"],
    )
    db.add(ai_result)
    db.commit()
    db.refresh(evidence)

    return EvidenceSummary.model_validate(evidence)
