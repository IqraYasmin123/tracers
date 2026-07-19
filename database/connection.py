"""Database engine and session management.

Not yet wired into the FastAPI backend — that happens in Module 13 (Case Management), which
will use `get_db()` as a FastAPI dependency the same way Module 9 used
`get_pipeline_service()`. Prepared now so the pattern is consistent when that module arrives.
"""
from __future__ import annotations

import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tracer_dev.db")

# check_same_thread=False is only needed for SQLite (used in tests/local dev without a real
# Postgres server); ignored harmlessly by other dialects if ever passed to them by mistake.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI-style dependency generator — yields a session, always closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
