"""LLM provider (OpenAI-compatible chat completions)."""
import logging
from functools import lru_cache

from openai import AsyncOpenAI

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.services.embedding_service import make_client

logger = logging.getLogger("app.llm")


class LLMService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: AsyncOpenAI | None = None

    @property
    def model(self) -> str:
        return self.settings.llm_model

    async def generate(self, system_prompt: str, messages: list[dict]) -> str:
        if self._client is None:
            self._client = make_client(self.settings)
        try:
            resp = await self._client.chat.completions.create(
                model=self.settings.llm_model,
                temperature=self.settings.llm_temperature,
                messages=[{"role": "system", "content": system_prompt}, *messages],
            )
        except AppError:
            raise
        except Exception as exc:  # network, rate limit, auth, timeout ...
            logger.error("LLM request failed: %s", type(exc).__name__)
            raise AppError(502, "llm_unavailable", "The AI coach couldn't respond right now. Your message is saved - please retry.") from exc
        text = (resp.choices[0].message.content or "").strip() if resp.choices else ""
        if not text:
            raise AppError(502, "llm_empty", "The AI coach returned an empty answer. Your message is saved - please retry.")
        return text


@lru_cache
def get_llm_service() -> LLMService:
    """FastAPI dependency (overridden in tests)."""
    return LLMService(get_settings())
