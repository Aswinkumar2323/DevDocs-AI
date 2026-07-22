import logging
from typing import Optional

logger = logging.getLogger(__name__)


def generate_chunk_metadata(
    source_id: int,
    source_name: str,
    page_id: int,
    page_title: Optional[str],
    page_url: str,
    heading: Optional[str],
    chunk_index: int,
    token_count: int,
) -> dict:

    metadata = {
        "source_id": source_id,
        "source_name": source_name or "Unknown",
        "page_id": page_id,
        "page_title": page_title or "Untitled",
        "page_url": page_url,
        "heading": heading or "General",
        "chunk_index": chunk_index,
        "token_count": token_count,
    }

    logger.debug(f"Generated metadata for chunk {chunk_index} of page {page_id}")
    return metadata
