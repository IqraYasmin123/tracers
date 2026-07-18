"""
TracerPipelineService — wraps the AI engine (Modules 2-8) behind a single service used by
API routes.

Lazily loads CLIP and the trained detector on first real use, not at import time or app
startup — this keeps `pytest` and app startup fast (neither ever needs to touch torch), and
means the FastAPI app can still start even if the AI engine isn't fully configured yet
(routes needing it will just raise a clear 503 until it is).

Note on the `src` package name: the AI engine's package is still literally named `src`
(from ai-engine/src/), not something more descriptive like `tracer_ai`. This is a documented
piece of technical debt carried over from Modules 2-8's development — renaming it now would
touch ~40 files across 6 modules for a cosmetic improvement, with real risk of breaking
something that already works. A future refactor (post-FYP) could rename it cleanly.
"""
from __future__ import annotations

import base64
import hashlib
import io
import sys
import time
from pathlib import Path
from typing import Optional

from PIL import Image

from ..config import settings

_AI_ENGINE_PATH = str(Path(settings.ai_engine_path).resolve())
if _AI_ENGINE_PATH not in sys.path:
    sys.path.insert(0, _AI_ENGINE_PATH)


class TracerPipelineService:
    """Constructed once (see app/dependencies.py's lru_cache) and reused across every
    request — loading CLIP per-request would make every API call take 10+ seconds."""

    def __init__(self) -> None:
        self._vlm = None
        self._detector = None
        self._attack_classifier = None
        self._explainer = None

    def _ensure_loaded(self) -> None:
        if self._vlm is not None:
            return

        from src.detection import EntropyClassifier
        from src.vlm import CLIPVLM, VLMConfig
        from src.xai import RuleBasedExplainer

        self._vlm = CLIPVLM(VLMConfig())
        self._explainer = RuleBasedExplainer()

        detector_path = Path(settings.detector_path)
        if detector_path.exists():
            self._detector = EntropyClassifier().load(str(detector_path))
        # else: left as None — analyze() raises a clear, actionable error if used without one

        attack_path = Path(settings.attack_classifier_path)
        if attack_path.exists():
            self._attack_classifier = EntropyClassifier().load(str(attack_path))

    def analyze(self, image_bytes: bytes, caption: Optional[str] = None) -> dict:
        """Run detection + attribution + explanation on one image. Does NOT run
        reconstruction — see docs/module9_backend.md for why that stays Colab-only for now."""
        self._ensure_loaded()

        if self._detector is None:
            raise RuntimeError(
                "No trained detector available. Train one via "
                "ai-engine/notebooks/05_detection.ipynb, then place entropy_detector.joblib "
                "at the path configured by DETECTOR_PATH (see .env.example)."
            )

        from src.attribution import GradientSaliency
        from src.detection import extract_attention_entropy
        from src.xai import ExplanationContext

        start = time.perf_counter()

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        sha256_hash = hashlib.sha256(image_bytes).hexdigest()

        pixel_values = self._vlm.preprocess_image(image)
        entropy_features = extract_attention_entropy(self._vlm, pixel_values).cpu().numpy()

        prediction = self._detector.predict(entropy_features)[0]
        probabilities = self._detector.predict_proba(entropy_features)[0]
        confidence = float(probabilities[list(self._detector.classes_).index(prediction)])

        attack_type = None
        attack_type_confidence = None
        if self._attack_classifier is not None:
            attack_prediction = self._attack_classifier.predict(entropy_features)[0]
            if attack_prediction != "clean":
                attack_probabilities = self._attack_classifier.predict_proba(entropy_features)[0]
                attack_type = attack_prediction
                attack_type_confidence = float(
                    attack_probabilities[
                        list(self._attack_classifier.classes_).index(attack_prediction)
                    ]
                )

        text_embeds = self._vlm.encode_text([caption or "a photo"])
        attribution = GradientSaliency().generate(self._vlm, pixel_values, text_embeds)
        peak_fraction = float((attribution.heatmap > 0.5).mean())
        heatmap_png_base64 = self._heatmap_to_base64_png(attribution.heatmap)

        context = ExplanationContext(
            detection_verdict=prediction,
            detection_confidence=confidence,
            attack_type=attack_type,
            attack_type_confidence=attack_type_confidence,
            attribution_method=attribution.method,
            attribution_peak_fraction=peak_fraction,
        )
        explanation = self._explainer.explain(context)

        processing_time_ms = (time.perf_counter() - start) * 1000

        return {
            "verdict": prediction,
            "confidence": confidence,
            "attack_type": attack_type,
            "attack_type_confidence": attack_type_confidence,
            "attribution_method": attribution.method,
            "attribution_heatmap_png_base64": heatmap_png_base64,
            "attribution_peak_fraction": peak_fraction,
            "explanation_summary": explanation.summary,
            "explanation_details": explanation.details,
            "sha256_hash": sha256_hash,
            "processing_time_ms": processing_time_ms,
        }

    @staticmethod
    def _heatmap_to_base64_png(heatmap) -> str:
        import matplotlib.cm as cm

        colored = (cm.jet(heatmap)[:, :, :3] * 255).astype("uint8")
        buffer = io.BytesIO()
        Image.fromarray(colored).save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("ascii")
