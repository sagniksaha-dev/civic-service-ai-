from app.schemas.knowledge_document import (
    KnowledgeChunkResponse,
    KnowledgeDocumentResponse,
    KnowledgeDocumentIndexRequest,
)

# Aliases matching folder structure specification
DocumentResponse = KnowledgeDocumentResponse
DocumentChunkResponse = KnowledgeChunkResponse
DocumentIndexRequest = KnowledgeDocumentIndexRequest

__all__ = [
    "KnowledgeChunkResponse",
    "KnowledgeDocumentResponse",
    "KnowledgeDocumentIndexRequest",
    "DocumentResponse",
    "DocumentChunkResponse",
    "DocumentIndexRequest",
]
