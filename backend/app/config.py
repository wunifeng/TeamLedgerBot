"""Application configuration using Pydantic BaseSettings."""
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str

    # ── Telegram ──────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: str

    # ── Application ───────────────────────────────────────────
    APP_ENV: str = "development"
    # NOTE: pydantic-settings v2 JSON-parses List[str] fields before validators run.
    # Store as plain str and expose as list via property to avoid parse errors.
    CORS_ORIGINS: str = "http://localhost:3000"
    TIMEZONE: str = "Asia/Bangkok"

    # ── Risk Alert Thresholds ─────────────────────────────────
    RISK_HIGH_AMOUNT_THRESHOLD: float = 10_000.0
    RISK_DUPLICATE_WINDOW_SECONDS: int = 300
    RISK_FREQUENCY_LIMIT: int = 5
    RISK_FREQUENCY_WINDOW_SECONDS: int = 600

    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS_ORIGINS as a list, supporting comma-separated values."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
