"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the e-SewaSathi backend."""

    app_name: str = "e-SewaSathi"
    api_prefix: str = "/api"
    environment: str = "development"
    demo_mode: bool = True
    debug: bool = False

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "e_sewasathi"

    jwt_secret: str = "dev-only-secret-change-me-please-use-openssl-rand-hex-32"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    upload_dir: str = "../private_uploads"
    max_file_size_mb: int = 5
    allowed_mime_types: tuple[str, ...] = ("application/pdf", "image/jpeg", "image/png")

    bcrypt_rounds: int = 12

    # Phase 2 - agent / LLM
    llm_provider: str = "demo"  # demo | ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    chat_history_limit: int = 60

    # Phase 2 - OCR
    ocr_provider: str = "demo"  # demo | paddle
    ocr_confidence_threshold: float = 0.75

    # Phase 2 - mock government portal
    portal_mode: str = "api"  # api | playwright
    portal_base_url: str = "http://localhost:8001"
    portal_api_token: str = ""
    portal_timeout_seconds: float = 10.0

    # Phase 2 - workflow
    workflow_max_retries: int = 1
    workflow_recursion_limit: int = 50

    # Phase 2 - realtime / voice
    realtime_enabled: bool = True
    voice_enabled: bool = True

    # Phase 2 - privacy
    encryption_key: str = "dev-only-encryption-key-change-me-32bytes"
    max_request_body_kb: int = 2048

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("allowed_mime_types", mode="before")
    @classmethod
    def _split_mime_types(cls, value: object) -> object:
        if isinstance(value, str):
            return tuple(item.strip() for item in value.split(",") if item.strip())
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        """CORS origins parsed from the comma separated environment value."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
