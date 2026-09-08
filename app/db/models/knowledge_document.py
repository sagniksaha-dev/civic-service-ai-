import enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Enum, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.department import Department
    from app.db.models.service import Service
    from app.db.models.user import User
    from app.db.models.knowledge_chunk import KnowledgeChunk


class DocumentStatus(str, enum.Enum):
    """Processing and indexing statuses for approved knowledge documents."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class KnowledgeDocument(Base, TimestampMixin):
    """Approved civic service guideline, policy, form, or FAQ document."""
    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)  # pdf, docx, txt, md
    department_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    service_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("services.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    doc_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False
    )
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status", values_callable=lambda obj: [e.value for e in obj]),
        default=DocumentStatus.UPLOADED,
        nullable=False,
        index=True
    )
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    uploaded_by_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Relationships
    department: Mapped[Optional["Department"]] = relationship(
        "Department",
        back_populates="documents"
    )
    service: Mapped[Optional["Service"]] = relationship(
        "Service",
        back_populates="documents"
    )
    uploader: Mapped["User"] = relationship(
        "User",
        back_populates="uploaded_documents"
    )
    chunks: Mapped[List["KnowledgeChunk"]] = relationship(
        "KnowledgeChunk",
        back_populates="document",
        cascade="all, delete-orphan"
    )
