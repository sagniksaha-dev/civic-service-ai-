import enum
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.citizen import Citizen
    from app.db.models.service_application import ServiceApplication
    from app.db.models.grievance import Grievance
    from app.db.models.knowledge_document import KnowledgeDocument
    from app.db.models.chat_session import ChatSession
    from app.db.models.notification import Notification


class UserRole(str, enum.Enum):
    """User roles for Role-Based Access Control (RBAC)."""
    ADMIN = "admin"
    DEPARTMENT_OFFICER = "department_officer"
    CITIZEN = "citizen"


class User(Base, TimestampMixin):
    """User account entity for authentication and identity."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda obj: [e.value for e in obj]),
        default=UserRole.CITIZEN,
        nullable=False,
        index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    citizen_profile: Mapped[Optional["Citizen"]] = relationship(
        "Citizen",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    reviewed_applications: Mapped[List["ServiceApplication"]] = relationship(
        "ServiceApplication",
        back_populates="reviewer",
        foreign_keys="ServiceApplication.reviewed_by_id"
    )
    assigned_grievances: Mapped[List["Grievance"]] = relationship(
        "Grievance",
        back_populates="assigned_officer",
        foreign_keys="Grievance.assigned_officer_id"
    )
    uploaded_documents: Mapped[List["KnowledgeDocument"]] = relationship(
        "KnowledgeDocument",
        back_populates="uploader",
        foreign_keys="KnowledgeDocument.uploaded_by_id"
    )
    chat_sessions: Mapped[List["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
    )
