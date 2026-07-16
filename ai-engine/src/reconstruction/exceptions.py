"""Custom exception for the reconstruction module."""


class ReconstructionError(RuntimeError):
    """Raised when reconstruction fails — invalid heatmap range, shape mismatch between
    images being compared, or the underlying diffusion pipeline erroring."""
