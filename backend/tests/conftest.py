"""Test fixtures: in-memory MongoDB (mongomock), in-memory Qdrant, fake LLM + fake embeddings."""
import hashlib
import math
import os
import re

# Must be set BEFORE the app/settings are imported.
os.environ.update(
    SECRET_KEY="test-secret-key-" + "x" * 32,
    ENVIRONMENT="test",
    BCRYPT_ROUNDS="4",
    EMBEDDING_DIM="512",
    RAG_SCORE_THRESHOLD="0.15",
    MAX_MESSAGE_LENGTH="500",
    CORS_ORIGINS="http://localhost:5173",
)

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from mongomock_motor import AsyncMongoMockClient  # noqa: E402
from qdrant_client import AsyncQdrantClient  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.errors import AppError  # noqa: E402
from app.db.mongo import get_db, init_indexes  # noqa: E402
from app.db.qdrant import ensure_collection, get_qdrant  # noqa: E402
from app.main import app  # noqa: E402
from app.services.embedding_service import get_embedding_service  # noqa: E402
from app.services.kb_ingest import ingest_directory  # noqa: E402
from app.services.llm_service import get_llm_service  # noqa: E402

settings = get_settings()


class FakeEmbedder:
    """Deterministic bag-of-words hashing embedder (no network)."""

    async def embed(self, texts):
        out = []
        for t in texts:
            v = [0.0] * settings.embedding_dim
            for w in re.findall(r"[a-z]+", t.lower()):
                h = int(hashlib.md5(w.encode()).hexdigest(), 16) % settings.embedding_dim
                v[h] += 1.0
            norm = math.sqrt(sum(x * x for x in v)) or 1.0
            out.append([x / norm for x in v])
        return out


class FakeLLM:
    model = "fake-llm"

    def __init__(self):
        self.calls: list[dict] = []
        self.fail = False

    async def generate(self, system_prompt, messages):
        self.calls.append({"system": system_prompt, "messages": messages})
        if self.fail:
            raise AppError(502, "llm_unavailable", "The AI coach couldn't respond right now. Your message is saved - please retry.")
        return f"Coach reply to: {messages[-1]['content']}"


@pytest_asyncio.fixture
async def db():
    database = AsyncMongoMockClient()["test_db"]
    await init_indexes(database)
    return database


@pytest_asyncio.fixture
async def qdrant(tmp_path):
    client = AsyncQdrantClient(":memory:")
    await ensure_collection(client, settings)
    kb = tmp_path / "kb"
    kb.mkdir()
    (kb / "protein.md").write_text(
        "# Protein Guide\n\n## Daily protein\nProtein intake for muscle gain is about 1.6 grams per kilogram of body weight.\n"
        "Eat protein foods such as eggs and dal.\n",
        encoding="utf-8",
    )
    (kb / "sleep.md").write_text("# Sleep Guide\n\n## Sleep hours\nAdults should sleep seven to nine hours every night.\n", encoding="utf-8")
    await ingest_directory(client, FakeEmbedder(), settings, kb)
    yield client
    await client.close()


@pytest_asyncio.fixture
async def fake_llm():
    return FakeLLM()


@pytest_asyncio.fixture
async def client(db, qdrant, fake_llm):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_qdrant] = lambda: qdrant
    app.dependency_overrides[get_embedding_service] = lambda: FakeEmbedder()
    app.dependency_overrides[get_llm_service] = lambda: fake_llm
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def other_client(client):
    """A second, independent browser session (separate cookie jar) against the same app."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def user_payload(email="alice@example.com", name="Alice Khan", password="Strong123"):
    return {"name": name, "email": email, "password": password, "confirm_password": password}


async def register(c, **kw):
    r = await c.post("/api/auth/register", json=user_payload(**kw))
    assert r.status_code == 201, r.text
    return r.json()["user"]
