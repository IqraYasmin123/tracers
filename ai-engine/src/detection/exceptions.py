"""Custom exceptions for the detection module."""


class DetectorNotFittedError(RuntimeError):
    """Raised when predict()/predict_proba() is called before fit() or load()."""


class DetectionError(RuntimeError):
    """Raised when detection fails for reasons other than an unfitted model — e.g. empty
    or malformed input features."""
