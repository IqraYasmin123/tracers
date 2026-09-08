"""Adversarial detection and attack-type classification (Module 5).

Public API:
    BaseDetector                — abstract interface
    EntropyClassifier            — MLP classifier over entropy features (binary or multi-class)
    DetectionConfig              — configuration dataclass
    DetectorNotFittedError, DetectionError — module-specific exceptions
    compute_entropy_from_attentions — core math (mean-only), VLM-independent, unit-testable
    extract_attention_entropy    — thin wrapper connecting the mean-only math to a real BaseVLM
    compute_rich_features_from_attentions — extended math (mean + std + cross-layer deltas)
    extract_rich_features        — thin wrapper connecting the extended math to a real BaseVLM
    plot_entropy_profiles, plot_confusion_matrix, plot_roc_curve — visualization utilities

Example (binary detection):
    >>> from src.detection import EntropyClassifier, extract_attention_entropy
    >>> features = extract_attention_entropy(vlm, pixel_values).cpu().numpy()
    >>> detector = EntropyClassifier().fit(X_train, y_train)   # y in {"clean","adversarial"}
    >>> detector.predict(features)

Example (attack-type classification — same class, different labels):
    >>> classifier = EntropyClassifier().fit(X_train, y_train)  # y in {"clean","fgsm","pgd"}
    >>> classifier.predict(features)

Example (richer features — mean + std + cross-layer deltas, an experiment for closing a
measured accuracy gap, particularly on PGD at small epsilon):
    >>> from src.detection import EntropyClassifier, extract_rich_features
    >>> features = extract_rich_features(vlm, pixel_values).cpu().numpy()
    >>> detector = EntropyClassifier().fit(X_train, y_train)  # same classifier, richer input
"""
from .base import BaseDetector
from .config import DetectionConfig
from .detector import EntropyClassifier
from .exceptions import DetectionError, DetectorNotFittedError
from .features import (
    compute_entropy_from_attentions,
    compute_rich_features_from_attentions,
    extract_attention_entropy,
    extract_rich_features,
)
from .visualize import plot_confusion_matrix, plot_entropy_profiles, plot_roc_curve

__all__ = [
    "BaseDetector",
    "EntropyClassifier",
    "DetectionConfig",
    "DetectorNotFittedError",
    "DetectionError",
    "compute_entropy_from_attentions",
    "extract_attention_entropy",
    "compute_rich_features_from_attentions",
    "extract_rich_features",
    "plot_entropy_profiles",
    "plot_confusion_matrix",
    "plot_roc_curve",
]
