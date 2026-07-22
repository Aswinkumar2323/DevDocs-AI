from datetime import datetime
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Chunk(Base):

    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Foreign key linking this chunk to its parent page
    page_id: Mapped[int] = mapped_column(ForeignKey("pages.id"), index=True)

    # The section heading this chunk falls under (e.g., "Parameters", "Examples")
    heading: Mapped[str] = mapped_column(String(500), nullable=True)

    # The actual text content of this chunk
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Position of this chunk within its parent page (0-indexed)
    # Used to reconstruct document order when displaying results
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)

    # Number of tokens in this chunk (counted by tiktoken)
    # Stored to avoid recounting and to validate against embedding model limits
    token_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship back to the parent Page
    page = relationship("Page", back_populates="chunks")
