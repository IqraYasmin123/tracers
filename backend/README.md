# TRACER Backend

FastAPI REST API — the bridge between the client apps (React, Flutter) and the AI engine.

**Status:** Module 9 complete — health check + image analysis endpoint, dependency-injected
and fully unit tested. Authentication (Module 16) and database persistence (Module 10) not
yet implemented.

## Quick Start

```bash
python -m venv venv
venv\Scripts\activate          # Windows; source venv/bin/activate on Mac/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000/docs` for interactive API documentation.

For real AI inference (not needed just to run tests), also install:
```bash
pip install -r ../ai-engine/requirements.txt
```
and download `entropy_detector.joblib` from your Google Drive into `../ai-engine/models/`.

## Testing

```bash
pytest -v
```

See [`docs/module9_backend.md`](../docs/module9_backend.md) at the repo root for full design
documentation.
