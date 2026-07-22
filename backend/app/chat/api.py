import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.chat.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationSummary,
    ConversationDetail,
    ConversationUpdate,
    MessageSchema,
    Citation,
    RetrievedChunkDetail,
)
from app.chat.service import process_chat_message
from app.chat import conversation as conv_ops

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def send_chat_message(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        return process_chat_message(db, request)

    except RuntimeError as e:
        logger.error("Chat processing failed: %s", e)
        raise HTTPException(status_code=502, detail=str(e))

    except Exception as e:
        logger.error("Unexpected error in chat: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process chat message")


@router.get("/conversations", response_model=list[ConversationSummary])
def get_conversations(db: Session = Depends(get_db)):
    conversations = conv_ops.list_conversations(db)
    return [ConversationSummary(**c) for c in conversations]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    conversation = conv_ops.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Build message schemas with parsed JSON fields
    messages = []
    for msg in conversation.messages:
        citations = []
        retrieved_chunks = []

        if msg.citations_json:
            try:
                citations = [
                    Citation(**c) for c in json.loads(msg.citations_json)
                ]
            except (json.JSONDecodeError, TypeError):
                pass

        if msg.retrieved_chunks_json:
            try:
                retrieved_chunks = [
                    RetrievedChunkDetail(**c)
                    for c in json.loads(msg.retrieved_chunks_json)
                ]
            except (json.JSONDecodeError, TypeError):
                pass

        messages.append(
            MessageSchema(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                citations=citations,
                retrieved_chunks=retrieved_chunks,
                created_at=msg.created_at,
            )
        )

    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        messages=messages,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.patch("/conversations/{conversation_id}", response_model=ConversationSummary)
def update_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    db: Session = Depends(get_db),
):
    conversation = conv_ops.update_conversation(db, conversation_id, payload.title)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get message count for the response
    message_count = len(conversation.messages) if conversation.messages else 0

    return ConversationSummary(
        id=conversation.id,
        title=conversation.title,
        message_count=message_count,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    deleted = conv_ops.delete_conversation(db, conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"detail": "Conversation deleted"}
