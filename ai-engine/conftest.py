"""Ensures `src` is importable regardless of how pytest is invoked.

`python -m pytest` adds the current directory to sys.path automatically; a bare `pytest`
invocation does not. This file's mere presence at the ai-engine root makes pytest treat
ai-engine/ as the rootdir and add it to sys.path, so `from src.dataset import ...` works
the same way whether you run `pytest tests/` or `python -m pytest tests/`.
"""
