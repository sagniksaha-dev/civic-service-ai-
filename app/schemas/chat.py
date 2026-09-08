from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SourceReference(BaseModel):
    """Citation of an approved document source used for grounding."""
    document_id: Optional[int] = None
    title: str = Field(..., description="Approved document title")
    file_name: str = Field(..., description="Document file name")
    page_number: Optional[int] = Field(None, description="Page number where snippet was found")
    chunk_index: Optional[int] = None
    similarity_score: Optional[float] = None
    snippet: Optional[str] = Field(None, description="Excerpt from approved guideline")


class ChatQueryRequest(BaseModel):
    """Schema for querying the civic assistant chatbot."""
    question: str = Field(..., min_length=2, max_length=1000, description="Citizen inquiry or procedure question")
    session_id: Optional[str] = Field(None, description="Conversation session ID for continuity")
    department_id: Optional[int] = Field(None, description="Optional department filter")
    service_id: Optional[int] = Field(None, description="Optional service filter")
    language: Optional[str] = Field(default="en", description="Preferred response language ('en', 'hi', 'bn')")


class ChatQueryResponse(BaseModel):
    """Schema for grounded civic assistant response."""
    session_id: str
    question: str
    answer: str
    sources: List[SourceReference] = Field(default_factory=list)
    disclaimer: str = Field(
        default="Disclaimer: Information provided is for guidance only based on approved documents and does not constitute formal legal approval."
    )
    is_grounded: bool = Field(default=True, description="Indicates if answer is grounded in retrieved documents")
    language: Optional[str] = Field(default="en", description="Language of response")


class ChatMessageResponse(BaseModel):
    """Schema for single conversation message."""
    id: int
    session_id: int
    sender_type: str
    question: str
    answer: Optional[str] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    disclaimer: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatSessionResponse(BaseModel):
    """Schema for chat session details with message history."""
    id: int
    session_id: str
    user_id: Optional[int] = None
    title: str
    messages: List[ChatMessageResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebSocketChatMessage(BaseModel):
    """Payload exchanged over real-time WebSocket connection."""
    type: str = Field(default="message", description="Event type: 'message', 'typing', 'error', 'ping'")
    question: Optional[str] = None
    answer: Optional[str] = None
    session_id: Optional[str] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    disclaimer: Optional[str] = None
    error: Optional[str] = None
    language: Optional[str] = "en"
