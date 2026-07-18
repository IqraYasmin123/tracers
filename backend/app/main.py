"""TRACER FastAPI application entry point.

Run locally:
    uvicorn app.main:app --reload

Then visit http://127.0.0.1:8000/docs for interactive API documentation.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routes import health, inference
from .config import settings
from .logging_config import configure_logging

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TRACER API",
    description=(
        "Digital forensics API for detecting, attributing, and reconstructing adversarial "
        "attacks in Vision-Language Models."
    ),
    version="0.1.0",
)

# Permissive CORS for local development. Tightened in Module 16 (Security & Authentication)
# once real auth/allowed-origins configuration exists — never ship "*" to production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(inference.router, prefix="/api/v1", tags=["inference"])


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError) -> JSONResponse:
    """Every AI-engine exception (VLMLoadError, DetectionError, AttributionError, etc.)
    subclasses RuntimeError — mapped to 503 'service temporarily unavailable' since these
    represent the AI engine not being ready/configured correctly, not bad user input."""
    logger.error("Pipeline error: %s", exc)
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Config/input validation errors (e.g. from a dataclass's __post_init__) map to 422."""
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.get("/")
def root() -> dict:
    return {"service": "TRACER API", "status": "running", "docs": "/docs"}
