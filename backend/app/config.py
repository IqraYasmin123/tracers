"""Application configuration, loaded from environment variables (.env at repo root)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

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

    # Path to the repo root's `database` package (sibling to backend/ and ai-engine/), so
    # `database.connection` / `database.models` become importable — same pattern as
    # ai_engine_path above.
    database_package_path: str = os.getenv("DATABASE_PACKAGE_PATH", "..")

    # Where uploaded evidence images are saved on disk once attached to a case (Module 13).
    # Module 9's stateless /analyze never persists anything; this only applies to
    # /cases/{id}/evidence, which does.
    evidence_storage_dir: str = os.getenv("EVIDENCE_STORAGE_DIR", "./data/evidence")

    # Where generated PDF/DOCX case reports are saved (Module 14).
    report_storage_dir: str = os.getenv("REPORT_STORAGE_DIR", "./data/reports")

    # --- Auth (Module 16) ---
    # HARD REQUIREMENT for anything beyond local dev: set a real, random JWT_SECRET_KEY via
    # environment variable. The fallback below is intentionally obvious and identical for
    # every fresh checkout — anyone using it in production could forge tokens for any user.
    jwt_secret_key: str = os.getenv(
        "JWT_SECRET_KEY", "INSECURE-DEV-ONLY-SECRET-CHANGE-ME-IN-PRODUCTION"
    )
    jwt_algorithm: str = "HS256"
    # 8 hours: long enough that an investigator mid-case isn't forced to re-login every
    # few minutes, short enough that a leaked token doesn't stay valid indefinitely. No
    # refresh-token flow exists yet (out of scope for this pass) — re-login is required
    # after expiry.
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

    # The initial admin account bootstrapped on first startup if no users exist yet (see
    # app/auth/bootstrap.py). Only the username/email are configurable — the password is
    # always freshly, randomly generated and printed once, never hardcoded or stored in
    # config, so it can't accidentally ship in a repo or .env file.
    initial_admin_username: str = os.getenv("INITIAL_ADMIN_USERNAME", "admin")
    initial_admin_email: str = os.getenv("INITIAL_ADMIN_EMAIL", "admin@tracer.local")

    # CORS: a real allowlist instead of Module 9's original wildcard, now that real auth
    # exists and tokens matter. Comma-separated env var; defaults to the React dev
    # server's known port. Flutter web's dev server picks a random port on every run —
    # either pin one with `flutter run -d chrome --web-port=<port>` and add it here, or
    # add it to ALLOWED_ORIGINS for local testing convenience.
    allowed_origins: list[str] = field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv(
                "ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
            ).split(",")
            if origin.strip()
        ]
    )


settings = Settings()
