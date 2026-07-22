import logging
import re
from typing import Any

from app.chat.schemas import Citation

logger = logging.getLogger(__name__)

# Regex to match markdown-style source citations: [Source: Page Title](url)
_CITATION_PATTERN = re.compile(
    r'\[Source:\s*([^\]]+)\]\(([^)]+)\)',
    re.IGNORECASE,
)


def extract_citations(
    answer: str,
    retrieved_chunks: list[dict[str, Any]],
) -> list[Citation]:
    # Build a URL → chunk lookup for validation
    chunk_by_url: dict[str, dict[str, Any]] = {}
    for chunk in retrieved_chunks:
        url = chunk.get("url", "")
        if url and url not in chunk_by_url:
            chunk_by_url[url] = chunk

    citations: list[Citation] = []
    seen_urls: set[str] = set()

    # Try to parse inline citations from the answer
    matches = _CITATION_PATTERN.findall(answer)

    if matches:
        for title, url in matches:
            url = url.strip()
            if url in seen_urls:
                continue
            seen_urls.add(url)

            # Look up the chunk for additional metadata
            chunk = chunk_by_url.get(url, {})

            citations.append(
                Citation(
                    source_name=chunk.get("source_name"),
                    page_title=title.strip() or chunk.get("page_title"),
                    page_url=url,
                    heading=chunk.get("heading"),
                    content_snippet=chunk.get("content", "")[:200],
                )
            )

        logger.info("Extracted %d inline citations from LLM answer", len(citations))

    # Fallback: if the LLM didn't produce citations, create them from top chunks
    if not citations and retrieved_chunks:
        for chunk in retrieved_chunks[:5]:  # Top 5 chunks as sources
            url = chunk.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            citations.append(
                Citation(
                    source_name=chunk.get("source_name"),
                    page_title=chunk.get("page_title"),
                    page_url=url,
                    heading=chunk.get("heading"),
                    content_snippet=chunk.get("content", "")[:200],
                )
            )

        logger.info(
            "No inline citations found; generated %d from retrieved chunks",
            len(citations),
        )

    return citations
