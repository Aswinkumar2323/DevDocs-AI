from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database.dependencies import get_db
from app.models.documentation_source import DocumentationSource
from app.schemas.documentation_source import DocumentationSourceCreate, DocumentationSourceResponse
from app.crawler.parser import start_crawl

router = APIRouter(prefix="/sources", tags=["sources"])

# List all Documentation Sources
@router.get("", response_model=list[DocumentationSourceResponse])
def list_sources(db: Session = Depends(get_db)):
    sources = db.query(DocumentationSource).all()
    return sources

@router.post("", response_model=DocumentationSourceResponse)
def create_source(source: DocumentationSourceCreate, db: Session = Depends(get_db)):
    db_source = DocumentationSource(name=source.name, base_url=source.base_url)
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source

@router.post("/crawl/{id}")
def crawl_source(id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    source = db.query(DocumentationSource).filter(DocumentationSource.id == id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
        
    background_tasks.add_task(start_crawl, source_id=id)
    return {"message": "Crawl job started in the background", "source_id": id}

@router.get("/crawl/status/{id}")
def crawl_status(id: int, db: Session = Depends(get_db)):
    source = db.query(DocumentationSource).filter(DocumentationSource.id == id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
        
    # Count pages
    from app.models.page import Page
    total_pages = db.query(Page).filter(Page.source_id == id).count()
    processed_pages = db.query(Page).filter(Page.source_id == id, Page.status == "processed").count()
    failed_pages = db.query(Page).filter(Page.source_id == id, Page.status == "failed").count()
    
    return {
        "source_id": id,
        "status": source.status,
        "total_discovered_pages": total_pages,
        "processed_pages": processed_pages,
        "failed_pages": failed_pages
    }

# View a specific Documentation Source
@router.get("/{id}", response_model=DocumentationSourceResponse)
def get_source(id: int, db: Session = Depends(get_db)):
    source = db.query(DocumentationSource).filter(DocumentationSource.id == id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source

# Delete a Documentation Source (and its pages cascade delete)
@router.delete("/{id}")
def delete_source(id: int, db: Session = Depends(get_db)):
    source = db.query(DocumentationSource).filter(DocumentationSource.id == id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(source)
    db.commit()
    return {"message": f"Successfully deleted source {id} and associated pages"}

