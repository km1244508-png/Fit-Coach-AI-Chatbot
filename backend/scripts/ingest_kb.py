"""Index the sample knowledge base into Qdrant.

Usage (from backend/):
    python -m scripts.ingest_kb              # create collection if needed + upsert chunks
    python -m scripts.ingest_kb --recreate   # drop and rebuild the collection (e.g. after changing embedding model)
"""
import argparse
import asyncio
from pathlib import Path

from app.core.config import get_settings
from app.db.qdrant import ensure_collection, get_qdrant
from app.services.embedding_service import EmbeddingService
from app.services.kb_ingest import ingest_directory

DEFAULT_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge_base"


async def main(directory: Path, recreate: bool) -> None:
    settings = get_settings()
    client = get_qdrant()
    await ensure_collection(client, settings, recreate=recreate)
    count = await ingest_directory(client, EmbeddingService(settings), settings, directory)
    print(f"Indexed {count} chunks into '{settings.qdrant_collection}' (dim={settings.embedding_dim}).")
    await client.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Index knowledge-base markdown files into Qdrant")
    ap.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    ap.add_argument("--recreate", action="store_true")
    args = ap.parse_args()
    asyncio.run(main(args.dir, args.recreate))
