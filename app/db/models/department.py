from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.service import Service
    from app.db.models.grievance import Grievance
    from app.db.models.knowledge_document import KnowledgeDocument


class Department(Base, TimestampMixin):
    """Public service department entity (e.g. Public Works, Revenue, Municipal)."""
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    services: Mapped[List["Service"]] = relationship(
        "Service",
        back_populates="department",
        cascade="all, delete-orphan"
    )
    grievances: Mapped[List["Grievance"]] = relationship(
        "Grievance",
        back_populates="department"
    )
    documents: Mapped[List["KnowledgeDocument"]] = relationship(
        "KnowledgeDocument",
        back_populates="department"
    )
