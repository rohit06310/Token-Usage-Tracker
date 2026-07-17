"""
Application configuration — loads all settings from environment variables.
Uses Pydantic BaseSettings so values can come from .env or shell environment.
"""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All application configuration is centralised here.
    Secrets are NEVER hardcoded — they must be provided via environment.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------ App --
    app_name: str = "Unified AI Usage Dashboard"
    app_version: str = "0.2.0"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"

    # --------------------------------------------------------------- Database --
    database_url: str
    # SQLAlchemy pool settings — sensible defaults for Supabase direct conn.
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800  # 30 min — avoids Supabase idle timeout

    # ------------------------------------------------------------- Encryption --
    # Fernet key (URL-safe base64-encoded 32-byte key).
    # Generate with: python scripts/generate_keys.py
    fernet_key: str

    # ------------------------------------------------------- Dashboard Auth --
    # Raw API key for accessing this dashboard's own endpoints. (Legacy Phase 1-4 auth)
    dashboard_api_key: str | None = None
    
    # JWT authentication settings.
    # MUST be overridden in production — generate with: python -c "import secrets; print(secrets.token_hex(32))"
    secret_key: str = "changethisinsigningkeyinproductionorusefernetkey"
    access_token_expire_minutes: int = 1440  # 24 hours

    _INSECURE_SECRET = "changethisinsigningkeyinproductionorusefernetkey"

    # ---------------------------------------------------- Provider API Keys --
    # These are optional at startup — only required when the specific adapter is used.
    # Store provider keys here OR use the encrypted api_keys table (preferred for
    # multi-key / multi-project setups). These env-based keys are a convenience
    # for single-project use without hitting the DB.
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    groq_api_key: str | None = None
    gemini_api_key: str | None = None

    # --------------------------------------------------------------- CORS --
    allowed_origins: str | list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ----------------------------------------------------------- Scheduler & Alerts --
    scheduler_enabled: bool = True
    # How often to fetch provider-reported usage (in hours)
    usage_fetch_interval_hours: int = 6
    # Max age (days) of usage reports to fetch on initial sync
    usage_initial_lookback_days: int = 7
    # Generic webhook for alert dispatches
    generic_webhook_url: str | None = None

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: str | list[str]) -> list[str]:
        """Accept comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("fernet_key")
    @classmethod
    def validate_fernet_key(cls, v: str) -> str:
        import base64
        try:
            decoded = base64.urlsafe_b64decode(v.encode())
            if len(decoded) != 32:
                raise ValueError("Fernet key must decode to exactly 32 bytes.")
        except Exception as e:
            raise ValueError(f"Invalid FERNET_KEY: {e}") from e
        return v

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        insecure = "changethisinsigningkeyinproductionorusefernetkey"
        if v == insecure:
            env = info.data.get("app_env", "development")
            if env in ("production", "staging"):
                raise ValueError(
                    "SECRET_KEY must be changed before deploying to production or staging. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
                )
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached Settings instance.
    The lru_cache ensures the .env file is parsed only once.
    """
    return Settings()
