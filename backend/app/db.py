"""Wires Module 10's `database` package into this app.

`database` lives at the repo root — a sibling of `backend/` and `ai-engine/`, not a
subpackage of either — so it isn't importable by default when running the backend from
inside `backend/`. Made importable the same way `pipeline_service.py` handles
`ai-engine/src`: insert the resolved path onto `sys.path` before importing.

`get_db` is re-exported here (rather than importing `database.connection` directly all over
`app/api/routes/`) so every route depends on *this* module, giving one place to swap the
implementation later if needed.
"""
from __future__ import annotations

import sys
from pathlib import Path

from .config import settings

_DATABASE_PACKAGE_PATH = str(Path(settings.database_package_path).resolve())
if _DATABASE_PACKAGE_PATH not in sys.path:
    sys.path.insert(0, _DATABASE_PACKAGE_PATH)

from database.connection import SessionLocal, engine, get_db  # noqa: E402
from database.models import Base  # noqa: E402

# Dev convenience only: creates any missing tables on a fresh SQLite dev database so
# `uvicorn app.main:app --reload` works immediately without a manual Alembic step. Alembic
# (database/migrations/) remains the canonical, authoritative way to evolve the schema —
# this call is a no-op against a database that Alembic has already brought up to date, and
# is never the right tool for a real Postgres deployment's initial setup.
Base.metadata.create_all(bind=engine)

__all__ = ["get_db", "SessionLocal", "engine"]
