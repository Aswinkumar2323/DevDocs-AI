from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PageBase(BaseModel):
    url: str
    title: Optional[str] = None
    checksum: Optional[str] = None
    status: str = "pending"


class PageCreate(PageBase):
    source_id: int
    html: Optional[str] = None
    markdown: Optional[str] = None


class PageUpdate(BaseModel):
    title: Optional[str] = None
    html: Optional[str] = None
    markdown: Optional[str] = None
    checksum: Optional[str] = None
    status: Optional[str] = None


class PageResponse(PageBase):
    id: int
    source_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class PageResponseWithContent(PageResponse):
    markdown: Optional[str] = None
    html: Optional[str] = None
