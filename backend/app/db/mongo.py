"""MongoDB connection (PyMongo async driver) and index creation."""
from pymongo import ASCENDING, AsyncMongoClient, DESCENDING
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import get_settings

_client: AsyncMongoClient | None = None


def get_client() -> AsyncMongoClient:
    global _client
    if _client is None:
        s = get_settings()
        _client = AsyncMongoClient(s.mongodb_uri, tz_aware=True, serverSelectionTimeoutMS=5000)
    return _client


def get_db() -> AsyncDatabase:
    """FastAPI dependency (overridden in tests)."""
    return get_client()[get_settings().mongodb_db_name]


async def init_indexes(db) -> None:
    """Indexes required by the brief + token revocation TTL."""
    await db.users.create_index([("email", ASCENDING)], unique=True, name="uniq_email")
    await db.conversations.create_index([("user_id", ASCENDING), ("last_message_at", DESCENDING)], name="user_last_message")
    await db.messages.create_index([("conversation_id", ASCENDING), ("created_at", ASCENDING)], name="conv_created")
    await db.revoked_tokens.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0, name="ttl_expires")


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None
