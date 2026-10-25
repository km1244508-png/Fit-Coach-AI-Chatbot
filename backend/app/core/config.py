"""Environment-based settings. All secrets come from env vars / .env (never hard-coded)."""
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App / auth
    environment: str = "development"
    secret_key: str = Field(min_length=32)
    access_token_expire_minutes: int = Field(default=720, ge=5, le=60 * 24 * 30)
    cookie_name: str = "access_token"
    cookie_samesite: str = "lax"
    cookie_secure: bool | None = None  # None -> secure only in production
    cors_origins: str = "http://localhost:5173"
    bcrypt_rounds: int = Field(default=12, ge=4, le=16)

    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "health_coach"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "health_fitness_kb"

    # LLM / embeddings (OpenAI-compatible)
    openai_api_key: str = ""
    openai_base_url: str | None = None
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.4
    llm_timeout_seconds: float = 60.0
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = Field(default=1536, ge=8)

    # RAG / chat
    rag_top_k: int = Field(default=4, ge=1, le=20)
    rag_score_threshold: float = 0.30
    max_message_length: int = Field(default=4000, ge=10, le=20000)
    history_context_messages: int = Field(default=12, ge=1, le=50)

    @field_validator("qdrant_api_key", "openai_base_url", "cookie_secure", mode="before")
    @classmethod
    def _empty_to_none(cls, v):
        # `KEY=` in a .env file arrives as "" -> treat as "not set".
        return None if isinstance(v, str) and v.strip() == "" else v

    @field_validator("cookie_samesite")
    @classmethod
    def _check_samesite(cls, v: str) -> str:
        v = v.lower()
        if v not in {"lax", "strict", "none"}:
            raise ValueError("COOKIE_SAMESITE must be lax, strict or none")
        return v

    @model_validator(mode="after")
    def _check_production(self):
        if self.environment == "production" and self.secret_key.startswith("replace-with"):
            raise ValueError("Set a real SECRET_KEY before running in production")
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cookie_secure_effective(self) -> bool:
        if self.cookie_secure is not None:
            return bool(self.cookie_secure)
        return self.is_production or self.cookie_samesite == "none"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
