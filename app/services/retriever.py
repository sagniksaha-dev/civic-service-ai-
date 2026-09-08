from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.schemas.chat import SourceReference
from app.services.vector_store import vector_store


class RetrieverService:
    """Service to retrieve relevant document chunks and format source references."""

    @staticmethod
    def retrieve_context(
        query: str,
        top_k: int = settings.SIMILARITY_TOP_K,
        department_id: Optional[int] = None,
        service_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve matching document snippets from the vector store."""
        return vector_store.query_similar(
            query_text=query,
            top_k=top_k,
            department_id=department_id,
            service_id=service_id
        )

    @staticmethod
    def format_sources(snippets: List[Dict[str, Any]]) -> List[SourceReference]:
        """Convert retrieved snippet metadata into structured SourceReference objects."""
        sources = []
        for s in snippets:
            meta = s.get("metadata", {})
            sources.append(SourceReference(
                document_id=meta.get("document_id"),
                title=meta.get("title", "Approved Civic Guideline"),
                file_name=meta.get("file_name", "document.pdf"),
                page_number=meta.get("page_number"),
                chunk_index=meta.get("chunk_index"),
                similarity_score=s.get("similarity_score"),
                snippet=s.get("text", "")[:300] + ("..." if len(s.get("text", "")) > 300 else "")
            ))
        return sources


retriever_service = RetrieverService()
