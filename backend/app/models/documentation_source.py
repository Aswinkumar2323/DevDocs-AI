from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column, relationship

from app.database.base import Base


class DocumentationSource(Base):

    __tablename__ = "documentation_sources"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(100))

    base_url: Mapped[str] = mapped_column(String(500))

    status: Mapped[str] = mapped_column(default="pending")

    pages = relationship("Page", back_populates="source", cascade="all, delete-orphan")