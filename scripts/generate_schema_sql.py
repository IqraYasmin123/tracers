"""
Regenerates database/schemas/schema.sql directly from database/models.py, for the
PostgreSQL dialect. Run this any time models.py changes, so schema.sql never drifts out of
sync with the actual ORM definitions.

Usage (from repo root):
    python scripts/generate_schema_sql.py
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from database.models import Base


def main() -> None:
    statements = []
    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=postgresql.dialect())).strip()
        statements.append(ddl + ";")

    output = "\n\n".join(statements)

    with open("database/schemas/schema.sql", "w", encoding="utf-8") as f:
        f.write("-- TRACER database schema (PostgreSQL)\n")
        f.write("-- Auto-generated from database/models.py — do not hand-edit.\n")
        f.write("-- Regenerate via: python scripts/generate_schema_sql.py\n\n")
        f.write(output)
        f.write("\n")

    print("database/schemas/schema.sql regenerated.")


if __name__ == "__main__":
    main()
