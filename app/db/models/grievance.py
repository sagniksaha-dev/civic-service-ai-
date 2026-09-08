import enum
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.citizen import Citizen
    from app.db.models.department import Department
    from app.db.models.service import Service
    from app.db.models.user import User


class GrievanceStatus(str, enum.Enum):
    """Workflow statuses for citizen grievance complaints."""
    SUBMITTED = "submitted"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Grievance(Base, TimestampMixin):
    """Citizen grievance complaint entity."""
    __tablename__ = "grievances"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    citizen_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("citizens.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    department_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    service_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("services.id", ondelete="SET NULL"),
        nullable=True
    )
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[GrievanceStatus] = mapped_column(
        Enum(GrievanceStatus, name="grievance_status", values_callable=lambda obj: [e.value for e in obj]),
        default=GrievanceStatus.SUBMITTED,
        nullable=False,
        index=True
    )
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assigned_officer_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    citizen: Mapped["Citizen"] = relationship(
        "Citizen",
        back_populates="grievances"
    )
    department: Mapped["Department"] = relationship(
        "Department",
        back_populates="grievances"
    )
    service: Mapped[Optional["Service"]] = relationship(
        "Service",
        back_populates="grievances"
    )
    assigned_officer: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="assigned_grievances",
        foreign_keys=[assigned_officer_id]
    )
