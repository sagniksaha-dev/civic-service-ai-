from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.knowledge_document import DocumentStatus


class KnowledgeChunkResponse(BaseModel):
    """Schema for individual chunk from a knowledge document."""
    id: int
    document_id: int
    chunk_text: str
    chunk_index: int
    page_number: Optional[int] = None
    vector_id: Optional[str] = None
    chunk_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeDocumentResponse(BaseModel):
    """Schema for knowledge document details."""
    id: int
    title: str
    file_name: str
    file_type: str
    department_id: Optional[int] = None
    service_id: Optional[int] = None
    doc_metadata: Dict[str, Any] = Field(default_factory=dict)
    status: DocumentStatus
    chunk_count: int
    uploaded_by_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeDocumentIndexRequest(BaseModel):
    """Schema for manual re-indexing requests."""
    force_reindex: bool = Field(default=False, description="Re-chunk and recreate embeddings")
