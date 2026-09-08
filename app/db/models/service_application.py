import enum
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.citizen import Citizen
    from app.db.models.service import Service
    from app.db.models.user import User


class ApplicationStatus(str, enum.Enum):
    """Workflow statuses for service applications."""
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ADDITIONAL_INFO_REQUIRED = "additional_info_required"
    APPROVED = "approved"
    REJECTED = "rejected"


class ServiceApplication(Base, TimestampMixin):
    """Citizen service application entity with workflow status tracking."""
    __tablename__ = "service_applications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    citizen_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("citizens.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    service_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    reference_no: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    payload: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status", values_callable=lambda obj: [e.value for e in obj]),
        default=ApplicationStatus.SUBMITTED,
        nullable=False,
        index=True
    )
    officer_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    citizen: Mapped["Citizen"] = relationship(
        "Citizen",
        back_populates="applications"
    )
    service: Mapped["Service"] = relationship(
        "Service",
        back_populates="applications"
    )
    reviewer: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="reviewed_applications",
        foreign_keys=[reviewed_by_id]
    )
