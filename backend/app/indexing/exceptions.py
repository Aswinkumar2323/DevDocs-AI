
class ChunkingError(Exception):
    """Raised when Markdown splitting fails.

    Common causes:
    - Empty or None markdown content
    - Malformed markdown that breaks the heading parser
    """
    pass


class EmbeddingError(Exception):
    """Raised when embedding generation fails.

    Common causes:
    - OpenAI API key invalid or missing
    - Rate limiting from the OpenAI API
    - Text exceeds the embedding model's token limit
    """
    pass


class VectorStoreError(Exception):
    """Raised when Qdrant operations fail.

    Common causes:
    - Qdrant server unreachable
    - Collection doesn't exist
    - Payload schema mismatch
    """
    pass


class IndexingError(Exception):
    """General orchestration failure in the indexing pipeline.

    Wraps lower-level exceptions when the overall pipeline
    cannot complete for a page or source.
    """
    pass
