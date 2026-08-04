"""Regression test for a real bug: `app/api/routes/cases.py` and `app/schemas/cases.py`
originally imported `database.models` *before* `app.db` (which is what actually adds the
`database` package to `sys.path`) — see app/db.py's docstring. This worked fine under
pytest, because `tests/conftest.py` imports `app.db` first for its own fixtures, which
patched `sys.path` before `cases.py` ever got imported. It failed immediately under real
`uvicorn app.main:app --reload`, which imports `app.main` (and therefore `cases.py`) fresh,
in its own subprocess, with none of that pre-warming.

Running this exact import in a clean subprocess — the same way uvicorn does it — is the
only way to actually catch this class of bug; importing `app.main` normally in this test
file would inherit conftest.py's already-patched sys.path and hide the problem exactly
like it did before.
"""
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


def test_app_main_imports_cleanly_in_a_fresh_process():
    result = subprocess.run(
        [sys.executable, "-c", "from app.main import app"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        "app.main failed to import in a fresh process (the way uvicorn actually starts "
        f"it), even though it may pass under pytest. stderr:\n{result.stderr}"
    )
