"""Custom exception for the attribution module."""


class AttributionError(RuntimeError):
    """Raised when generating an attribution heatmap fails — no gradient computed, missing
    required input, or an attention tensor that can't be reshaped into a spatial grid."""
