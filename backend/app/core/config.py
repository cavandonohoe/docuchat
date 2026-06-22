"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    cors_origins: str = "http://localhost:3000"

    database_url: str = Field(
        default="postgresql+psycopg://docuchat:docuchat@localhost:5432/docuchat"
    )

    openai_api_key: str = "sk-replace-me"
    openai_base_url: str | None = None
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536
    chat_model: str = "gpt-4o-mini"

    chunk_size: int = 800
    chunk_overlap: int = 120
    top_k: int = 5

    upload_dir: str = "/data/uploads"
    max_upload_mb: int = 25

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
