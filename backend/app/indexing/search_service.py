import logging
from typing import List, Optional

from app.indexing.embeddings import generate_embedding
from app.indexing.vector_store import search_vectors, hybrid_search
from app.indexing.reranker import rerank

logger = logging.getLogger(__name__)

# How many candidates to fetch from Qdrant before reranking
# We over-fetch so the reranker has a good pool to select from
RETRIEVAL_TOP_K = 20


def vector_search(
    query: str,
    source_id: Optional[int] = None,
    top_k: int = 5,
) -> List[dict]:
    logger.info(f"Vector search: '{query}' (source_id={source_id}, top_k={top_k})")

    # Step 1: Generate embedding for the query
    query_embedding = generate_embedding(query)

    # Step 2: Search Qdrant (over-fetch for reranking)
    raw_results = search_vectors(
        query_vector=query_embedding,
        source_id=source_id,
        top_k=RETRIEVAL_TOP_K,
    )

    # Step 3: Rerank and trim to requested top_k
    reranked = rerank(raw_results, query, top_n=top_k)

    return _format_results(reranked)


def search_hybrid(
    query: str,
    source_id: Optional[int] = None,
    top_k: int = 5,
) -> List[dict]:
    logger.info(f"Hybrid search: '{query}' (source_id={source_id}, top_k={top_k})")

    # Step 1: Generate embedding for the query
    query_embedding = generate_embedding(query)

    # Step 2: Hybrid search in Qdrant (vector + full-text fusion)
    raw_results = hybrid_search(
        query_vector=query_embedding,
        query_text=query,
        source_id=source_id,
        top_k=RETRIEVAL_TOP_K,
    )

    # Step 3: Rerank and trim
    reranked = rerank(raw_results, query, top_n=top_k)

    return _format_results(reranked)


def _format_results(results: List[dict]) -> List[dict]:
    formatted = []
    for r in results:
        formatted.append({
            "score": r.get("score", 0.0),
            "page_title": r.get("page_title", "Untitled"),
            "heading": r.get("heading", ""),
            "url": r.get("page_url", ""),
            "content": r.get("content", ""),
            "source_name": r.get("source_name", ""),
            "chunk_index": r.get("chunk_index", 0),
        })
    return formatted
