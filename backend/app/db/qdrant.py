"""Qdrant client and collection setup."""
import logging
from functools import lru_cache

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PayloadSchemaType, VectorParams

from app.core.config import Settings, get_settings

logger = logging.getLogger("app.qdrant")


@lru_cache
def get_qdrant() -> AsyncQdrantClient:
    """FastAPI dependency (overridden in tests)."""
    s = get_settings()
    return AsyncQdrantClient(url=s.qdrant_url, api_key=s.qdrant_api_key, timeout=15)


async def ensure_collection(client: AsyncQdrantClient, settings: Settings, recreate: bool = False) -> None:
    """Create the knowledge-base collection (cosine, EMBEDDING_DIM) if missing; verify dimension if present."""
    name = settings.qdrant_collection
    exists = await client.collection_exists(name)
    if exists and recreate:
        await client.delete_collection(name)
        exists = False
    if exists:
        info = await client.get_collection(name)
        vectors = info.config.params.vectors
        size = getattr(vectors, "size", None)
        if size is not None and size != settings.embedding_dim:
            raise RuntimeError(
                f"Qdrant collection '{name}' has dimension {size} but EMBEDDING_DIM={settings.embedding_dim}. "
                "Use the same embedding model for indexing and querying (re-run ingest with --recreate)."
            )
        return
    await client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=settings.embedding_dim, distance=Distance.COSINE),
    )
    await client.create_payload_index(name, field_name="access_scope", field_schema=PayloadSchemaType.KEYWORD)
    logger.info("Created Qdrant collection %s (dim=%s)", name, settings.embedding_dim)


async def close_qdrant() -> None:
    if get_qdrant.cache_info().currsize:
        await get_qdrant().close()
        get_qdrant.cache_clear()
