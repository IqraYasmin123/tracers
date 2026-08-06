"""Request/response schemas for report generation (Module 14)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from .. import db as _db  # noqa: F401  (imported first for its sys.path side effect —
# `database` isn't importable until this runs; see app/db.py's docstring)
from database.models import ReportFormat


class ReportCreate(BaseModel):
    format: ReportFormat = ReportFormat.PDF


class ReportResponse(BaseModel):
    id: str
    case_id: str
    format: ReportFormat
    file_size_bytes: int
    created_at: datetime

    model_config = {"from_attributes": True}
