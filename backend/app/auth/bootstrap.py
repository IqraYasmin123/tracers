"""Bootstraps exactly one initial admin account if the `users` table is empty.

No account creation happens without an authenticated admin already existing (see
app/api/routes/auth.py's user-creation endpoint, which requires require_admin) — so
without this bootstrap step, a fresh database would have no way to create its first user
at all. Standard pattern (same idea as Django's createsuperuser or Jenkins' initial admin
password file): the password is randomly generated, never hardcoded, never stored in
config or committed anywhere, and printed to the console exactly once.
"""
from __future__ import annotations

import secrets
import string

from sqlalchemy.orm import Session

from .. import db as _db  # noqa: F401  (imported first for its sys.path side effect —
# `database` isn't importable until this runs; see app/db.py's docstring. This module
# happens to only ever get imported after cases.py has already primed sys.path via
# main.py's import order, but relying on that is exactly the fragile assumption that
# caused a real crash in Module 13 — see docs/module13_case_management.md — so this
# defends itself too rather than relying on import order elsewhere.)
from database.models import User, UserRole

from ..config import settings
from .security import hash_password


def _generate_password(length: int = 20) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def bootstrap_initial_admin(db: Session) -> None:
    if db.query(User).count() > 0:
        return  # already has at least one account — never overwrite/reset anything

    password = _generate_password()
    admin = User(
        username=settings.initial_admin_username,
        email=settings.initial_admin_email,
        password_hash=hash_password(password),
        role=UserRole.ADMIN,
    )
    db.add(admin)
    db.commit()

    # Deliberately loud — this is the only time this password will ever be visible.
    print("\n" + "=" * 70)
    print("TRACER: no user accounts existed, so an initial admin account was created.")
    print(f"  username: {settings.initial_admin_username}")
    print(f"  password: {password}")
    print("Log in and change this password immediately. It will not be shown again.")
    print("=" * 70 + "\n")
