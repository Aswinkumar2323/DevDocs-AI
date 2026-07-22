"""
Search API endpoint.

This is the main user-facing endpoint for Sprint 4. It accepts a
natural language query and returns the most relevant documentation
chunks from the indexed knowledge base.

No AI-generated answers are returned — only raw documentation
snippets with relevance scores. LLM answer generation is Sprint 5.

Endpoint:
    POST /search — Search indexed documentation
"""

import logging
from fastapi import APIRouter

from app.schemas.chunk import SearchRequest, SearchResponse, SearchResult
from app.indexing.search_service import vector_search, search_hybrid
from app.indexing.vector_store import ensure_collection_exists

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search_documents(request: SearchRequest):
    """
    Search indexed documentation.

    Accepts a query and returns the top-k most relevant chunks.

    Two search modes:
    - "vector": Pure semantic similarity (best for conceptual questions)
    - "hybrid": Semantic + keyword matching (best for specific terms)

    Example request:
    ```json
    {
        "query": "How does useState work?",
        "source_id": null,
        "top_k": 5,
        "search_type": "hybrid"
    }
    ```

    Example response:
    ```json
    {
        "query": "How does useState work?",
        "results": [
            {
                "score": 0.92,
                "page_title": "useState",
                "heading": "Overview",
                "url": "https://react.dev/reference/react/useState",
                "content": "The useState Hook lets you...",
                "source_name": "React Docs",
                "chunk_index": 0
            }
        ],
        "total": 1
    }
    ```
    """
    # Ensure the Qdrant collection exists before searching
    ensure_collection_exists()

    # Route to the appropriate search method
    if request.search_type == "hybrid":
        results = search_hybrid(
            query=request.query,
            source_id=request.source_id,
            top_k=request.top_k,
        )
    else:
        results = vector_search(
            query=request.query,
            source_id=request.source_id,
            top_k=request.top_k,
        )

    # Convert raw dicts to Pydantic models
    search_results = [
        SearchResult(
            score=r["score"],
            page_title=r.get("page_title"),
            heading=r.get("heading"),
            url=r.get("url", ""),
            content=r.get("content", ""),
            source_name=r.get("source_name"),
            chunk_index=r.get("chunk_index", 0),
        )
        for r in results
    ]

    return SearchResponse(
        query=request.query,
        results=search_results,
        total=len(search_results),
    )
