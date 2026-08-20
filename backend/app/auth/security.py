"""Password hashing and JWT token issuance/validation (Module 16).

Kept as pure functions with no FastAPI/database imports at the top level so this logic is
directly unit-testable without spinning up the app or a database.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt

from ..config import settings


def hash_password(plain_password: str) -> str:
    """bcrypt with its own random salt per call — never store or log the plain password."""
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Timing-safe comparison — bcrypt.checkpw is constant-time by design, so this doesn't
    leak how many characters matched via response timing."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Malformed hash (shouldn't happen with real data) — fail closed, not open.
        return False


def create_access_token(user_id: str, username: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


class TokenPayload:
    def __init__(self, user_id: str, username: str, role: str):
        self.user_id = user_id
        self.username = username
        self.role = role


def decode_access_token(token: str) -> Optional[TokenPayload]:
    """Returns None for any invalid/expired/malformed token — callers turn that into a 401,
    this function itself never raises for untrusted input."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None
    sub = payload.get("sub")
    username = payload.get("username")
    role = payload.get("role")
    if not sub or not username or not role:
        return None
    return TokenPayload(user_id=sub, username=username, role=role)
