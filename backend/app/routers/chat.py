"""Send a message: save -> retrieve (Qdrant) -> generate -> save."""
from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.db.mongo import get_db
from app.db.qdrant import get_qdrant
from app.deps import get_current_user
from app.schemas.conversation import ChatResponse, ConversationOut, MessageCreate, MessageOut
from app.services.chat_service import run_chat_turn
from app.services.embedding_service import get_embedding_service
from app.services.llm_service import get_llm_service

router = APIRouter(prefix="/api/conversations", tags=["chat"])


@router.post("/{conversation_id}/messages", response_model=ChatResponse, status_code=201)
async def send_message(
    conversation_id: str,
    payload: MessageCreate,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
    settings: Settings = Depends(get_settings),
    qdrant=Depends(get_qdrant),
    embedder=Depends(get_embedding_service),
    llm=Depends(get_llm_service),
):
    user_msg, assistant_msg, conversation = await run_chat_turn(
        db, user=user, conversation_id=conversation_id, content=payload.content, retry_message_id=payload.retry_message_id,
        settings=settings, qdrant=qdrant, embedder=embedder, llm=llm,
    )
    return ChatResponse(
        user_message=MessageOut.from_doc(user_msg),
        assistant_message=MessageOut.from_doc(assistant_msg),
        conversation=ConversationOut.from_doc(conversation),
    )
