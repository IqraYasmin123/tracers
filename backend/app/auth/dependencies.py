"""FastAPI dependencies for authentication and role-based access control (Module 16)."""
from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .. import db as _db  # noqa: F401  (imported first for its sys.path side effect —
# `database` isn't importable until this runs; see app/db.py's docstring)
from database.models import User, UserRole

from ..db import get_db
from .security import decode_access_token

# tokenUrl is only used to populate FastAPI's interactive docs ("Authorize" button) with
# the right endpoint — it doesn't affect how tokens are actually validated below.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    unauthorized = HTTPException(
        status_code=401,
        detail="Not authenticated. Include a valid 'Authorization: Bearer <token>' header.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise unauthorized

    payload = decode_access_token(token)
    if payload is None:
        raise unauthorized

    user = db.query(User).filter(User.id == payload.user_id).first()
    if user is None:
        # The account referenced by an otherwise-valid token no longer exists (deleted
        # after the token was issued) — treat exactly like an invalid token, not a 404,
        # so this doesn't leak whether a given user id ever existed.
        raise unauthorized
    return user


def require_role(*allowed_roles: UserRole):
    """Dependency factory: `Depends(require_role(UserRole.ADMIN))` etc. Returns a dependency
    that resolves the current user via get_current_user, then 403s if their role isn't in
    the allowed set — kept separate from get_current_user so read-only routes can require
    "any authenticated user" without every route needing its own role list."""

    def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"This action requires one of these roles: {[r.value for r in allowed_roles]}.",
            )
        return user

    return _check


# Convenience dependencies for the common cases used across routes.
require_viewer_or_above = require_role(UserRole.VIEWER, UserRole.INVESTIGATOR, UserRole.ADMIN)
require_investigator_or_above = require_role(UserRole.INVESTIGATOR, UserRole.ADMIN)
require_admin = require_role(UserRole.ADMIN)
