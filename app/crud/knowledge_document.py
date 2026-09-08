from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.knowledge_document import KnowledgeDocument, DocumentStatus
from app.models.knowledge_chunk import KnowledgeChunk


class CRUDKnowledgeDocument:
    """CRUD operations for approved civic knowledge documents and chunks."""

    def get(self, db: Session, document_id: int) -> Optional[KnowledgeDocument]:
        """Fetch document by primary key ID."""
        return db.get(KnowledgeDocument, document_id)

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        department_id: Optional[int] = None,
        service_id: Optional[int] = None,
        status: Optional[DocumentStatus] = None
    ) -> List[KnowledgeDocument]:
        """List documents with optional department, service, and status filters."""
        stmt = select(KnowledgeDocument)
        if department_id is not None:
            stmt = stmt.where(KnowledgeDocument.department_id == department_id)
        if service_id is not None:
            stmt = stmt.where(KnowledgeDocument.service_id == service_id)
        if status is not None:
            stmt = stmt.where(KnowledgeDocument.status == status)

        stmt = stmt.order_by(KnowledgeDocument.created_at.desc()).offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())

    def create(
        self,
        db: Session,
        title: str,
        file_name: str,
        file_path: str,
        file_type: str,
        uploaded_by_id: int,
        department_id: Optional[int] = None,
        service_id: Optional[int] = None,
        doc_metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeDocument:
        """Create a new knowledge document record."""
        db_obj = KnowledgeDocument(
            title=title.strip(),
            file_name=file_name,
            file_path=file_path,
            file_type=file_type.lower().lstrip("."),
            uploaded_by_id=uploaded_by_id,
            department_id=department_id,
            service_id=service_id,
            doc_metadata=doc_metadata or {},
            status=DocumentStatus.UPLOADED,
            chunk_count=0
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def add_chunks(
        self,
        db: Session,
        document_id: int,
        chunks_data: List[Dict[str, Any]]
    ) -> List[KnowledgeChunk]:
        """Store chunk records in SQL database."""
        # Delete existing chunks first if re-indexing
        existing_chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == document_id).all()
        for ec in existing_chunks:
            db.delete(ec)

        created_chunks = []
        for c in chunks_data:
            chunk_obj = KnowledgeChunk(
                document_id=document_id,
                chunk_text=c.get("text", ""),
                chunk_index=c.get("chunk_index", 0),
                page_number=c.get("page_number", 1),
                vector_id=f"doc_{document_id}_chk_{c.get('chunk_index', 0)}",
                chunk_metadata=c.get("metadata", {})
            )
            db.add(chunk_obj)
            created_chunks.append(chunk_obj)

        doc = db.get(KnowledgeDocument, document_id)
        if doc:
            doc.chunk_count = len(created_chunks)
            doc.status = DocumentStatus.INDEXED

        db.commit()
        return created_chunks

    def delete(self, db: Session, document_id: int) -> Optional[KnowledgeDocument]:
        """Delete document and all attached chunks."""
        obj = db.get(KnowledgeDocument, document_id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


knowledge_document_crud = CRUDKnowledgeDocument()
