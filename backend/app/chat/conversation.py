import json
import logging
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.chat.models import Conversation, Message
from app.chat.schemas import Citation, RetrievedChunkDetail

logger = logging.getLogger(__name__)


def create_conversation(db: Session, title: str = "New Conversation") -> Conversation:
    conversation = Conversation(title=title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    logger.info("Created conversation %s: %s", conversation.id, title)
    return conversation


def get_conversation(db: Session, conversation_id: str) -> Optional[Conversation]:
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()


def list_conversations(db: Session) -> list[dict]:
    results = (
        db.query(
            Conversation,
            func.count(Message.id).label("message_count"),
        )
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .group_by(Conversation.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )

    conversations = []
    for conv, msg_count in results:
        conversations.append({
            "id": conv.id,
            "title": conv.title,
            "message_count": msg_count,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
        })

    return conversations


def update_conversation(
    db: Session, conversation_id: str, title: str
) -> Optional[Conversation]:
    conversation = get_conversation(db, conversation_id)
    if not conversation:
        return None

    conversation.title = title
    db.commit()
    db.refresh(conversation)
    logger.info("Renamed conversation %s → %s", conversation_id, title)
    return conversation


def delete_conversation(db: Session, conversation_id: str) -> bool:
    conversation = get_conversation(db, conversation_id)
    if not conversation:
        return False

    db.delete(conversation)
    db.commit()
    logger.info("Deleted conversation %s", conversation_id)
    return True


def add_message(
    db: Session,
    conversation_id: str,
    role: str,
    content: str,
    citations: list[Citation] | None = None,
    retrieved_chunks: list[RetrievedChunkDetail] | None = None,
) -> Message:
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        citations_json=(
            json.dumps([c.model_dump() for c in citations]) if citations else None
        ),
        retrieved_chunks_json=(
            json.dumps([c.model_dump() for c in retrieved_chunks])
            if retrieved_chunks
            else None
        ),
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_history(
    db: Session,
    conversation_id: str,
    limit: int = 20,
) -> list[dict[str, str]]:
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )

    # Reverse to chronological order
    messages.reverse()

    return [{"role": msg.role, "content": msg.content} for msg in messages]


def generate_title(first_message: str) -> str:
    title = first_message.strip()

    # Remove leading question markers
    for prefix in ["how ", "what ", "why ", "when ", "where ", "can ", "does "]:
        if title.lower().startswith(prefix):
            break

    # Truncate to 60 chars and add ellipsis if needed
    if len(title) > 60:
        title = title[:57] + "..."

    return title or "New Conversation"
