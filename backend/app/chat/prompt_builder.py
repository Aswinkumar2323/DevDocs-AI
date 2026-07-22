import logging
from typing import Any

from app.indexing.tokenizer import count_tokens

logger = logging.getLogger(__name__)

# Reserve tokens for the model's response
_RESPONSE_RESERVE = 4096

# Max tokens for conversation history (keeps recent context, drops old)
_HISTORY_BUDGET = 2000

# ── System prompt ─────────────────────────────────────────────────────

_SYSTEM_TEMPLATE = """You are DevDocs AI, a technical documentation assistant.

## Formatting & Structure Requirements
- Start with a direct 1-2 sentence high-level answer or summary.
- Use clear markdown section headings (e.g. `## Overview`, `## Usage & Syntax`, `## Key Details`).
- Structure steps and explanations with bullet points (`-`) or numbered lists.
- Place all code examples inside language-specific code blocks (e.g., ```tsx or ```python).
- Use inline code formatting (`like_this`) for function names, variables, parameters, and types.

## Grounding & Rules
- Answer ONLY using the provided documentation context below.
- If the context does not contain enough information to answer, clearly state: "I don't have enough information in the indexed documentation to answer this question."
- NEVER fabricate APIs, function signatures, code examples, or documentation content.
- Cite your sources inline using this format: [Source: Page Title](url)

## Documentation Context
{context}"""


def _format_context_block(chunks: list[dict[str, Any]]) -> str:
    """Format context chunks into a readable block for the system prompt."""
    if not chunks:
        return "_No documentation context available._"

    sections: list[str] = []
    for i, chunk in enumerate(chunks, 1):
        page_title = chunk.get("page_title") or "Untitled"
        heading = chunk.get("heading", "")
        url = chunk.get("url", "")
        content = chunk.get("content", "")
        score = chunk.get("score", 0)

        header = f"### [{i}] {page_title}"
        if heading:
            header += f" › {heading}"
        header += f"\nURL: {url} | Relevance: {score:.0%}"

        sections.append(f"{header}\n\n{content}")

    return "\n\n---\n\n".join(sections)


def _trim_history(
    history: list[dict[str, str]], max_tokens: int = _HISTORY_BUDGET
) -> list[dict[str, str]]:
    if not history:
        return []

    # Walk backwards, accumulating tokens
    trimmed: list[dict[str, str]] = []
    total = 0

    for msg in reversed(history):
        msg_tokens = count_tokens(msg.get("content", ""))
        if total + msg_tokens > max_tokens and trimmed:
            break
        trimmed.append(msg)
        total += msg_tokens

    trimmed.reverse()
    return trimmed


def build_prompt(
    question: str,
    context_chunks: list[dict[str, Any]],
    conversation_history: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    # Build system message with context
    context_block = _format_context_block(context_chunks)
    system_content = _SYSTEM_TEMPLATE.format(context=context_block)

    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_content},
    ]

    # Add trimmed conversation history
    if conversation_history:
        trimmed = _trim_history(conversation_history)
        messages.extend(trimmed)

    # Add the current question
    messages.append({"role": "user", "content": question})

    # Log token counts for debugging
    total_tokens = sum(count_tokens(m["content"]) for m in messages)
    logger.info(
        "Prompt built: %d messages, ~%d tokens (system=%d, history=%d, question=%d)",
        len(messages),
        total_tokens,
        count_tokens(system_content),
        sum(count_tokens(m["content"]) for m in messages[1:-1]),
        count_tokens(question),
    )

    return messages
