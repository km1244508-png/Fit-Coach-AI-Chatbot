"""Conversation CRUD. All routes require auth and are scoped to the current user."""
from fastapi import APIRouter, Depends, Query, Response

from app.db.mongo import get_db
from app.deps import get_current_user
from app.schemas.conversation import (
    ConversationCreate, ConversationDetailOut, ConversationListOut, ConversationOut, ConversationRename, MessageOut,
)
from app.services import conversation_service as cs

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("", response_model=ConversationOut, status_code=201)
async def create_conversation(payload: ConversationCreate | None = None, user: dict = Depends(get_current_user), db=Depends(get_db)):
    doc = await cs.create_conversation(db, user["_id"], payload.title if payload else None)
    return ConversationOut.from_doc(doc)


@router.get("", response_model=ConversationListOut)
async def list_conversations(
    limit: int = Query(50, ge=1, le=100), skip: int = Query(0, ge=0, le=100_000),
    user: dict = Depends(get_current_user), db=Depends(get_db),
):
    docs, total = await cs.list_conversations(db, user["_id"], limit, skip)
    return ConversationListOut(items=[ConversationOut.from_doc(d) for d in docs], total=total, limit=limit, skip=skip)


@router.get("/{conversation_id}", response_model=ConversationDetailOut)
async def get_conversation(
    conversation_id: str,
    limit: int = Query(100, ge=1, le=200),
    before: str | None = Query(None, description="Message ID cursor: return messages older than this one"),
    user: dict = Depends(get_current_user), db=Depends(get_db),
):
    conv = await cs.get_owned_conversation(db, user["_id"], conversation_id)
    rows, has_more = await cs.list_messages(db, user["_id"], conv["_id"], limit, before)
    return ConversationDetailOut(conversation=ConversationOut.from_doc(conv), messages=[MessageOut.from_doc(r) for r in rows], has_more=has_more)


@router.patch("/{conversation_id}", response_model=ConversationOut)
async def rename_conversation(conversation_id: str, payload: ConversationRename, user: dict = Depends(get_current_user), db=Depends(get_db)):
    doc = await cs.rename_conversation(db, user["_id"], conversation_id, payload.title)
    return ConversationOut.from_doc(doc)


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: str, user: dict = Depends(get_current_user), db=Depends(get_db)):
    await cs.delete_conversation(db, user["_id"], conversation_id)
    return Response(status_code=204)
