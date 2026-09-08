from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.chat import (
    ChatMessageResponse,
    ChatQueryRequest,
    ChatQueryResponse,
    ChatSessionResponse,
)
from app.services.chat_service import chat_service

router = APIRouter()


@router.post(
    "/query",
    response_model=ChatQueryResponse,
    summary="Query Civic Assistant (HTTP RAG)",
    description="Ask a procedural or eligibility question. Returns grounded answer, source citations, and liability disclaimer."
)
def query_assistant(
    query_in: ChatQueryRequest,
    db: Session = Depends(deps.get_db),
    current_user: Optional[User] = Depends(deps.oauth2_scheme)
) -> Any:
    """Process civic inquiry via RAG."""
    # Resolve user if token provided, otherwise anonymous
    user_id = None
    if current_user:
        try:
            resolved_user = deps.get_current_user(db=db, token=current_user)
            user_id = resolved_user.id
        except Exception:
            user_id = None

    return chat_service.process_query(db=db, query_in=query_in, user_id=user_id)


@router.get(
    "/sessions",
    response_model=List[ChatSessionResponse],
    summary="List My Chat Sessions",
    description="Retrieve conversation sessions for the authenticated user."
)
def list_chat_sessions(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """List current user's chat sessions."""
    return chat_service.get_user_sessions(db=db, user_id=current_user.id)


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionResponse,
    summary="Get Chat Session & History",
    description="Retrieve full message history and citations for a conversation session."
)
def get_chat_session(
    session_id: str,
    db: Session = Depends(deps.get_db),
    current_user: Optional[User] = Depends(deps.oauth2_scheme)
) -> Any:
    """Get chat session details."""
    session_obj = chat_service.get_session_by_id(db=db, session_id=session_id)
    if not session_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found."
        )

    # If session is owned by a registered user, enforce ownership
    if session_obj.user_id is not None:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to view this session."
            )
        resolved_user = deps.get_current_user(db=db, token=current_user)
        if resolved_user.role != "admin" and resolved_user.id != session_obj.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this chat session."
            )

    return session_obj
