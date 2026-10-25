"""Knowledge-base chunking + indexing into Qdrant (same embedding model as query time)."""
import re
import uuid
from pathlib import Path

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct

from app.core.config import Settings

MAX_CHUNK_CHARS = 900
BATCH = 32
_NAMESPACE = uuid.UUID("6f1d3a52-8c1e-4d1f-9a54-0f6c7b1c2e10")


def chunk_markdown(document_id: str, text: str) -> list[dict]:
    """Split a markdown doc ('# Title' + '## Section' blocks) into small chunks with a context header."""
    lines = text.strip().splitlines()
    title = document_id
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()
        lines = lines[1:]

    sections: list[tuple[str, list[str]]] = []
    heading, body = "Overview", []
    for line in lines:
        if line.startswith("## "):
            if "".join(body).strip():
                sections.append((heading, body))
            heading, body = line[3:].strip(), []
        else:
            body.append(line)
    if "".join(body).strip():
        sections.append((heading, body))

    chunks: list[dict] = []
    for heading, body_lines in sections:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", "\n".join(body_lines)) if p.strip()]
        current = ""
        pieces: list[str] = []
        for para in paragraphs:
            if current and len(current) + len(para) + 1 > MAX_CHUNK_CHARS:
                pieces.append(current)
                current = para
            else:
                current = f"{current}\n{para}".strip()
        if current:
            pieces.append(current)
        for piece in pieces:
            idx = len(chunks)
            chunks.append(
                {
                    "document_id": document_id,
                    "chunk_id": f"{document_id}-{idx}",
                    "source": title,
                    "text": f"{title} - {heading}\n{piece}",
                }
            )
    return chunks


def load_directory(directory: Path) -> list[dict]:
    chunks: list[dict] = []
    for path in sorted(directory.glob("*.md")):
        chunks.extend(chunk_markdown(path.stem, path.read_text(encoding="utf-8")))
    return chunks


async def ingest_directory(client: AsyncQdrantClient, embedder, settings: Settings, directory: Path) -> int:
    """Idempotent upsert: point IDs are derived from chunk_id, so re-running never duplicates."""
    chunks = load_directory(directory)
    for i in range(0, len(chunks), BATCH):
        batch = chunks[i : i + BATCH]
        vectors = await embedder.embed([c["text"] for c in batch])
        points = [
            PointStruct(
                id=str(uuid.uuid5(_NAMESPACE, c["chunk_id"])),
                vector=vec,
                payload={**c, "access_scope": "public"},
            )
            for c, vec in zip(batch, vectors)
        ]
        await client.upsert(collection_name=settings.qdrant_collection, points=points, wait=True)
    return len(chunks)
