"""Semantic retrieval from Qdrant."""
import logging

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.core.config import Settings
from app.core.errors import AppError
from app.prompts import RetrievedChunk

logger = logging.getLogger("app.retrieval")


async def retrieve_chunks(query: str, *, qdrant: AsyncQdrantClient, embedder, settings: Settings) -> list[RetrievedChunk]:
    """Embed the query, search Qdrant (public scope only) and drop chunks below the score threshold."""
    vectors = await embedder.embed([query])  # AppError propagates (503)
    try:
        res = await qdrant.query_points(
            collection_name=settings.qdrant_collection,
            query=vectors[0],
            limit=settings.rag_top_k,
            score_threshold=settings.rag_score_threshold,
            query_filter=Filter(must=[FieldCondition(key="access_scope", match=MatchValue(value="public"))]),
            with_payload=True,
        )
    except Exception as exc:
        logger.error("Qdrant query failed: %s", type(exc).__name__)
        raise AppError(503, "knowledge_base_unavailable", "The knowledge base is temporarily unavailable. Your message is saved - please retry.") from exc

    chunks: list[RetrievedChunk] = []
    for p in res.points:
        payload = p.payload or {}
        if not payload.get("text"):
            continue
        chunks.append(
            RetrievedChunk(
                text=payload["text"],
                document_id=str(payload.get("document_id", "")),
                chunk_id=str(payload.get("chunk_id", "")),
                source=str(payload.get("source", "knowledge base")),
                score=float(p.score),
            )
        )
    return chunks
