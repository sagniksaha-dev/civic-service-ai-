from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, List, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.chat_session import ChatSession


class ChatMessage(Base):
    """Grounded conversation message storing question, generated answer, citations, and disclaimer."""
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    sender_type: Mapped[str] = mapped_column(String(20), default="user", nullable=False)  # user, assistant, system
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sources: Mapped[List[Any]] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )
    disclaimer: Mapped[Optional[str]] = mapped_column(
        Text,
        default="Disclaimer: Information provided is for guidance only based on approved documents and does not constitute formal legal approval.",
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    session: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="messages"
    )
