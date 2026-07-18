"""Application configuration, loaded from environment variables (.env at repo root)."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """Backend settings. Every field has a sensible default so the app can start without
    a .env file present — real deployments should override via environment variables."""

    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Path to the ai-engine directory, so its `src` package becomes importable.
    ai_engine_path: str = os.getenv("AI_ENGINE_PATH", "../ai-engine")

    # Paths to trained model weights saved by the Module 5 notebook. Not committed to git
    # (see .gitignore) — download entropy_detector.joblib from your Google Drive
    # (MyDrive/TRACER/models/) to this path to enable real detection locally.
    detector_path: str = os.getenv(
        "DETECTOR_PATH", "../ai-engine/models/entropy_detector.joblib"
    )
    attack_classifier_path: str = os.getenv(
        "ATTACK_CLASSIFIER_PATH", "../ai-engine/models/attack_classifier.joblib"
    )

    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))


settings = Settings()
