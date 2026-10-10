"""Application settings: every variable of docs/04-backend/backend.md section 8 (and docs/10-devops/env.example).

Business thresholds (45 days, 14 days, fit cut-offs...) are settings, never literals elsewhere in the code.
The app refuses to start on a weak secret (SEC-10).
"""
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> repo root is three levels above the app package.
_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


class ConfigError(RuntimeError):
    """Raised at startup when the configuration is unsafe or incomplete."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ROOT_ENV) if _ROOT_ENV.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Database ---
    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    # --- Auth ---
    jwt_secret_key: str = ""
    jwt_expire_minutes: int = 480
    cors_origins: str = "http://localhost:3000"
    login_rate_limit_per_min: int = 10

    # --- Uploads ---
    upload_dir: str = "/data/uploads"
    max_upload_mb: int = 10
    upload_rate_limit_per_hour: int = 20
    max_resume_mb: int = 5
    max_resume_pages: int = 4
    resume_rate_limit_per_hour: int = 5

    # --- AI ---
    # D-2 (2026-10-10): the only key the team has is a Groq key, so MDL-01 runs
    # on Groq. The `anthropic` branch is kept for a future key. ai-system 2.1.
    llm_provider: Literal["groq", "anthropic", "none"] = "groq"
    anthropic_api_key: str = ""
    groq_api_key: str = ""
    llm_model: str = "qwen/qwen3.8-27b"
    llm_timeout_s: int = 25
    max_llm_calls_per_day: int = 200
    extraction_cache_dir: str = "/app/extraction_cache"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    hf_home: str = "/models"

    # --- Verification thresholds ---
    cert_auto_certify_min: float = 0.85
    name_match_min: int = 85
    phash_max_distance: int = 6
    tamper_check_enabled: bool = False
    ela_threshold: float = 12.0

    # --- Fit scoring ---
    fit_ready_min: float = 65
    fit_close_min: float = 40
    sim_min: float = 0.60

    # --- Mentoring rules ---
    min_meetings_per_term: int = 2
    attention_no_session_days: int = 45
    issue_stale_days: int = 14
    session_confirm_days: int = 7
    at_risk_attendance_pct: float = 75.0
    at_risk_cgpa_drop: float = 1.0
    mentor_load_warn: int = 20
    reminder_term_end_days: int = 30
    current_term_id: str = ""
    today_override: date | None = None

    # --- Ops ---
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @field_validator("today_override", mode="before")
    @classmethod
    def _empty_date_is_none(cls, value: object) -> object:
        # `.env` lines such as `TODAY_OVERRIDE=` arrive as an empty string.
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def _check_secrets(self) -> "Settings":
        problems: list[str] = []
        if len(self.jwt_secret_key) < 32:
            problems.append(
                "JWT_SECRET_KEY must be at least 32 characters. Generate one with: "
                'python -c "import secrets;print(secrets.token_urlsafe(48))"'
            )
        if len(self.neo4j_password) < 12:
            problems.append("NEO4J_PASSWORD must be at least 12 characters.")
        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            problems.append("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic (or set LLM_PROVIDER=none).")
        if self.llm_provider == "groq" and not self.groq_api_key:
            problems.append("GROQ_API_KEY is required when LLM_PROVIDER=groq (or set LLM_PROVIDER=none).")
        if problems:
            raise ConfigError("Unsafe or incomplete configuration (SEC-10):\n- " + "\n- ".join(problems))
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def max_resume_bytes(self) -> int:
        return self.max_resume_mb * 1024 * 1024

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
