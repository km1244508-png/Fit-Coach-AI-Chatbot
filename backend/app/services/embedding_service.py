"""Embedding provider (OpenAI-compatible). Same model for indexing and querying."""
import logging
from functools import lru_cache

from openai import AsyncOpenAI

from app.core.config import Settings, get_settings
from app.core.errors import AppError

logger = logging.getLogger("app.embeddings")


def make_client(settings: Settings) -> AsyncOpenAI:
    if not settings.openai_api_key:
        raise AppError(503, "llm_not_configured", "The AI provider is not configured on the server.")
    return AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url, timeout=settings.llm_timeout_seconds, max_retries=1)


class EmbeddingService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: AsyncOpenAI | None = None

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self._client is None:
            self._client = make_client(self.settings)
        kwargs = {"model": self.settings.embedding_model, "input": texts}
        if self.settings.embedding_model.startswith("text-embedding-3"):
            kwargs["dimensions"] = self.settings.embedding_dim
        try:
            resp = await self._client.embeddings.create(**kwargs)
        except AppError:
            raise
        except Exception as exc:
            logger.error("Embedding request failed: %s", type(exc).__name__)
            raise AppError(503, "embedding_unavailable", "The AI service is temporarily unavailable. Please retry.") from exc
        vectors = [list(item.embedding) for item in resp.data]
        if any(len(v) != self.settings.embedding_dim for v in vectors):
            logger.error("Embedding dimension mismatch (expected %s)", self.settings.embedding_dim)
            raise AppError(500, "embedding_dim_mismatch", "Server embedding configuration is invalid.")
        return vectors


@lru_cache
def get_embedding_service() -> EmbeddingService:
    """FastAPI dependency (overridden in tests)."""
    return EmbeddingService(get_settings())
