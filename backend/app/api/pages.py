from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.dependencies import get_db
from app.models.page import Page
from app.schemas.page import PageResponse, PageResponseWithContent

router = APIRouter(prefix="/pages", tags=["pages"])

@router.get("", response_model=List[PageResponse])
def get_pages(
    source_id: Optional[int] = Query(None, description="Filter pages by source ID"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Page)
    if source_id is not None:
        query = query.filter(Page.source_id == source_id)
        
    pages = query.offset(skip).limit(limit).all()
    return pages

@router.get("/{id}", response_model=PageResponseWithContent)
def get_page(id: int, db: Session = Depends(get_db)):
    page = db.query(Page).filter(Page.id == id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page

# Delete a single Page
@router.delete("/{id}")
def delete_page(id: int, db: Session = Depends(get_db)):
    page = db.query(Page).filter(Page.id == id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    db.delete(page)
    db.commit()
    return {"message": f"Successfully deleted page {id}"}
