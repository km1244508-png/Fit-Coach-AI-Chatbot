"""Pydantic models for conversations and messages."""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.core.config import get_settings
from app.core.timeutil import as_utc


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=100)

    @field_validator("title")
    @classmethod
    def _clean(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = " ".join(v.split())
        return v or None


class ConversationRename(BaseModel):
    title: str = Field(min_length=1, max_length=100)

    @field_validator("title")
    @classmethod
    def _clean(cls, v: str) -> str:
        v = " ".join(v.split())
        if not v:
            raise ValueError("Title cannot be empty")
        return v


class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime

    @classmethod
    def from_doc(cls, d: dict) -> "ConversationOut":
        return cls(
            id=str(d["_id"]),
            title=d["title"],
            created_at=as_utc(d["created_at"]),
            updated_at=as_utc(d["updated_at"]),
            last_message_at=as_utc(d["last_message_at"]),
        )


class ConversationListOut(BaseModel):
    items: list[ConversationOut]
    total: int
    limit: int
    skip: int


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime
    metadata: dict[str, Any] | None = None

    @classmethod
    def from_doc(cls, d: dict) -> "MessageOut":
        return cls(
            id=str(d["_id"]),
            conversation_id=str(d["conversation_id"]),
            role=d["role"],
            content=d["content"],
            created_at=as_utc(d["created_at"]),
            metadata=d.get("metadata"),
        )


class ConversationDetailOut(BaseModel):
    conversation: ConversationOut
    messages: list[MessageOut]
    has_more: bool = Field(description="True if older messages exist before the first returned message")


class MessageCreate(BaseModel):
    content: str
    retry_message_id: str | None = Field(
        default=None,
        description="ID of an already-saved user message whose assistant reply failed; regenerates without duplicating it.",
    )

    @field_validator("content")
    @classmethod
    def _check_content(cls, v: str) -> str:
        v = v.strip()
        limit = get_settings().max_message_length
        if not v:
            raise ValueError("Message cannot be empty")
        if len(v) > limit:
            raise ValueError(f"Message is too long (max {limit} characters)")
        return v


class ChatResponse(BaseModel):
    user_message: MessageOut
    assistant_message: MessageOut
    conversation: ConversationOut
