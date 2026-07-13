"""Custom exception for the attacks module."""


class AttackGenerationError(RuntimeError):
    """Raised when generating an adversarial example fails (e.g. no gradient computed,
    shape mismatch between image and text embeddings)."""
