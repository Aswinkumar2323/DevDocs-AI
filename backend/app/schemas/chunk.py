from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class ChunkResponse(BaseModel):
    id: int
    page_id: int
    heading: Optional[str] = None
    content: str
    chunk_index: int
    token_count: int
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="The search query")
    source_id: Optional[int] = Field(None, description="Filter by documentation source")
    top_k: int = Field(5, ge=1, le=50, description="Number of results to return")
    search_type: str = Field("hybrid", description="'vector' or 'hybrid'")


class SearchResult(BaseModel):
    score: float
    page_title: Optional[str] = None
    heading: Optional[str] = None
    url: str
    content: str
    source_name: Optional[str] = None
    chunk_index: int = 0


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total: int
