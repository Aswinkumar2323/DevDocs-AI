import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.models.documentation_source import DocumentationSource
from app.models.page import Page
from app.models.chunk import Chunk
from app.indexing.index_service import index_page, index_source

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/indexing", tags=["indexing"])


@router.post("/source/{id}")
def index_source_endpoint(
    id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    source = db.query(DocumentationSource).filter(
        DocumentationSource.id == id
    ).first()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    if source.status not in ("processed", "indexed", "partially_indexed"):
        raise HTTPException(
            status_code=400,
            detail=f"Source must be crawled first. Current status: {source.status}"
        )

    # Launch indexing in background
    background_tasks.add_task(index_source, source_id=id)

    return {
        "message": "Indexing started in the background",
        "source_id": id,
        "source_name": source.name,
    }


@router.post("/page/{id}")
def index_page_endpoint(
    id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    page = db.query(Page).filter(Page.id == id).first()

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    if not page.markdown:
        raise HTTPException(
            status_code=400,
            detail="Page has no markdown content. Crawl it first."
        )

    background_tasks.add_task(index_page, page_id=id)

    return {
        "message": "Page indexing started in the background",
        "page_id": id,
        "page_url": page.url,
    }


@router.get("/status/{source_id}")
def get_indexing_status(
    source_id: int,
    db: Session = Depends(get_db),
):
    source = db.query(DocumentationSource).filter(
        DocumentationSource.id == source_id
    ).first()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # Count pages and chunks
    total_pages = db.query(Page).filter(Page.source_id == source_id).count()
    processed_pages = db.query(Page).filter(
        Page.source_id == source_id,
        Page.status == "processed",
    ).count()

    # Count chunks across all pages for this source
    total_chunks = (
        db.query(Chunk)
        .join(Page, Chunk.page_id == Page.id)
        .filter(Page.source_id == source_id)
        .count()
    )

    # Count pages that have at least one chunk (i.e., have been indexed)
    from sqlalchemy import distinct, func
    indexed_pages = (
        db.query(func.count(distinct(Chunk.page_id)))
        .join(Page, Chunk.page_id == Page.id)
        .filter(Page.source_id == source_id)
        .scalar()
    )

    return {
        "source_id": source_id,
        "source_name": source.name,
        "status": source.status,
        "total_pages": total_pages,
        "processed_pages": processed_pages,
        "indexed_pages": indexed_pages,
        "total_chunks": total_chunks,
    }
