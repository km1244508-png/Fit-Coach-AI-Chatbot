"""Orchestrates one chat turn: save user msg -> retrieve -> generate -> save assistant msg."""

from app.core.config import Settings
from app.core.errors import AppError
from app.core.timeutil import as_utc
from app.prompts import build_system_message
from app.schemas.conversation import MessageOut
from app.services import conversation_service as cs
from app.services.retrieval_service import retrieve_chunks


async def _get_retry_target(db, conversation: dict, message_id: str) -> dict:
    """A retry is only valid for the latest message, if it is a user message with no reply yet."""
    mid = cs.parse_object_id(message_id, "Message")
    msg = await db.messages.find_one({"_id": mid, "conversation_id": conversation["_id"], "user_id": conversation["user_id"]})
    if not msg or msg["role"] != "user":
        raise AppError(404, "not_found", "Message not found")
    latest = await cs.recent_messages(db, conversation, 1)
    if not latest or latest[0]["_id"] != msg["_id"]:
        raise AppError(409, "already_answered", "This message already has a reply.")
    return msg


async def run_chat_turn(db, *, user: dict, conversation_id: str, content: str, retry_message_id: str | None,
                        settings: Settings, qdrant, embedder, llm) -> tuple[dict, dict, dict]:
    conversation = await cs.get_owned_conversation(db, user["_id"], conversation_id)

    # 1) Persist the user's message first, so an LLM/Qdrant failure never loses it.
    if retry_message_id:
        user_msg = await _get_retry_target(db, conversation, retry_message_id)
        content = user_msg["content"]
    else:
        is_first = await db.messages.find_one({"conversation_id": conversation["_id"]}, {"_id": 1}) is None
        user_msg = await cs.add_message(db, conversation, "user", content)
        title = cs.make_title(content) if is_first and not conversation.get("title_locked") else None
        conversation = await cs.touch_conversation(db, conversation, user_msg["created_at"], title)

    # 2) Retrieve + generate. On failure keep the saved user message and tell the client to offer "Retry".
    try:
        chunks = await retrieve_chunks(content, qdrant=qdrant, embedder=embedder, settings=settings)
        history = await cs.recent_messages(db, conversation, settings.history_context_messages)
        llm_messages = [{"role": m["role"], "content": m["content"]} for m in history if m["role"] in ("user", "assistant")]
        answer = await llm.generate(build_system_message(chunks), llm_messages)
    except AppError as exc:
        raise AppError(
            exc.status_code, exc.code, exc.message,
            {**exc.extra, "user_message": MessageOut.from_doc(user_msg).model_dump(mode="json")},
        ) from exc

    # 3) Persist the assistant answer (only real model output is ever saved).
    metadata = {
        "retrieval": {"used": bool(chunks), "sources": [c.to_metadata() for c in chunks]},
        "model": getattr(llm, "model", settings.llm_model),
    }
    assistant_msg = await cs.add_message(db, conversation, "assistant", answer, metadata)
    # Guarantee strictly later activity than the user message.
    when = max(as_utc(assistant_msg["created_at"]), as_utc(user_msg["created_at"]))
    conversation = await cs.touch_conversation(db, conversation, when)
    return user_msg, assistant_msg, conversation
