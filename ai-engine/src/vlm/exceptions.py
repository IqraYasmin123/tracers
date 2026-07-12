"""Custom exceptions for the VLM module.

Using specific exception types (instead of bare Exception) lets calling code — later, the
FastAPI backend — catch and handle load failures differently from inference failures
(e.g. return a 503 "model unavailable" vs a 422 "bad input image").
"""


class VLMLoadError(RuntimeError):
    """Raised when a VLM backbone fails to load (bad model name, network issue, OOM, etc.)."""


class VLMInferenceError(RuntimeError):
    """Raised when a forward pass through the VLM fails (bad input, shape mismatch, etc.)."""
