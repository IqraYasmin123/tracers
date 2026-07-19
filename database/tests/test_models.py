"""Tests for the database schema (Module 10).

Run against an in-memory SQLite database — fast, no real PostgreSQL server needed. SQLite
doesn't exercise every PostgreSQL-specific behavior (native ENUM storage, JSONB indexing),
so treat this as verifying the schema's *logic* (relationships, constraints, cascades) is
correct, not as a full PostgreSQL compatibility guarantee — spot-check against real Postgres
once you have one running (see docs/module10_database.md).

Run:
    pytest tests/test_models.py -v
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from database.models import (
    AIResult,
    AuditLog,
    Base,
    Case,
    CaseStatus,
    Evidence,
    Report,
    ReportFormat,
    User,
    UserRole,
    Verdict,
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_user(db_session: Session) -> User:
    user = User(
        username="jdoe",
        email="jdoe@example.com",
        password_hash="hashed_password_placeholder",
        role=UserRole.INVESTIGATOR,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_case(db_session: Session, sample_user: User) -> Case:
    case = Case(
        case_number="CASE-0001",
        title="Suspicious upload investigation",
        status=CaseStatus.OPEN,
        created_by=sample_user.id,
    )
    db_session.add(case)
    db_session.commit()
    return case


# ---------------------------------------------------------------------------
# Basic create/read for each table
# ---------------------------------------------------------------------------


def test_create_user(db_session, sample_user):
    fetched = db_session.query(User).filter_by(username="jdoe").first()
    assert fetched is not None
    assert fetched.email == "jdoe@example.com"
    assert fetched.role == UserRole.INVESTIGATOR
    assert fetched.created_at is not None


def test_create_case_linked_to_user(db_session, sample_case, sample_user):
    fetched = db_session.query(Case).filter_by(case_number="CASE-0001").first()
    assert fetched is not None
    assert fetched.created_by == sample_user.id
    assert fetched.created_by_user.username == "jdoe"


def test_create_evidence_linked_to_case(db_session, sample_case, sample_user):
    evidence = Evidence(
        case_id=sample_case.id,
        original_filename="photo.jpg",
        storage_path="/data/evidence/photo.jpg",
        sha256_hash="a" * 64,
        mime_type="image/jpeg",
        file_size_bytes=204800,
        uploaded_by=sample_user.id,
    )
    db_session.add(evidence)
    db_session.commit()

    fetched = db_session.query(Evidence).filter_by(original_filename="photo.jpg").first()
    assert fetched.case.case_number == "CASE-0001"
    assert fetched.uploaded_by_user.username == "jdoe"


def test_create_ai_result_linked_to_evidence(db_session, sample_case, sample_user):
    evidence = Evidence(
        case_id=sample_case.id,
        original_filename="photo.jpg",
        storage_path="/data/evidence/photo.jpg",
        sha256_hash="a" * 64,
        mime_type="image/jpeg",
        file_size_bytes=204800,
        uploaded_by=sample_user.id,
    )
    db_session.add(evidence)
    db_session.commit()

    result = AIResult(
        evidence_id=evidence.id,
        verdict=Verdict.ADVERSARIAL,
        confidence=0.92,
        attack_type="pgd",
        attack_type_confidence=0.71,
        attribution_method="gradient_saliency",
        attribution_peak_fraction=0.28,
        explanation_summary="This image was classified as ADVERSARIAL with 92.0% confidence.",
        explanation_details=["Detail one.", "Detail two."],
        processing_time_ms=1234.5,
    )
    db_session.add(result)
    db_session.commit()

    fetched = db_session.query(AIResult).filter_by(evidence_id=evidence.id).first()
    assert fetched.verdict == Verdict.ADVERSARIAL
    assert fetched.explanation_details == ["Detail one.", "Detail two."]
    assert fetched.evidence.original_filename == "photo.jpg"


def test_create_report_linked_to_case(db_session, sample_case, sample_user):
    report = Report(
        case_id=sample_case.id,
        generated_by=sample_user.id,
        file_path="/data/reports/case-0001.pdf",
        format=ReportFormat.PDF,
    )
    db_session.add(report)
    db_session.commit()

    fetched = db_session.query(Report).filter_by(case_id=sample_case.id).first()
    assert fetched.format == ReportFormat.PDF
    assert fetched.case.title == "Suspicious upload investigation"


def test_create_audit_log(db_session, sample_user):
    log = AuditLog(
        user_id=sample_user.id,
        action="login",
        resource_type="user",
        resource_id=sample_user.id,
        details={"ip": "127.0.0.1"},
    )
    db_session.add(log)
    db_session.commit()

    fetched = db_session.query(AuditLog).filter_by(action="login").first()
    assert fetched.details == {"ip": "127.0.0.1"}
    assert fetched.user.username == "jdoe"


def test_audit_log_allows_null_user_for_system_actions(db_session):
    """Not every audit event has a human actor — e.g. an automated system cleanup job."""
    log = AuditLog(user_id=None, action="scheduled_cleanup", resource_type="evidence")
    db_session.add(log)
    db_session.commit()

    fetched = db_session.query(AuditLog).filter_by(action="scheduled_cleanup").first()
    assert fetched.user_id is None
    assert fetched.user is None


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------


def test_username_must_be_unique(db_session, sample_user):
    duplicate = User(
        username="jdoe",  # same as sample_user
        email="different@example.com",
        password_hash="x",
    )
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_case_number_must_be_unique(db_session, sample_case, sample_user):
    duplicate = Case(
        case_number="CASE-0001",  # same as sample_case
        title="A different case",
        created_by=sample_user.id,
    )
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_ai_result_evidence_id_must_be_unique(db_session, sample_case, sample_user):
    """One AI result per piece of evidence, not many — enforced at the schema level, not
    just by application logic."""
    evidence = Evidence(
        case_id=sample_case.id,
        original_filename="photo.jpg",
        storage_path="/data/evidence/photo.jpg",
        sha256_hash="a" * 64,
        mime_type="image/jpeg",
        file_size_bytes=204800,
        uploaded_by=sample_user.id,
    )
    db_session.add(evidence)
    db_session.commit()

    first_result = AIResult(
        evidence_id=evidence.id,
        verdict=Verdict.CLEAN,
        confidence=0.9,
        attribution_method="gradient_saliency",
        explanation_summary="Clean.",
        processing_time_ms=100.0,
    )
    db_session.add(first_result)
    db_session.commit()

    duplicate_result = AIResult(
        evidence_id=evidence.id,  # same evidence again
        verdict=Verdict.ADVERSARIAL,
        confidence=0.8,
        attribution_method="gradient_saliency",
        explanation_summary="Adversarial.",
        processing_time_ms=100.0,
    )
    db_session.add(duplicate_result)
    with pytest.raises(IntegrityError):
        db_session.commit()


# ---------------------------------------------------------------------------
# Cascades
# ---------------------------------------------------------------------------


def test_deleting_case_cascades_to_evidence(db_session, sample_case, sample_user):
    evidence = Evidence(
        case_id=sample_case.id,
        original_filename="photo.jpg",
        storage_path="/data/evidence/photo.jpg",
        sha256_hash="a" * 64,
        mime_type="image/jpeg",
        file_size_bytes=204800,
        uploaded_by=sample_user.id,
    )
    db_session.add(evidence)
    db_session.commit()
    evidence_id = evidence.id

    db_session.delete(sample_case)
    db_session.commit()

    assert db_session.query(Evidence).filter_by(id=evidence_id).first() is None
