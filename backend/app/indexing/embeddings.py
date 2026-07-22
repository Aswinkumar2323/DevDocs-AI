import logging
from typing import List

from openai import OpenAI

from app.core.config import settings
from app.indexing.exceptions import EmbeddingError

logger = logging.getLogger(__name__)

# OpenAI embedding model configuration
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536

# Lazy-initialized client (created on first use)
_client: OpenAI = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise EmbeddingError(
                "OPENAI_API_KEY is not configured. "
                "Set it in your .env file to use OpenAI embeddings."
            )
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("OpenAI client initialized for embedding generation")
    return _client


def generate_embedding(text: str) -> List[float]:
    if not text or not text.strip():
        raise EmbeddingError("Cannot generate embedding for empty text")

    try:
        client = _get_client()
        response = client.embeddings.create(
            input=text,
            model=EMBEDDING_MODEL,
        )
        embedding = response.data[0].embedding
        logger.debug(f"Generated embedding ({len(embedding)} dims) for text ({len(text)} chars)")
        return embedding

    except EmbeddingError:
        raise
    except Exception as e:
        raise EmbeddingError(f"Failed to generate embedding: {e}") from e


def generate_embeddings_batch(texts: List[str], batch_size: int = 100) -> List[List[float]]:
    if not texts:
        return []

    all_embeddings = []
    client = _get_client()

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(texts) + batch_size - 1) // batch_size

        try:
            logger.info(f"Generating embeddings batch {batch_num}/{total_batches} ({len(batch)} texts)")

            response = client.embeddings.create(
                input=batch,
                model=EMBEDDING_MODEL,
            )

            # OpenAI returns embeddings in the same order as input
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        except Exception as e:
            raise EmbeddingError(
                f"Failed to generate embeddings for batch {batch_num}: {e}"
            ) from e

    logger.info(f"Generated {len(all_embeddings)} embeddings total")
    return all_embeddings
