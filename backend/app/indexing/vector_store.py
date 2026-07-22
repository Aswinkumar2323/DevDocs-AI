import logging
from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    MatchText,
    TextIndexParams,
    TokenizerType,
    SearchParams,
    FusionQuery,
    Prefetch,
    Fusion,
)

from app.core.config import settings
from app.indexing.embeddings import EMBEDDING_DIMENSIONS
from app.indexing.exceptions import VectorStoreError

logger = logging.getLogger(__name__)

# Collection name in Qdrant — all documentation chunks go here
COLLECTION_NAME = "documentation_chunks"

# Module-level client singleton
_client: QdrantClient = None


def _get_client() -> QdrantClient:
    global _client
    if _client is None:
        try:
            _client = QdrantClient(url=settings.QDRANT_URL, check_compatibility=False)
            logger.info(f"Connected to Qdrant at {settings.QDRANT_URL}")
        except Exception as e:
            raise VectorStoreError(f"Failed to connect to Qdrant: {e}") from e
    return _client


def ensure_collection_exists():
    try:
        client = _get_client()
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]

        if COLLECTION_NAME not in collection_names:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIMENSIONS,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"Created Qdrant collection: {COLLECTION_NAME}")

            # Create full-text index on 'content' for hybrid search
            # This lets Qdrant do keyword matching alongside vector similarity
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="content",
                field_schema=TextIndexParams(
                    type="text",
                    tokenizer=TokenizerType.WORD,
                    min_token_len=2,
                    max_token_len=20,
                    lowercase=True,
                ),
            )
            logger.info("Created full-text index on 'content' field")

            # Create keyword indexes for filtering
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="source_id",
                field_schema="integer",
            )
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="page_id",
                field_schema="integer",
            )
            logger.info("Created payload indexes for source_id and page_id")
        else:
            logger.info(f"Qdrant collection '{COLLECTION_NAME}' already exists")

    except VectorStoreError:
        raise
    except Exception as e:
        raise VectorStoreError(f"Failed to ensure collection exists: {e}") from e


def upsert_chunks(
    chunk_ids: List[int],
    embeddings: List[List[float]],
    payloads: List[Dict[str, Any]],
    contents: List[str],
) -> None:
    if not chunk_ids:
        return

    try:
        client = _get_client()

        # Build Qdrant PointStruct objects
        points = []
        for chunk_id, embedding, payload, content in zip(chunk_ids, embeddings, payloads, contents):
            # Merge content into the payload so it's searchable via full-text index
            full_payload = {**payload, "content": content}
            points.append(PointStruct(
                id=chunk_id,
                vector=embedding,
                payload=full_payload,
            ))

        # Upsert in batches of 100 to avoid oversized requests
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=batch,
            )
            logger.info(f"Upserted {len(batch)} points to Qdrant (batch {i // batch_size + 1})")

    except Exception as e:
        raise VectorStoreError(f"Failed to upsert chunks: {e}") from e


def delete_by_page_id(page_id: int) -> None:
    try:
        client = _get_client()
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[FieldCondition(key="page_id", match=MatchValue(value=page_id))]
            ),
        )
        logger.info(f"Deleted all vectors for page_id={page_id}")
    except Exception as e:
        raise VectorStoreError(f"Failed to delete vectors for page {page_id}: {e}") from e


def delete_by_source_id(source_id: int) -> None:
    try:
        client = _get_client()
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[FieldCondition(key="source_id", match=MatchValue(value=source_id))]
            ),
        )
        logger.info(f"Deleted all vectors for source_id={source_id}")
    except Exception as e:
        raise VectorStoreError(f"Failed to delete vectors for source {source_id}: {e}") from e


def search_vectors(
    query_vector: List[float],
    source_id: Optional[int] = None,
    top_k: int = 20,
) -> List[Dict[str, Any]]:
    try:
        client = _get_client()

        # Build filter if source_id is specified
        query_filter = None
        if source_id is not None:
            query_filter = Filter(
                must=[FieldCondition(key="source_id", match=MatchValue(value=source_id))]
            )

        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )

        return [
            {
                "id": point.id,
                "score": point.score,
                **point.payload,
            }
            for point in results.points
        ]

    except Exception as e:
        raise VectorStoreError(f"Vector search failed: {e}") from e


def hybrid_search(
    query_vector: List[float],
    query_text: str,
    source_id: Optional[int] = None,
    top_k: int = 20,
) -> List[Dict[str, Any]]:
    """
    Hybrid search combining vector similarity search with Qdrant MatchText full-text search.

    1. Executes vector similarity search to find semantically relevant chunks.
    2. Executes Qdrant payload text search (MatchText) to find keyword matches.
    3. Combines both using Reciprocal Rank Fusion (RRF) for optimal ranking.
    """
    try:
        client = _get_client()

        # 1. Vector Search
        vector_results = search_vectors(query_vector, source_id, top_k=top_k)

        # 2. Full-Text Search on payload 'content' field using MatchText
        must_conditions = [FieldCondition(key="content", match=MatchText(text=query_text))]
        if source_id is not None:
            must_conditions.append(FieldCondition(key="source_id", match=MatchValue(value=source_id)))

        text_filter = Filter(must=must_conditions)

        text_records, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=text_filter,
            limit=top_k,
            with_payload=True,
        )

        text_results = [
            {
                "id": record.id,
                **record.payload,
            }
            for record in text_records
        ]

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[Any, float] = {}
        chunk_map: Dict[Any, Dict[str, Any]] = {}
        k_const = 60.0

        # Process vector ranks
        for rank, item in enumerate(vector_results):
            c_id = item.get("id")
            if c_id is not None:
                chunk_map[c_id] = item
                rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (k_const + rank + 1))

        # Process text search ranks
        for rank, item in enumerate(text_results):
            c_id = item.get("id")
            if c_id is not None:
                if c_id not in chunk_map:
                    chunk_map[c_id] = {**item, "score": 0.5}
                rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (k_const + rank + 1))

        # Sort chunks by RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        combined_results = []
        for c_id in sorted_ids[:top_k]:
            item = chunk_map[c_id]
            # Give a small keyword match bonus if matched both full-text and vector
            base_score = item.get("score", 0.5)
            is_text_match = any(t["id"] == c_id for t in text_results if "id" in t)
            text_bonus = 0.05 if is_text_match else 0.0
            
            combined_results.append({
                **item,
                "score": min(1.0, base_score + text_bonus),
            })

        return combined_results

    except Exception as e:
        logger.warning(f"Hybrid search failed, falling back to vector search: {e}")
        return search_vectors(query_vector, source_id, top_k)
