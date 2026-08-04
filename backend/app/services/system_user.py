"""Temporary attribution stand-in for real authentication (Module 16, not yet built).

`Case.created_by` and `Evidence.uploaded_by` are required, real foreign keys to `users.id`
(see database/models.py) — deliberately NOT nullable, because a real forensic system should
never allow an unattributed case or piece of evidence, even temporarily. Rather than weaken
the schema to work around Module 16 not existing yet, every request in Module 13 is
attributed to one seeded "system" account until real login/session handling lands.

Security notes for whoever builds Module 16:
  - This account's password_hash is a fixed sentinel string, not a real hash of anything —
    it must NEVER be able to authenticate through a real login endpoint. Before wiring up
    login, either exclude username == SYSTEM_USERNAME from login entirely, or delete this
    account and replace every caller of get_or_create_system_user() with real
    current-user resolution (e.g. a `Depends(get_current_user)`).
  - This account is role=ADMIN only so it isn't blocked by future role checks on case
    creation — it is NOT meant to imply any real administrator is acting.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from .. import db as _db  # noqa: F401  (imported for its sys.path side effect, not its contents)
from database.models import User, UserRole

SYSTEM_USERNAME = "system"
SYSTEM_EMAIL = "system@tracer.local"
_DISABLED_PASSWORD_SENTINEL = "disabled-no-login-until-module-16-auth-exists"


def get_or_create_system_user(db: Session) -> User:
    """Idempotent: returns the existing system user if present, otherwise creates it."""
    user = db.query(User).filter_by(username=SYSTEM_USERNAME).first()
    if user is not None:
        return user

    user = User(
        username=SYSTEM_USERNAME,
        email=SYSTEM_EMAIL,
        password_hash=_DISABLED_PASSWORD_SENTINEL,
        role=UserRole.ADMIN,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
