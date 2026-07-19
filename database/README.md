# TRACER Database

PostgreSQL schema, ER diagram, and migrations for users, cases, evidence, AI results,
reports, and audit logs.

**Status:** Module 10 complete — schema designed (3NF), SQLAlchemy models, Alembic
migrations verified end-to-end. Not yet wired into the backend (that's Module 13 — Case
Management).

## Quick Start

```bash
pip install -r requirements.txt

# Local dev / testing (no Postgres needed) — uses SQLite by default:
python -m pytest tests/ -v      # run from repo root, not from inside database/

# Real PostgreSQL:
# 1. Start a Postgres server (see docs/module10_database.md for Docker/native instructions)
# 2. Set DATABASE_URL in your .env
# 3. Apply the schema:
alembic upgrade head
```

## Files

- `models.py` — SQLAlchemy ORM models (the source of truth)
- `connection.py` — engine/session setup, ready for Module 13 to use
- `schemas/schema.sql` — generated reference DDL (regenerate via
  `python scripts/generate_schema_sql.py` at repo root — never hand-edit)
- `migrations/` — Alembic scaffold + the verified initial migration
- `tests/` — 11 tests against in-memory SQLite

See [`docs/module10_database.md`](../docs/module10_database.md) at the repo root for full
design documentation.
