from datetime import datetime, timezone
from typing import Any, Dict, List
from sqlalchemy import JSON, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base SQLAlchemy Declarative Model with default table name and json types."""

    type_annotation_map = {
        dict: JSON,
        list: JSON,
        Dict[str, Any]: JSON,
        List[Any]: JSON,
    }


class TimestampMixin:
    """Mixin to provide created_at and updated_at timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
