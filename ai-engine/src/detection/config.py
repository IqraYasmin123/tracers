"""Configuration for TRACER's entropy-based classifier."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DetectionConfig:
    """Configuration for EntropyClassifier.

    Attributes:
        classifier_type: Which sklearn model backs the classifier. "mlp" (default) is the
            original small neural net. "gboost" is a GradientBoostingClassifier -- an
            experiment for closing the measured PGD@2/255 detection gap (see
            ai-engine/notebooks/05b_table2_evaluation.ipynb): gradient boosting splits on
            individual feature thresholds rather than fitting smooth decision boundaries,
            which can pick out a few informative std/delta dimensions even when the overall
            clean/adversarial separation in entropy-feature space is small, as it is for
            PGD at low epsilon. Both read the same feature vectors (mean-only or rich) --
            this is a classifier swap, not a new feature set.
        hidden_layer_sizes: MLP architecture (only used when classifier_type="mlp"). Small
            on purpose -- the input is only a per-layer entropy vector (12 numbers for CLIP
            ViT-B/32), not raw pixels, so a large network would just overfit.
        max_iter: Training iterations cap (only used when classifier_type="mlp").
        n_estimators: Number of boosting stages (only used when classifier_type="gboost").
        max_depth: Max depth of each boosting tree (only used when classifier_type="gboost").
            Kept shallow (3) since the feature vectors are small (12-35 dims) and training
            sets are a few thousand rows at most -- deeper trees would overfit.
        learning_rate: Shrinkage applied to each tree's contribution (only used when
            classifier_type="gboost").
        random_state: Fixed seed for reproducible training results across runs.
    """

    classifier_type: str = "mlp"
    hidden_layer_sizes: tuple = field(default_factory=lambda: (32, 16))
    max_iter: int = 1000
    n_estimators: int = 200
    max_depth: int = 3
    learning_rate: float = 0.05
    random_state: int = 42

    def __post_init__(self) -> None:
        if self.classifier_type not in ("mlp", "gboost"):
            raise ValueError(
                f"classifier_type must be 'mlp' or 'gboost', got {self.classifier_type!r}"
            )
