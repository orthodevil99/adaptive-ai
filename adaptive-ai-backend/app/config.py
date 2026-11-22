import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

VERSION = "3.0.0"


class Settings(BaseSettings):
    # --- runtime ---------------------------------------------------------
    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    log_json: bool = False
    docs_enabled: bool | None = None  # default: on in dev/test, off in production
    # Deployed frontend is allowed by default so the live Vercel frontend and
    # backend work without env setup; an explicit CORS_ORIGINS env var overrides.
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,https://adaptive-ai-web-xi.vercel.app"
    max_body_bytes: int = Field(default=65536, ge=1024, le=10_000_000)

    # --- access control --------------------------------------------------
    # Comma-separated keys that clients must send as `X-API-Key` or `Authorization: Bearer`.
    # Empty = open (allowed only outside production).
    app_api_keys: SecretStr = SecretStr("")
    rate_limit_per_minute: int = Field(default=120, ge=0, le=100_000)  # all /api/v1 calls; 0 = off
    respond_rate_limit_per_minute: int = Field(default=20, ge=0, le=10_000)  # LLM calls; 0 = off
    trust_proxy: bool = False  # honour X-Forwarded-For for rate limiting

    # --- LLM provider ----------------------------------------------------
    provider: Literal["groq", "mock"] = "groq"
    groq_api_key: SecretStr = SecretStr("")
    groq_model: str = "openai/gpt-oss-120b"
    groq_fallback_model: str = "openai/gpt-oss-20b"  # "" disables fallback
    groq_reasoning: bool = True  # send reasoning_effort to gpt-oss models
    model_timeout_seconds: float = Field(default=60.0, gt=0, le=300)
    max_retries: int = Field(default=2, ge=0, le=5)  # SDK-level retries (429/5xx/network)
    max_concurrent_generations: int = Field(default=4, ge=1, le=64)
    max_output_tokens: int = Field(default=4096, ge=256, le=16384)

    # --- conversation ----------------------------------------------------
    max_request_length: int = Field(default=6000, ge=10, le=50000)
    max_context_messages: int = Field(default=12, ge=0, le=60)
    max_context_chars: int = Field(default=12000, ge=0, le=200_000)

    # --- adaptation / storage -------------------------------------------
    adaptation_mode: Literal["thompson", "greedy", "off"] = "thompson"
    min_feedback_samples: int = Field(default=3, ge=1, le=100)
    # On Vercel the deployment filesystem is read-only; only /tmp is writable,
    # so the default SQLite file must live there or the app crashes at import.
    # An explicit DATABASE_URL env var always overrides this default.
    database_url: str = Field(
        default_factory=lambda: (
            "sqlite:////tmp/adaptive.db" if os.getenv("VERCEL") else "sqlite:///./data/adaptive.db"
        )
    )
    session_ttl_days: int = Field(default=0, ge=0, le=3650)  # 0 = keep forever

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False,
        protected_namespaces=("settings_",),  # allow fields named model_*
    )

    @field_validator("groq_api_key", "app_api_keys", mode="before")
    @classmethod
    def _strip_secret(cls, value: object) -> object:
        if isinstance(value, SecretStr):
            return value
        return str(value or "").strip()

    # ---- derived values -------------------------------------------------
    @property
    def allowed_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def api_key_list(self) -> list[str]:
        raw = self.app_api_keys.get_secret_value()
        return [item.strip() for item in raw.split(",") if item.strip()]

    @property
    def groq_configured(self) -> bool:
        return bool(self.groq_api_key.get_secret_value())

    @property
    def docs_on(self) -> bool:
        if self.docs_enabled is not None:
            return self.docs_enabled
        return self.app_env != "production"

    def check_runtime(self) -> list[str]:
        """Raise on unsafe production config; return non-fatal warnings otherwise."""
        warnings: list[str] = []
        fatal: list[str] = []
        if not self.api_key_list:
            (fatal if self.app_env == "production" else warnings).append(
                "APP_API_KEYS is empty: the API is open to anyone who can reach it."
            )
        if "*" in self.allowed_origins and self.app_env == "production":
            fatal.append("CORS_ORIGINS must list explicit origins in production.")
        if self.provider == "groq" and not self.groq_configured:
            warnings.append("GROQ_API_KEY is not set: /analyze works, /respond returns 503.")
        if fatal:
            raise RuntimeError("Unsafe configuration: " + " ".join(fatal))
        return warnings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
