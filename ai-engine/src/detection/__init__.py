"""Adversarial detection and attack-type classification (Module 5).

Public API:
    BaseDetector                — abstract interface
    EntropyClassifier            — MLP classifier over entropy features (binary or multi-class)
    DetectionConfig              — configuration dataclass
    DetectorNotFittedError, DetectionError — module-specific exceptions
    compute_entropy_from_attentions — core math, VLM-independent, unit-testable in isolation
    extract_attention_entropy    — thin wrapper connecting the math to a real BaseVLM
    plot_entropy_profiles, plot_confusion_matrix, plot_roc_curve — visualization utilities

Example (binary detection):
    >>> from src.detection import EntropyClassifier, extract_attention_entropy
    >>> features = extract_attention_entropy(vlm, pixel_values).cpu().numpy()
    >>> detector = EntropyClassifier().fit(X_train, y_train)   # y in {"clean","adversarial"}
    >>> detector.predict(features)

Example (attack-type classification — same class, different labels):
    >>> classifier = EntropyClassifier().fit(X_train, y_train)  # y in {"clean","fgsm","pgd"}
    >>> classifier.predict(features)
"""
from .base import BaseDetector
from .config import DetectionConfig
from .detector import EntropyClassifier
from .exceptions import DetectionError, DetectorNotFittedError
from .features import compute_entropy_from_attentions, extract_attention_entropy
from .visualize import plot_confusion_matrix, plot_entropy_profiles, plot_roc_curve

__all__ = [
    "BaseDetector",
    "EntropyClassifier",
    "DetectionConfig",
    "DetectorNotFittedError",
    "DetectionError",
    "compute_entropy_from_attentions",
    "extract_attention_entropy",
    "plot_entropy_profiles",
    "plot_confusion_matrix",
    "plot_roc_curve",
]
