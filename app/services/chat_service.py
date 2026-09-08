from typing import List, Optional
from sqlalchemy.orm import Session

from app.crud.chat import chat_crud
from app.models.chat_session import ChatSession
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.rag_service import rag_service


class ChatService:
    """Service for managing chat conversations, sessions, and persistence."""

    @classmethod
    def get_or_create_session(
        cls,
        db: Session,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
        initial_title: str = "Civic Query"
    ) -> ChatSession:
        """Get existing session or initialize a new one via CRUD layer."""
        return chat_crud.get_or_create_session(
            db=db,
            session_id=session_id,
            user_id=user_id,
            title=initial_title
        )

    @classmethod
    def process_query(
        cls,
        db: Session,
        query_in: ChatQueryRequest,
        user_id: Optional[int] = None
    ) -> ChatQueryResponse:
        """Process user query via RAG and persist exchange to database."""
        session_obj = cls.get_or_create_session(
            db=db,
            session_id=query_in.session_id,
            user_id=user_id,
            initial_title=query_in.question[:50]
        )

        # Run RAG
        answer, sources, disclaimer, is_grounded = rag_service.answer_civic_query(
            question=query_in.question,
            department_id=query_in.department_id,
            service_id=query_in.service_id,
            language=query_in.language or "en"
        )

        # Persist message via chat_crud
        sources_payload = [s.model_dump() for s in sources]
        chat_crud.add_message(
            db=db,
            session_id=session_obj.id,
            question=query_in.question,
            answer=answer,
            sources=sources_payload,
            disclaimer=disclaimer,
            sender_type="user"
        )

        return ChatQueryResponse(
            session_id=session_obj.session_id,
            question=query_in.question,
            answer=answer,
            sources=sources,
            disclaimer=disclaimer,
            is_grounded=is_grounded,
            language=query_in.language or "en"
        )

    @classmethod
    def get_user_sessions(cls, db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[ChatSession]:
        """Fetch chat sessions belonging to a user."""
        return chat_crud.get_user_sessions(db=db, user_id=user_id, skip=skip, limit=limit)

    @classmethod
    def get_session_by_id(cls, db: Session, session_id: str) -> Optional[ChatSession]:
        """Fetch chat session by session string identifier."""
        return chat_crud.get_session_by_session_id(db=db, session_id=session_id)


chat_service = ChatService()
