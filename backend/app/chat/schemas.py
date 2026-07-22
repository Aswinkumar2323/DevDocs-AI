from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Request ───────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The user's question")
    conversation_id: Optional[str] = Field(
        None, description="Existing conversation ID for multi-turn chat"
    )


class ConversationUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


# ── Response building blocks ──────────────────────────────────────────


class Citation(BaseModel):
    source_name: Optional[str] = None
    page_title: Optional[str] = None
    page_url: str
    heading: Optional[str] = None
    content_snippet: str = ""


class RetrievedChunkDetail(BaseModel):
    content: str
    page_title: Optional[str] = None
    page_url: str = ""
    heading: Optional[str] = None
    similarity_score: float = 0.0
    chunk_index: int = 0
    token_count: int = 0


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


# ── Top-level responses ──────────────────────────────────────────────


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = []
    retrieved_chunks: list[RetrievedChunkDetail] = []
    conversation_id: str
    usage: TokenUsage = TokenUsage()


class MessageSchema(BaseModel):
    id: int
    role: str
    content: str
    citations: list[Citation] = []
    retrieved_chunks: list[RetrievedChunkDetail] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationSummary(BaseModel):
    id: str
    title: str
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetail(BaseModel):
    id: str
    title: str
    messages: list[MessageSchema] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
