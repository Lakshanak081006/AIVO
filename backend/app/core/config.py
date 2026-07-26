from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed application settings.

    SQLite is the zero-setup local default. Docker Compose overrides this with
    PostgreSQL, so the same application can be used for a quick demo or a full
    deployment.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "Autonomous Personal Assistant"
    APP_VERSION: str = "16.0.0"
    APP_ENV: Literal["development", "testing", "production"] = "development"
    DEBUG: bool = True
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = Field(default=8000, ge=1, le=65535)
    API_V1_PREFIX: str = "/api"

    DATABASE_URL: str = "sqlite:///./assistant.db"
    AUTO_CREATE_DB: bool = True

    JWT_SECRET_KEY: str = "change-this-secret-before-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=120, ge=1, le=10080)

    FRONTEND_URL: str = "http://localhost:5173"
    LLM_PROVIDER: Literal["none", "gemini", "openai"] = "none"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""

    MAX_TOOL_RETRIES: int = Field(default=3, ge=0, le=10)
    RETRY_BASE_DELAY_SECONDS: float = Field(default=0.1, ge=0, le=60)
    DEMONSTRATION_MODE: bool = True
    LOG_LEVEL: str = "INFO"

    DEMO_USER_EMAIL: str = "demo@example.com"
    DEMO_USER_PASSWORD: str = "Demo@12345"
    DEMO_USER_NAME: str = "Demo User"

    # Lyzr Studio integration
    LYZR_ENABLED: bool = False
    LYZR_API_KEY: str = ""
    LYZR_AGENT_ID: str = "6a645e3294689fab2dee8010"
    LYZR_BASE_URL: str = "https://agent-prod.studio.lyzr.ai"
    LYZR_CHAT_ENDPOINT: str = "/v3/inference/chat/"
    LYZR_TIMEOUT_SECONDS: int = Field(default=60, ge=5, le=300)

    @property
    def lyzr_chat_url(self) -> str:
        return self.LYZR_BASE_URL.rstrip("/") + "/" + self.LYZR_CHAT_ENDPOINT.lstrip("/")

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).lower() in {"1", "true", "yes", "on"}

    @field_validator("LYZR_ENABLED", mode="before")
    @classmethod
    def parse_lyzr_enabled(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).lower() in {"1", "true", "yes", "on"}

    @field_validator("API_V1_PREFIX")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith("/"):
            value = f"/{value}"
        return value.rstrip("/") or "/api"

    @field_validator("LOG_LEVEL")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        normalized = value.upper().strip()
        return normalized if normalized in allowed else "INFO"

    @property
    def cors_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.FRONTEND_URL.split(",") if origin.strip()]
        # In development, also allow common localhost variants and dev ports
        # so the frontend dev server (which may use a different port) is not blocked.
        if self.APP_ENV == "development":
            dev_origins = [
                "http://localhost:5173", "http://127.0.0.1:5173",
                "http://localhost:5174", "http://127.0.0.1:5174",
                "http://localhost:5175", "http://127.0.0.1:5175",
                "http://localhost:5176", "http://127.0.0.1:5176",
                "http://localhost:3000", "http://127.0.0.1:3000",
                "http://localhost:8080", "http://127.0.0.1:8080",
            ]
            for o in dev_origins:
                if o not in origins:
                    origins.append(o)
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
