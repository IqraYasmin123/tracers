"""FastAPI dependency providers — overridable in tests via app.dependency_overrides."""
from __future__ import annotations

from functools import lru_cache

from .services.pipeline_service import TracerPipelineService


@lru_cache
def get_pipeline_service() -> TracerPipelineService:
    """Singleton: constructing TracerPipelineService is cheap (it doesn't load anything
    until first use — see _ensure_loaded), but we still want exactly one instance per
    process so CLIP is only ever loaded once, not once per request."""
    return TracerPipelineService()
