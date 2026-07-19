"""Ensures the repo root (parent of database/) is on sys.path, so `from database.models
import ...` resolves correctly regardless of which directory pytest is invoked from, or
whether it's invoked as `pytest` or `python -m pytest`.

Without this, running plain `pytest` from inside `database/` fails with
`ModuleNotFoundError: No module named 'database'` — pytest's own directory-based sys.path
insertion adds `database/tests` (or `database/`), not the repo root one level further up.
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
