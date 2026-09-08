from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.service_application import ServiceApplication
    from app.db.models.grievance import Grievance


class Citizen(Base, TimestampMixin):
    """Citizen profile linked to a User account."""
    __tablename__ = "citizens"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=lambda: {
            "street": "",
            "city": "",
            "district": "",
            "state": "",
            "postal_code": ""
        },
        nullable=False
    )
    date_of_birth: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="citizen_profile"
    )
    applications: Mapped[List["ServiceApplication"]] = relationship(
        "ServiceApplication",
        back_populates="citizen",
        cascade="all, delete-orphan"
    )
    grievances: Mapped[List["Grievance"]] = relationship(
        "Grievance",
        back_populates="citizen",
        cascade="all, delete-orphan"
    )
