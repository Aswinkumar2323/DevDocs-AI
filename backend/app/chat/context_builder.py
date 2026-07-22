import logging
from typing import Any

from app.indexing.tokenizer import count_tokens

logger = logging.getLogger(__name__)

# Internal budget — keeps context concise to avoid the "lost in the middle"
# problem and control costs. GPT-4o-mini handles 128k but answers degrade
# when swamped with irrelevant context.
_MAX_CONTEXT_TOKENS = 6000


def build_context(
    search_results: list[dict[str, Any]],
    max_tokens: int = _MAX_CONTEXT_TOKENS,
) -> list[dict[str, Any]]:
    if not search_results:
        return []

    # Step 1: Deduplicate by content hash
    seen_content: set[str] = set()
    unique_chunks: list[dict[str, Any]] = []

    for result in search_results:
        content = result.get("content", "").strip()
        if not content:
            continue

        # Use first 200 chars as a dedup fingerprint (fast & catches near-dupes)
        fingerprint = content[:200].lower()
        if fingerprint in seen_content:
            logger.debug("Skipping duplicate chunk: %s", content[:60])
            continue

        seen_content.add(fingerprint)
        unique_chunks.append(result)

    # Step 2: Sort by page → chunk_index for coherent ordering
    unique_chunks.sort(
        key=lambda c: (
            c.get("source_name", ""),
            c.get("url", ""),
            c.get("chunk_index", 0),
        )
    )

    # Step 3: Merge adjacent chunks from the same page
    merged: list[dict[str, Any]] = []
    for chunk in unique_chunks:
        if (
            merged
            and merged[-1].get("url") == chunk.get("url")
            and chunk.get("chunk_index", 0) - merged[-1].get("chunk_index", 0) == 1
        ):
            # Adjacent chunk on the same page — merge content
            merged[-1]["content"] += "\n\n" + chunk.get("content", "")
            merged[-1]["chunk_index"] = chunk.get("chunk_index", 0)
            # Keep the higher score
            merged[-1]["score"] = max(
                merged[-1].get("score", 0), chunk.get("score", 0)
            )
        else:
            merged.append(dict(chunk))

    # Step 4: Trim to token budget (keep highest-scoring first)
    # Re-sort by score so we keep the most relevant chunks
    merged.sort(key=lambda c: c.get("score", 0), reverse=True)

    selected: list[dict[str, Any]] = []
    total_tokens = 0

    for chunk in merged:
        content = chunk.get("content", "")
        tokens = count_tokens(content)
        chunk["token_count"] = tokens

        if total_tokens + tokens > max_tokens:
            # If we have at least some context, stop; otherwise force-include
            if selected:
                break

        selected.append(chunk)
        total_tokens += tokens

    logger.info(
        "Context builder: %d results → %d unique → %d merged → %d selected (%d tokens)",
        len(search_results),
        len(unique_chunks),
        len(merged),
        len(selected),
        total_tokens,
    )

    # Final re-sort by page order for coherent reading
    selected.sort(
        key=lambda c: (
            c.get("source_name", ""),
            c.get("url", ""),
            c.get("chunk_index", 0),
        )
    )

    return selected
