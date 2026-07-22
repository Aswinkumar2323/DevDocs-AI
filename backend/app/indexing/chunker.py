import re
import logging
from dataclasses import dataclass
from typing import List, Optional

from app.indexing.tokenizer import count_tokens, truncate_to_tokens
from app.indexing.exceptions import ChunkingError

logger = logging.getLogger(__name__)

# Regex to detect Markdown heading lines: # H1, ## H2, ### H3, etc.
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")

# Chunk size constraints (in tokens, not characters)
# 512 is optimal for embedding models — large enough for context,
# small enough for precise retrieval
MAX_CHUNK_TOKENS = 512

# Chunks smaller than this are usually noise (e.g., just a heading with
# no content, or a single-word section). They produce poor embeddings.
MIN_CHUNK_TOKENS = 30


@dataclass
class ChunkData:
    """
    Intermediate representation of a chunk before it's saved to the database.

    Attributes:
        heading: The Markdown heading this chunk belongs to (e.g., "## Parameters")
        content: The actual text content
        chunk_index: Sequential position within the parent page (0-indexed)
        token_count: Pre-computed token count to avoid recounting later
    """
    heading: Optional[str]
    content: str
    chunk_index: int
    token_count: int


def chunk_markdown(markdown: str, max_tokens: int = MAX_CHUNK_TOKENS, min_tokens: int = MIN_CHUNK_TOKENS) -> List[ChunkData]:
    """
    Split a Markdown document into semantic chunks based on headings.

    This is the main entry point for the chunker.

    Args:
        markdown: The full Markdown content of a documentation page.
        max_tokens: Maximum tokens per chunk (default 512).
        min_tokens: Minimum tokens per chunk; smaller chunks are merged
                    with the next section or dropped (default 30).

    Returns:
        List of ChunkData objects, ordered by chunk_index.

    Raises:
        ChunkingError: If the markdown is empty or processing fails.
    """
    if not markdown or not markdown.strip():
        raise ChunkingError("Cannot chunk empty or blank markdown content")

    try:
        # Step 1: Parse into raw sections based on headings
        sections = _split_by_headings(markdown)

        # Step 2: Enforce max token limits (split oversized sections)
        sized_sections = _enforce_size_limits(sections, max_tokens)

        # Step 3: Build ChunkData objects and filter out tiny fragments
        chunks = _build_chunks(sized_sections, min_tokens)

        if not chunks:
            # Edge case: all sections were too small after filtering
            # Fall back to treating the entire document as one chunk
            token_count = count_tokens(markdown)
            chunks = [ChunkData(
                heading=None,
                content=markdown.strip(),
                chunk_index=0,
                token_count=token_count
            )]

        logger.info(f"Chunked document into {len(chunks)} chunks")
        return chunks

    except ChunkingError:
        raise
    except Exception as e:
        raise ChunkingError(f"Failed to chunk markdown: {e}") from e


def _split_by_headings(markdown: str) -> List[dict]:
    """
    Parse Markdown into sections, where each section is defined by a heading.

    Lines before the first heading go into a section with heading=None
    (this handles pages that start with content before any heading).

    Returns:
        List of dicts: [{"heading": str|None, "content": str}, ...]
    """
    lines = markdown.split("\n")
    sections = []
    current_heading = None
    current_lines = []

    for line in lines:
        match = HEADING_PATTERN.match(line.strip())
        if match:
            # Save the previous section before starting a new one
            if current_lines:
                content = "\n".join(current_lines).strip()
                if content:
                    sections.append({
                        "heading": current_heading,
                        "content": content
                    })
            # Start new section with the detected heading
            current_heading = match.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Don't forget the last section
    if current_lines:
        content = "\n".join(current_lines).strip()
        if content:
            sections.append({
                "heading": current_heading,
                "content": content
            })

    return sections


def _enforce_size_limits(sections: List[dict], max_tokens: int) -> List[dict]:
    """
    Split any section that exceeds max_tokens.

    Strategy:
    1. First try splitting at paragraph boundaries (double newlines)
       — this preserves the most semantic meaning
    2. If a paragraph itself exceeds the limit, hard-split at token boundaries
       — this is a last resort and should rarely happen for documentation

    The heading from the original section is preserved on all sub-chunks
    so the search result still shows the correct section context.
    """
    result = []

    for section in sections:
        token_count = count_tokens(section["content"])

        if token_count <= max_tokens:
            # Section fits, keep as-is
            result.append(section)
        else:
            # Section too large — split at paragraph boundaries
            paragraphs = re.split(r"\n\s*\n", section["content"])
            current_chunk = ""
            current_tokens = 0

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                para_tokens = count_tokens(para)

                if para_tokens > max_tokens:
                    # Even a single paragraph is too large — hard split
                    if current_chunk:
                        result.append({
                            "heading": section["heading"],
                            "content": current_chunk.strip()
                        })
                        current_chunk = ""
                        current_tokens = 0

                    # Split this paragraph into max_tokens-sized pieces
                    remaining = para
                    while count_tokens(remaining) > max_tokens:
                        piece = truncate_to_tokens(remaining, max_tokens)
                        result.append({
                            "heading": section["heading"],
                            "content": piece.strip()
                        })
                        # Remove the piece we just took
                        remaining = remaining[len(piece):].strip()

                    if remaining:
                        current_chunk = remaining
                        current_tokens = count_tokens(remaining)

                elif current_tokens + para_tokens > max_tokens:
                    # Adding this paragraph would exceed the limit
                    # Save current chunk and start a new one
                    if current_chunk:
                        result.append({
                            "heading": section["heading"],
                            "content": current_chunk.strip()
                        })
                    current_chunk = para
                    current_tokens = para_tokens

                else:
                    # Fits — accumulate into current chunk
                    if current_chunk:
                        current_chunk += "\n\n" + para
                    else:
                        current_chunk = para
                    current_tokens += para_tokens

            # Flush the last accumulated chunk
            if current_chunk.strip():
                result.append({
                    "heading": section["heading"],
                    "content": current_chunk.strip()
                })

    return result


def _build_chunks(sections: List[dict], min_tokens: int) -> List[ChunkData]:
    """
    Convert raw sections into ChunkData objects.

    Filters out sections smaller than min_tokens to avoid creating
    embeddings for near-empty chunks (which would pollute search results
    with low-quality matches).
    """
    chunks = []
    index = 0

    for section in sections:
        content = section["content"].strip()
        if not content:
            continue

        token_count = count_tokens(content)

        # Skip tiny chunks — they produce poor embeddings
        if token_count < min_tokens:
            logger.debug(
                f"Skipping small chunk ({token_count} tokens) "
                f"under heading: {section['heading']}"
            )
            continue

        chunks.append(ChunkData(
            heading=section["heading"],
            content=content,
            chunk_index=index,
            token_count=token_count
        ))
        index += 1

    return chunks
