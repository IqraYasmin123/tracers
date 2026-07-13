"""Custom exception for the dataset module."""


class DatasetLoadError(RuntimeError):
    """Raised when a dataset fails to load — missing directory, unrecognized structure,
    or no valid (image, caption) pairs found."""
