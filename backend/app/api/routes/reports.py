"""Report generation endpoints (Module 14).

Reports are generated from the same Case/Evidence/AIResult rows Module 13 persists — see
app/services/report_service.py's docstring. No AI inference happens here; this is purely
a formatting/export step over data that was already honestly computed.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from ... import db as _db  # noqa: F401  (imported first for its sys.path side effect —
# `database` isn't importable until this runs; see app/db.py's docstring)
from database.models import Case, Evidence, Report, ReportFormat

from ...config import settings
from ...db import get_db
from ...schemas.reports import ReportCreate, ReportResponse
from ...services.report_service import generate_docx_report, generate_pdf_report
from ...services.system_user import get_or_create_system_user

router = APIRouter()

_CONTENT_TYPES = {
    ReportFormat.PDF: "application/pdf",
    ReportFormat.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _to_report_response(report: Report) -> ReportResponse:
    size = Path(report.file_path).stat().st_size if Path(report.file_path).exists() else 0
    return ReportResponse.model_validate(
        {
            "id": report.id,
            "case_id": report.case_id,
            "format": report.format,
            "file_size_bytes": size,
            "created_at": report.created_at,
        }
    )


def _load_case_with_evidence(db: Session, case_id: str) -> Case:
    case = (
        db.query(Case)
        .options(joinedload(Case.evidence).joinedload(Evidence.ai_result))
        .filter(Case.id == case_id)
        .first()
    )
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return case


@router.post("/cases/{case_id}/reports", response_model=ReportResponse, status_code=201)
def create_report(
    case_id: str, payload: ReportCreate, db: Session = Depends(get_db)
) -> ReportResponse:
    case = _load_case_with_evidence(db, case_id)
    system_user = get_or_create_system_user(db)

    report_id = uuid.uuid4().hex
    extension = "pdf" if payload.format == ReportFormat.PDF else "docx"
    output_path = Path(settings.report_storage_dir) / case.id / f"{report_id}.{extension}"

    if payload.format == ReportFormat.PDF:
        generate_pdf_report(case, output_path)
    else:
        generate_docx_report(case, output_path)

    report = Report(
        case_id=case.id,
        generated_by=system_user.id,
        file_path=str(output_path),
        format=payload.format,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return _to_report_response(report)


@router.get("/cases/{case_id}/reports", response_model=list[ReportResponse])
def list_reports(case_id: str, db: Session = Depends(get_db)) -> list[ReportResponse]:
    _load_case_with_evidence(db, case_id)  # 404s if the case doesn't exist
    reports = (
        db.query(Report)
        .filter(Report.case_id == case_id)
        .order_by(Report.created_at.desc())
        .all()
    )
    return [_to_report_response(r) for r in reports]


@router.get("/cases/{case_id}/reports/{report_id}/download")
def download_report(case_id: str, report_id: str, db: Session = Depends(get_db)) -> FileResponse:
    report = (
        db.query(Report).filter(Report.id == report_id, Report.case_id == case_id).first()
    )
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")

    file_path = Path(report.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=410,
            detail="The report file is no longer available on disk.",
        )

    extension = "pdf" if report.format == ReportFormat.PDF else "docx"
    return FileResponse(
        path=str(file_path),
        media_type=_CONTENT_TYPES[report.format],
        filename=f"{case_id}_report.{extension}",
    )
