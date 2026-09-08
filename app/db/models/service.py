import enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.department import Department
    from app.db.models.service_application import ServiceApplication
    from app.db.models.grievance import Grievance
    from app.db.models.knowledge_document import KnowledgeDocument


class ServiceStatus(str, enum.Enum):
    """Status states for public services."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"


class Service(Base, TimestampMixin):
    """Public service catalogue entity (e.g. Water Connection, Trade License)."""
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    department_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    requirements: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=lambda: {"required_documents": [], "instructions": []},
        nullable=False
    )
    eligibility_criteria: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=lambda: {"min_age": 18, "residency_required": True, "details": []},
        nullable=False
    )
    processing_time_days: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    status: Mapped[ServiceStatus] = mapped_column(
        Enum(ServiceStatus, name="service_status", values_callable=lambda obj: [e.value for e in obj]),
        default=ServiceStatus.ACTIVE,
        nullable=False,
        index=True
    )

    # Relationships
    department: Mapped["Department"] = relationship(
        "Department",
        back_populates="services"
    )
    applications: Mapped[List["ServiceApplication"]] = relationship(
        "ServiceApplication",
        back_populates="service",
        cascade="all, delete-orphan"
    )
    grievances: Mapped[List["Grievance"]] = relationship(
        "Grievance",
        back_populates="service"
    )
    documents: Mapped[List["KnowledgeDocument"]] = relationship(
        "KnowledgeDocument",
        back_populates="service"
    )
