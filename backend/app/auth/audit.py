"""Writes real rows to the `audit_logs` table (Module 10's schema, unused until now).

Kept as a single small helper called explicitly at the point of each meaningful action
(login, case created, status changed, evidence attached, report generated) rather than
generic middleware — explicit calls make it obvious from reading a route exactly what gets
audited, instead of a blanket "log every request" that buries the meaningful events in
noise (health checks, list views, etc.).
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from .. import db as _db  # noqa: F401  (imported first for its sys.path side effect —
# `database` isn't importable until this runs; see app/db.py's docstring)
from database.models import AuditLog


def write_audit_log(
    db: Session,
    *,
    user_id: Optional[str],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> None:
    """Does not commit — callers already have an open transaction for the action itself
    (e.g. creating a case) and should commit both together, so a failed audit write can't
    silently leave an unaudited action committed."""
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
        )
    )
