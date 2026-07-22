import logging
from typing import Any

from sqlalchemy.orm import Session

from app.indexing.embeddings import generate_embedding
from app.indexing.search_service import search_hybrid
from app.indexing.vector_store import ensure_collection_exists

from app.chat import conversation as conv_ops
from app.chat.context_builder import build_context
from app.chat.prompt_builder import build_prompt
from app.chat.llm import generate_response
from app.chat.citations import extract_citations
from app.chat.schemas import (
    ChatRequest,
    ChatResponse,
    RetrievedChunkDetail,
    TokenUsage,
)

logger = logging.getLogger(__name__)

# How many raw candidates to fetch before context building
_RETRIEVAL_TOP_K = 20


def process_chat_message(db: Session, request: ChatRequest) -> ChatResponse:
    # ── 1. Conversation ───────────────────────────────────────────────
    if request.conversation_id:
        conversation = conv_ops.get_conversation(db, request.conversation_id)
        if not conversation:
            # If the ID is invalid, start a new conversation
            logger.warning(
                "Conversation %s not found, creating new", request.conversation_id
            )
            title = conv_ops.generate_title(request.message)
            conversation = conv_ops.create_conversation(db, title)
    else:
        title = conv_ops.generate_title(request.message)
        conversation = conv_ops.create_conversation(db, title)

    # ── 2. Save user message ──────────────────────────────────────────
    conv_ops.add_message(db, conversation.id, "user", request.message)

    # ── 3. Conversation history ───────────────────────────────────────
    history = conv_ops.get_history(db, conversation.id)
    # Remove the message we just saved (it'll be the current question)
    if history and history[-1]["role"] == "user":
        history = history[:-1]

    # ── 4. Retrieval ──────────────────────────────────────────────────
    ensure_collection_exists()

    raw_results = search_hybrid(
        query=request.message,
        top_k=_RETRIEVAL_TOP_K,
    )

    logger.info("Retrieved %d raw chunks for query: %s", len(raw_results), request.message[:80])

    # ── 5. Build context ──────────────────────────────────────────────
    context_chunks = build_context(raw_results)

    # Convert to schema objects for the response
    retrieved_chunk_details = [
        RetrievedChunkDetail(
            content=c.get("content", ""),
            page_title=c.get("page_title"),
            page_url=c.get("url", ""),
            heading=c.get("heading"),
            similarity_score=c.get("score", 0.0),
            chunk_index=c.get("chunk_index", 0),
            token_count=c.get("token_count", 0),
        )
        for c in context_chunks
    ]

    # ── 6. Build prompt ───────────────────────────────────────────────
    messages = build_prompt(
        question=request.message,
        context_chunks=context_chunks,
        conversation_history=history if history else None,
    )

    # ── 7. Call LLM ───────────────────────────────────────────────────
    llm_result = generate_response(messages)

    # ── 8. Extract citations ──────────────────────────────────────────
    citations = extract_citations(llm_result.content, context_chunks)

    # ── 9. Save assistant message ─────────────────────────────────────
    conv_ops.add_message(
        db,
        conversation.id,
        "assistant",
        llm_result.content,
        citations=citations,
        retrieved_chunks=retrieved_chunk_details,
    )

    # ── 10. Build response ────────────────────────────────────────────
    usage = TokenUsage(
        prompt_tokens=llm_result.prompt_tokens,
        completion_tokens=llm_result.completion_tokens,
        total_tokens=llm_result.total_tokens,
    )

    return ChatResponse(
        answer=llm_result.content,
        citations=citations,
        retrieved_chunks=retrieved_chunk_details,
        conversation_id=conversation.id,
        usage=usage,
    )
