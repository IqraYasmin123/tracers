"""
Generic entropy-feature classifier.

Serves two roles in TRACER depending on what labels it's trained with:
    - Binary detector: fit with y in {"clean", "adversarial"}
    - Attack-type classifier: fit with y in {"clean", "fgsm", "pgd"}

Same underlying model both times -- this is intentional, not a shortcut. The classification
task is the same shape (entropy features -> label) regardless of how many classes there are;
duplicating the class for "2-class" vs "N-class" would just be copy-pasted code with no real
difference in behavior.

Backing model is selected via DetectionConfig.classifier_type ("mlp" or "gboost") -- see
config.py for why gradient boosting is offered as an alternative.
"""
from __future__ import annotations

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

from .base import BaseDetector
from .config import DetectionConfig
from .exceptions import DetectionError, DetectorNotFittedError


def _build_model(config: DetectionConfig):
    if config.classifier_type == "gboost":
        return GradientBoostingClassifier(
            n_estimators=config.n_estimators,
            max_depth=config.max_depth,
            learning_rate=config.learning_rate,
            random_state=config.random_state,
        )
    return MLPClassifier(
        hidden_layer_sizes=config.hidden_layer_sizes,
        max_iter=config.max_iter,
        random_state=config.random_state,
    )


class EntropyClassifier(BaseDetector):
    """Classifier over attention-entropy feature vectors, with feature scaling and
    save/load built in. Backing model (MLP or gradient boosting) is set by
    DetectionConfig.classifier_type."""

    def __init__(self, config: DetectionConfig | None = None) -> None:
        self.config = config or DetectionConfig()
        self._scaler = StandardScaler()
        self._model = _build_model(self.config)
        self._is_fitted = False
        self.classes_: list = []

    def fit(self, X: np.ndarray, y: np.ndarray) -> "EntropyClassifier":
        X = np.asarray(X)
        y = np.asarray(y)
        if len(X) == 0:
            raise DetectionError("Cannot fit on empty training data.")
        if len(X) != len(y):
            raise DetectionError(f"X has {len(X)} samples but y has {len(y)} labels.")

        X_scaled = self._scaler.fit_transform(X)
        self._model.fit(X_scaled, y)
        self._is_fitted = True
        self.classes_ = list(self._model.classes_)
        return self

    def _check_fitted(self) -> None:
        if not self._is_fitted:
            raise DetectorNotFittedError(
                "Model has not been fitted. Call fit() with training data, or load() a "
                "previously saved model, before calling predict()/predict_proba()."
            )

    def predict(self, X: np.ndarray) -> np.ndarray:
        self._check_fitted()
        X_scaled = self._scaler.transform(np.asarray(X))
        return self._model.predict(X_scaled)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        self._check_fitted()
        X_scaled = self._scaler.transform(np.asarray(X))
        return self._model.predict_proba(X_scaled)

    def save(self, path: str) -> None:
        self._check_fitted()
        joblib.dump(
            {"scaler": self._scaler, "model": self._model, "classes": self.classes_}, path
        )

    def load(self, path: str) -> "EntropyClassifier":
        data = joblib.load(path)
        self._scaler = data["scaler"]
        self._model = data["model"]
        self.classes_ = data["classes"]
        self._is_fitted = True
        return self
