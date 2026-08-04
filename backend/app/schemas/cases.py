"""Request/response schemas for the Case Management endpoints (Module 13)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .. import db as _db  # noqa: F401  (imported first for its sys.path side effect —
# `database` isn't importable until this runs; see app/db.py's docstring)
from database.models import CaseStatus, Verdict


class CaseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class CaseUpdate(BaseModel):
    """All fields optional — a PATCH only changes what's provided."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[CaseStatus] = None


class AIResultSummary(BaseModel):
    verdict: Verdict
    confidence: float
    attack_type: Optional[str] = None
    attack_type_confidence: Optional[float] = None
    attribution_method: str
    attribution_peak_fraction: Optional[float] = None
    explanation_summary: str
    explanation_details: list[str]
    processing_time_ms: float
    created_at: datetime

    model_config = {"from_attributes": True}


class EvidenceSummary(BaseModel):
    id: str
    original_filename: str
    sha256_hash: str
    mime_type: str
    file_size_bytes: int
    uploaded_at: datetime
    ai_result: Optional[AIResultSummary] = None

    model_config = {"from_attributes": True}


class CaseResponse(BaseModel):
    id: str
    case_number: str
    title: str
    description: Optional[str] = None
    status: CaseStatus
    created_at: datetime
    updated_at: datetime
    evidence_count: int

    model_config = {"from_attributes": True}


class CaseDetailResponse(CaseResponse):
    evidence: list[EvidenceSummary] = []


class CaseStatsResponse(BaseModel):
    """Backs the Analytics page's 'Case Statistics' panel and Dashboard's summary cards."""

    total_cases: int
    open_cases: int
    in_progress_cases: int
    closed_cases: int
    archived_cases: int

    # Evidence-level aggregates, across every case in the database — distinct from
    # Analytics' live session stats, which are scoped to one browser's localStorage.
    total_evidence: int
    clean_verdicts: int
    adversarial_verdicts: int
    avg_confidence: Optional[float] = None
