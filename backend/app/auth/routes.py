"""Authentication endpoints (Module 16)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import db as _db  # noqa: F401  (imported first for its sys.path side effect —
# `database` isn't importable until this runs; see app/db.py's docstring)
from database.models import User

from ..config import settings
from ..db import get_db
from ..schemas.auth import PasswordChange, TokenResponse, UserCreate, UserResponse
from .dependencies import get_current_user, require_admin
from .security import create_access_token, hash_password, verify_password
from .audit import write_audit_log

router = APIRouter()


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/auth/login", response_model=TokenResponse)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    # Accepts either username or email in the same field — the existing frontend/mobile
    # login forms both collect "email", and forcing a UX change to "username" for this
    # alone isn't worth it. Looking up by either doesn't weaken anything: both are unique,
    # and the error message below is identical regardless of which one (or neither)
    # matched, or whether the password was wrong.
    user = (
        db.query(User)
        .filter((User.username == form_data.username) | (User.email == form_data.username))
        .first()
    )

    # Same generic error whether the username doesn't exist or the password is wrong —
    # a different message for "no such user" vs "wrong password" would let an attacker
    # enumerate valid usernames.
    invalid_credentials = HTTPException(status_code=401, detail="Incorrect username or password.")

    if user is None or not verify_password(form_data.password, user.password_hash):
        write_audit_log(
            db,
            user_id=user.id if user else None,
            action="login_failed",
            resource_type="user",
            resource_id=user.id if user else None,
            details={"username_attempted": form_data.username},
            ip_address=_client_ip(request),
        )
        db.commit()
        raise invalid_credentials

    write_audit_log(
        db,
        user_id=user.id,
        action="login_succeeded",
        resource_type="user",
        resource_id=user.id,
        ip_address=_client_ip(request),
    )
    db.commit()

    token = create_access_token(user_id=user.id, username=user.username, role=user.role.value)
    return TokenResponse(access_token=token, expires_in_minutes=settings.access_token_expire_minutes)


@router.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/auth/users", response_model=UserResponse, status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> UserResponse:
    existing = (
        db.query(User)
        .filter((User.username == payload.username) | (User.email == payload.email))
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="A user with that username or email already exists.")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.flush()
    write_audit_log(
        db,
        user_id=admin.id,
        action="user_created",
        resource_type="user",
        resource_id=user.id,
        details={"created_username": user.username, "role": user.role.value},
    )
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.patch("/auth/me/password", status_code=204)
def change_my_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")

    current_user.password_hash = hash_password(payload.new_password)
    write_audit_log(
        db,
        user_id=current_user.id,
        action="password_changed",
        resource_type="user",
        resource_id=current_user.id,
    )
    db.commit()
