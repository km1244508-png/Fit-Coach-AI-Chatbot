"""Conversation + message persistence. Every query is scoped to the owning user."""
import re

from bson import ObjectId

from app.core.errors import not_found
from app.core.timeutil import utcnow

DEFAULT_TITLE = "New Chat"
TITLE_MAX = 50


def parse_object_id(value: str, what: str = "Resource") -> ObjectId:
    """Validate IDs before touching the DB; invalid IDs look exactly like missing ones (404)."""
    if not isinstance(value, str) or len(value) != 24 or not ObjectId.is_valid(value):
        raise not_found(what)
    return ObjectId(value)


def make_title(text: str) -> str:
    """Short title from the first user message (safe truncated fallback)."""
    t = re.sub(r"```.*?```", " ", text, flags=re.S)
    t = re.sub(r"[#>*_`~\[\]]+", " ", t)
    t = " ".join(t.split())
    if not t:
        return DEFAULT_TITLE
    if len(t) <= TITLE_MAX:
        return t[0].upper() + t[1:]
    cut = t[:TITLE_MAX].rsplit(" ", 1)[0] or t[:TITLE_MAX]
    cut = cut.rstrip(" ,.;:!?-")
    return (cut[0].upper() + cut[1:]) + "…"


async def create_conversation(db, user_id: ObjectId, title: str | None = None) -> dict:
    now = utcnow()
    doc = {
        "user_id": user_id,
        "title": title or DEFAULT_TITLE,
        "title_locked": bool(title),  # a user-chosen title is never auto-overwritten
        "created_at": now,
        "updated_at": now,
        "last_message_at": now,
        "metadata": {},
    }
    res = await db.conversations.insert_one(doc)
    doc["_id"] = res.inserted_id
    return doc


async def get_owned_conversation(db, user_id: ObjectId, conversation_id: str) -> dict:
    cid = parse_object_id(conversation_id, "Conversation")
    doc = await db.conversations.find_one({"_id": cid, "user_id": user_id})
    if not doc:
        raise not_found("Conversation")
    return doc


async def list_conversations(db, user_id: ObjectId, limit: int, skip: int) -> tuple[list[dict], int]:
    total = await db.conversations.count_documents({"user_id": user_id})
    cursor = db.conversations.find({"user_id": user_id}).sort("last_message_at", -1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit), total


async def rename_conversation(db, user_id: ObjectId, conversation_id: str, title: str) -> dict:
    cid = parse_object_id(conversation_id, "Conversation")
    doc = await db.conversations.find_one_and_update(
        {"_id": cid, "user_id": user_id},
        {"$set": {"title": title, "title_locked": True, "updated_at": utcnow()}},
        return_document=True,
    )
    if not doc:
        raise not_found("Conversation")
    return doc


async def delete_conversation(db, user_id: ObjectId, conversation_id: str) -> None:
    cid = parse_object_id(conversation_id, "Conversation")
    res = await db.conversations.delete_one({"_id": cid, "user_id": user_id})
    if res.deleted_count == 0:
        raise not_found("Conversation")
    await db.messages.delete_many({"conversation_id": cid, "user_id": user_id})


async def list_messages(db, user_id: ObjectId, conversation_id: ObjectId, limit: int, before: str | None = None) -> tuple[list[dict], bool]:
    """Newest `limit` messages (optionally older than cursor `before`), returned oldest -> newest."""
    query: dict = {"conversation_id": conversation_id, "user_id": user_id}
    if before:
        bid = parse_object_id(before, "Message")
        ref = await db.messages.find_one({"_id": bid, "conversation_id": conversation_id, "user_id": user_id})
        if not ref:
            raise not_found("Message")
        query["$or"] = [
            {"created_at": {"$lt": ref["created_at"]}},
            {"created_at": ref["created_at"], "_id": {"$lt": ref["_id"]}},
        ]
    cursor = db.messages.find(query).sort([("created_at", -1), ("_id", -1)]).limit(limit + 1)
    rows = await cursor.to_list(length=limit + 1)
    has_more = len(rows) > limit
    rows = rows[:limit]
    rows.reverse()
    return rows, has_more


async def add_message(db, conversation: dict, role: str, content: str, metadata: dict | None = None) -> dict:
    doc = {
        "conversation_id": conversation["_id"],
        "user_id": conversation["user_id"],
        "role": role,
        "content": content,
        "created_at": utcnow(),
        "metadata": metadata,
    }
    res = await db.messages.insert_one(doc)
    doc["_id"] = res.inserted_id
    return doc


async def touch_conversation(db, conversation: dict, when, title: str | None = None) -> dict:
    """Move activity forward (drives 'Today / Yesterday' grouping). Returns the fresh document."""
    update = {"last_message_at": when, "updated_at": when}
    if title:
        update["title"] = title
    doc = await db.conversations.find_one_and_update(
        {"_id": conversation["_id"], "user_id": conversation["user_id"]}, {"$set": update}, return_document=True
    )
    return doc or {**conversation, **update}


async def recent_messages(db, conversation: dict, limit: int) -> list[dict]:
    cursor = db.messages.find({"conversation_id": conversation["_id"], "user_id": conversation["user_id"]}).sort(
        [("created_at", -1), ("_id", -1)]
    ).limit(limit)
    rows = await cursor.to_list(length=limit)
    rows.reverse()
    return rows
