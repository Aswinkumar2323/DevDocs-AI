import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.page import Page
from app.models.chunk import Chunk
from app.models.documentation_source import DocumentationSource
from app.database.session import SessionLocal
from app.indexing.chunker import chunk_markdown
from app.indexing.tokenizer import count_tokens
from app.indexing.metadata import generate_chunk_metadata
from app.indexing.embeddings import generate_embeddings_batch
from app.indexing.vector_store import (
    ensure_collection_exists,
    upsert_chunks,
    delete_by_page_id,
    delete_by_source_id,
)
from app.indexing.exceptions import (
    ChunkingError,
    EmbeddingError,
    VectorStoreError,
    IndexingError,
)

logger = logging.getLogger(__name__)


def index_page(page_id: int, db: Optional[Session] = None) -> dict:
    own_session = db is None
    if own_session:
        db = SessionLocal()

    try:
        # ---- Step 0: Load the page from the database ----
        page = db.query(Page).filter(Page.id == page_id).first()
        if not page:
            raise IndexingError(f"Page with id {page_id} not found")

        if not page.markdown or not page.markdown.strip():
            logger.warning(f"Page {page_id} has no markdown content, skipping")
            return {"page_id": page_id, "chunks_created": 0, "status": "skipped"}

        # Load the parent source for metadata
        source = db.query(DocumentationSource).filter(
            DocumentationSource.id == page.source_id
        ).first()
        source_name = source.name if source else "Unknown"

        logger.info(f"Indexing page {page_id}: '{page.title or page.url}'")

        # ---- Step 1: Delete existing chunks for this page (re-index safe) ----
        existing_chunks = db.query(Chunk).filter(Chunk.page_id == page_id).all()
        if existing_chunks:
            logger.info(f"Deleting {len(existing_chunks)} existing chunks for page {page_id}")
            # Delete from Qdrant first
            try:
                delete_by_page_id(page_id)
            except VectorStoreError as e:
                logger.warning(f"Could not delete vectors from Qdrant (may not exist yet): {e}")

            # Then delete from PostgreSQL
            for chunk in existing_chunks:
                db.delete(chunk)
            db.commit()

        # ---- Step 2: Chunk the Markdown ----
        try:
            chunk_data_list = chunk_markdown(page.markdown)
        except ChunkingError as e:
            logger.error(f"Chunking failed for page {page_id}: {e}")
            return {"page_id": page_id, "chunks_created": 0, "status": "chunking_failed"}

        logger.info(f"Created {len(chunk_data_list)} chunks for page {page_id}")

        # ---- Step 3: Save chunks to PostgreSQL ----
        db_chunks = []
        for chunk_data in chunk_data_list:
            db_chunk = Chunk(
                page_id=page_id,
                heading=chunk_data.heading,
                content=chunk_data.content,
                chunk_index=chunk_data.chunk_index,
                token_count=chunk_data.token_count,
            )
            db.add(db_chunk)
            db_chunks.append(db_chunk)

        # Commit to get auto-generated IDs (needed as Qdrant point IDs)
        db.commit()
        for chunk in db_chunks:
            db.refresh(chunk)

        # ---- Step 4: Generate metadata for each chunk ----
        metadatas = []
        for chunk_data, db_chunk in zip(chunk_data_list, db_chunks):
            metadata = generate_chunk_metadata(
                source_id=page.source_id,
                source_name=source_name,
                page_id=page_id,
                page_title=page.title,
                page_url=page.url,
                heading=chunk_data.heading,
                chunk_index=chunk_data.chunk_index,
                token_count=chunk_data.token_count,
            )
            metadatas.append(metadata)

        # ---- Step 5: Generate embeddings via OpenAI ----
        try:
            texts = [chunk.content for chunk in db_chunks]
            embeddings = generate_embeddings_batch(texts)
        except EmbeddingError as e:
            logger.error(f"Embedding generation failed for page {page_id}: {e}")
            # Chunks are saved in DB, can retry embedding later
            return {"page_id": page_id, "chunks_created": len(db_chunks), "status": "embedding_failed"}

        # ---- Step 6: Ensure Qdrant collection exists ----
        ensure_collection_exists()

        # ---- Step 7: Upsert vectors + metadata to Qdrant ----
        try:
            chunk_ids = [chunk.id for chunk in db_chunks]
            contents = [chunk.content for chunk in db_chunks]
            upsert_chunks(chunk_ids, embeddings, metadatas, contents)
        except VectorStoreError as e:
            logger.error(f"Qdrant upsert failed for page {page_id}: {e}")
            return {"page_id": page_id, "chunks_created": len(db_chunks), "status": "vector_store_failed"}

        logger.info(f"Successfully indexed page {page_id} with {len(db_chunks)} chunks")
        return {"page_id": page_id, "chunks_created": len(db_chunks), "status": "indexed"}

    except IndexingError:
        raise
    except Exception as e:
        db.rollback()
        raise IndexingError(f"Failed to index page {page_id}: {e}") from e
    finally:
        if own_session:
            db.close()


def index_source(source_id: int) -> dict:
    db = SessionLocal()
    try:
        source = db.query(DocumentationSource).filter(
            DocumentationSource.id == source_id
        ).first()
        if not source:
            raise IndexingError(f"Source with id {source_id} not found")

        # Get all pages that have been crawled and processed
        pages = db.query(Page).filter(
            Page.source_id == source_id,
            Page.status == "processed",
        ).all()

        if not pages:
            logger.warning(f"No processed pages found for source {source_id}")
            return {
                "source_id": source_id,
                "total_pages": 0,
                "indexed_pages": 0,
                "failed_pages": 0,
                "total_chunks": 0,
                "status": "no_pages",
            }

        logger.info(f"Starting indexing for source '{source.name}' ({len(pages)} pages)")

        # Update source status
        source.status = "indexing"
        db.commit()

        indexed_count = 0
        failed_count = 0
        total_chunks = 0

        for i, page in enumerate(pages):
            try:
                logger.info(f"Indexing page {i + 1}/{len(pages)}: {page.url}")
                result = index_page(page.id, db=db)
                total_chunks += result.get("chunks_created", 0)

                if result["status"] == "indexed":
                    indexed_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                logger.error(f"Failed to index page {page.id}: {e}")
                failed_count += 1

        # Update source status
        source.status = "indexed" if failed_count == 0 else "partially_indexed"
        db.commit()

        stats = {
            "source_id": source_id,
            "total_pages": len(pages),
            "indexed_pages": indexed_count,
            "failed_pages": failed_count,
            "total_chunks": total_chunks,
            "status": source.status,
        }

        logger.info(f"Indexing complete for source {source_id}: {stats}")
        return stats

    except IndexingError:
        raise
    except Exception as e:
        db.rollback()
        raise IndexingError(f"Failed to index source {source_id}: {e}") from e
    finally:
        db.close()
