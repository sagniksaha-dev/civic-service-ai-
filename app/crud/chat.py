import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage


class CRUDChat:
    """CRUD operations for Chat Sessions and Grounded Messages."""

    def get_session_by_session_id(self, db: Session, session_id: str) -> Optional[ChatSession]:
        """Fetch chat session by UUID string identifier."""
        stmt = select(ChatSession).where(ChatSession.session_id == session_id)
        return db.execute(stmt).scalar_one_or_none()

    def get_session(self, db: Session, id: int) -> Optional[ChatSession]:
        """Fetch chat session by primary key ID."""
        return db.get(ChatSession, id)

    def create_session(
        self,
        db: Session,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
        title: str = "Civic Query"
    ) -> ChatSession:
        """Create a new chat conversation session."""
        new_session_id = session_id or str(uuid.uuid4())
        session_obj = ChatSession(
            session_id=new_session_id,
            user_id=user_id,
            title=title[:100]
        )
        db.add(session_obj)
        db.commit()
        db.refresh(session_obj)
        return session_obj

    def get_or_create_session(
        self,
        db: Session,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
        title: str = "Civic Query"
    ) -> ChatSession:
        """Fetch existing session or create a new session."""
        if session_id:
            existing = self.get_session_by_session_id(db, session_id=session_id)
            if existing:
                return existing
        return self.create_session(db, session_id=session_id, user_id=user_id, title=title)

    def get_user_sessions(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[ChatSession]:
        """Fetch chat sessions belonging to a specific user."""
        stmt = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

    def add_message(
        self,
        db: Session,
        session_id: int,
        question: str,
        answer: Optional[str] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
        disclaimer: Optional[str] = None,
        sender_type: str = "user"
    ) -> ChatMessage:
        """Persist a message exchange to the database."""
        msg = ChatMessage(
            session_id=session_id,
            sender_type=sender_type,
            question=question,
            answer=answer,
            sources=sources or [],
            disclaimer=disclaimer
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg

    def delete_session(self, db: Session, session_id: str) -> bool:
        """Delete a chat session and all linked messages."""
        session_obj = self.get_session_by_session_id(db, session_id=session_id)
        if not session_obj:
            return False
        db.delete(session_obj)
        db.commit()
        return True


chat_crud = CRUDChat()
