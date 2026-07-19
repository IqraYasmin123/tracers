"""
TRACER database schema — SQLAlchemy ORM models.

Six tables, normalized to 3NF:
    users        — accounts and roles
    cases        — forensic investigations
    evidence     — uploaded images belonging to a case
    ai_results   — one AI analysis result per piece of evidence
    reports      — generated PDF/DOCX reports for a case
    audit_logs   — who did what, when (security/compliance trail)

Normalization notes:
    - ai_results references evidence (not cases) — an AI result belongs to one specific
      piece of evidence, not directly to a case. Going through evidence avoids a transitive
      dependency (case info would otherwise be reachable two ways).
    - Every foreign key references a primary key directly — no table stores a copy of data
      that belongs in another table (e.g. case titles are never duplicated into evidence).
    - JSON columns (explanation_details, audit details) hold genuinely variable-shape data
      that doesn't warrant its own table — using JSON here isn't a normalization violation
      since these aren't multivalued attributes with independent meaning, just structured
      metadata for one row.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum as SqlEnum, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _new_uuid() -> str:
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    INVESTIGATOR = "investigator"
    VIEWER = "viewer"


class CaseStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    ARCHIVED = "archived"


class Verdict(str, enum.Enum):
    CLEAN = "clean"
    ADVERSARIAL = "adversarial"


class ReportFormat(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole), nullable=False, default=UserRole.INVESTIGATOR
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    cases_created: Mapped[list["Case"]] = relationship(back_populates="created_by_user")
    evidence_uploaded: Mapped[list["Evidence"]] = relationship(back_populates="uploaded_by_user")
    reports_generated: Mapped[list["Report"]] = relationship(back_populates="generated_by_user")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    case_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[CaseStatus] = mapped_column(
        SqlEnum(CaseStatus), nullable=False, default=CaseStatus.OPEN
    )
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    created_by_user: Mapped["User"] = relationship(back_populates="cases_created")
    evidence: Mapped[list["Evidence"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cases.id"), nullable=False, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    case: Mapped["Case"] = relationship(back_populates="evidence")
    uploaded_by_user: Mapped["User"] = relationship(back_populates="evidence_uploaded")
    ai_result: Mapped[Optional["AIResult"]] = relationship(
        back_populates="evidence", uselist=False, cascade="all, delete-orphan"
    )


class AIResult(Base):
    __tablename__ = "ai_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    evidence_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evidence.id"), nullable=False, unique=True, index=True
    )
    verdict: Mapped[Verdict] = mapped_column(SqlEnum(Verdict), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    attack_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    attack_type_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    attribution_method: Mapped[str] = mapped_column(String(100), nullable=False)
    attribution_heatmap_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    attribution_peak_fraction: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reconstruction_ssim: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reconstruction_psnr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reconstruction_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    explanation_summary: Mapped[str] = mapped_column(Text, nullable=False)
    explanation_details: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    processing_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    evidence: Mapped["Evidence"] = relationship(back_populates="ai_result")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cases.id"), nullable=False, index=True
    )
    generated_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    format: Mapped[ReportFormat] = mapped_column(
        SqlEnum(ReportFormat), nullable=False, default=ReportFormat.PDF
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    case: Mapped["Case"] = relationship(back_populates="reports")
    generated_by_user: Mapped["User"] = relationship(back_populates="reports_generated")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    user: Mapped[Optional["User"]] = relationship(back_populates="audit_logs")
