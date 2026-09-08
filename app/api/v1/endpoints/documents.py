import os
import shutil
from pathlib import Path
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.core.logging import logger
from app.crud.knowledge_document import knowledge_document_crud
from app.models.knowledge_document import DocumentStatus
from app.models.user import User
from app.schemas.knowledge_document import (
    KnowledgeChunkResponse,
    KnowledgeDocumentResponse,
)
from app.services.chunking import chunking_service
from app.services.document_loader import document_loader
from app.services.vector_store import vector_store

router = APIRouter()


@router.post(
    "/upload",
    response_model=KnowledgeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload & Index Approved Document (Officer or Admin)",
    description="Upload a PDF, DOCX, TXT, or Markdown guideline file and index it into the vector database."
)
async def upload_and_index_document(
    file: UploadFile = File(..., description="Civic guideline document (PDF, DOCX, TXT, MD)"),
    title: str = Form(..., min_length=2, max_length=200, description="Title of document"),
    department_id: Optional[int] = Form(None, description="Associated department ID"),
    service_id: Optional[int] = Form(None, description="Associated service ID"),
    category: Optional[str] = Form("guideline", description="Document category"),
    db: Session = Depends(deps.get_db),
    current_officer: User = Depends(deps.require_officer_or_admin)
) -> Any:
    """Upload, parse, chunk, embed, and index a document."""
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in document_loader.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file_ext}'. Allowed formats: {list(document_loader.SUPPORTED_EXTENSIONS)}"
        )

    # Save file to storage
    storage_dir = settings.get_absolute_path(settings.STORAGE_PATH)
    safe_filename = f"{Path(file.filename).stem}_{current_officer.id}{file_ext}"
    dest_path = storage_dir / safe_filename

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    logger.info("Saved uploaded document to %s", dest_path)

    # Create DB record
    doc_meta = {"category": category, "uploader_email": current_officer.email}
    doc_record = knowledge_document_crud.create(
        db=db,
        title=title,
        file_name=file.filename,
        file_path=str(dest_path),
        file_type=file_ext,
        uploaded_by_id=current_officer.id,
        department_id=department_id,
        service_id=service_id,
        doc_metadata=doc_meta
    )

    try:
        # Extract text pages
        pages = document_loader.load_document(str(dest_path))
        if not pages:
            raise ValueError("No extractable text found in uploaded document.")

        # Chunk text
        chunk_meta = {
            "document_id": doc_record.id,
            "title": doc_record.title,
            "file_name": doc_record.file_name,
            "department_id": department_id or 0,
            "service_id": service_id or 0,
            "category": category
        }
        chunks = chunking_service.chunk_document_pages(pages, doc_metadata=chunk_meta)

        # Store in Vector Database
        vector_ids = vector_store.add_chunks(chunks)

        # Store chunk records in SQL database
        knowledge_document_crud.add_chunks(db, document_id=doc_record.id, chunks_data=chunks)
        db.refresh(doc_record)

        logger.info("Successfully ingested document '%s' with %d chunks.", doc_record.title, len(chunks))
        return doc_record

    except Exception as e:
        logger.error("Error processing document %s: %s", doc_record.id, e)
        doc_record.status = DocumentStatus.FAILED
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract and index document: {str(e)}"
        )


@router.get(
    "/",
    response_model=List[KnowledgeDocumentResponse],
    summary="List Knowledge Documents",
    description="Retrieve list of all indexed approved civic knowledge documents."
)
def list_documents(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    department_id: Optional[int] = None,
    service_id: Optional[int] = None,
    status: Optional[DocumentStatus] = None
) -> Any:
    """List knowledge documents."""
    return knowledge_document_crud.get_multi(
        db,
        skip=skip,
        limit=limit,
        department_id=department_id,
        service_id=service_id,
        status=status
    )


@router.get(
    "/{document_id}",
    response_model=KnowledgeDocumentResponse,
    summary="Get Document Details",
    description="Retrieve metadata for a specific knowledge document."
)
def get_document(
    document_id: int,
    db: Session = Depends(deps.get_db)
) -> Any:
    """Get document details."""
    doc = knowledge_document_crud.get(db, document_id=document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )
    return doc


@router.post(
    "/{document_id}/reindex",
    response_model=KnowledgeDocumentResponse,
    summary="Re-index Document (Officer or Admin)",
    description="Re-extract, chunk, and embed an existing document into ChromaDB."
)
def reindex_document(
    document_id: int,
    db: Session = Depends(deps.get_db),
    current_officer: User = Depends(deps.require_officer_or_admin)
) -> Any:
    """Re-index a single document in vector store."""
    doc = knowledge_document_crud.get(db, document_id=document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )

    if not os.path.exists(doc.file_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Physical file not found on disk for re-indexing."
        )

    try:
        # 1. Purge old vectors from ChromaDB
        vector_store.delete_document_chunks(document_id)

        # 2. Extract pages & chunk
        pages = document_loader.load_document(doc.file_path)
        chunk_meta = {
            "document_id": doc.id,
            "title": doc.title,
            "file_name": doc.file_name,
            "department_id": doc.department_id or 0,
            "service_id": doc.service_id or 0,
            "category": doc.doc_metadata.get("category", "guideline")
        }
        chunks = chunking_service.chunk_document_pages(pages, doc_metadata=chunk_meta)

        # 3. Add to ChromaDB
        vector_store.add_chunks(chunks)

        # 4. Save SQL chunk records
        knowledge_document_crud.add_chunks(db, document_id=doc.id, chunks_data=chunks)
        db.refresh(doc)
        logger.info("Successfully re-indexed document %d with %d chunks.", doc.id, len(chunks))
        return doc
    except Exception as e:
        logger.error("Re-indexing failed for document %d: %s", doc.id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Re-indexing failed: {str(e)}"
        )


@router.post(
    "/reindex-all",
    summary="Re-index All Documents (Admin Only)",
    description="Re-index all approved documents across the entire civic repository."
)
def reindex_all_documents(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.require_admin)
) -> Any:
    """Re-index all documents in the system."""
    docs = knowledge_document_crud.get_multi(db, limit=500)
    reindexed_count = 0
    errors = []

    for doc in docs:
        if os.path.exists(doc.file_path):
            try:
                vector_store.delete_document_chunks(doc.id)
                pages = document_loader.load_document(doc.file_path)
                chunk_meta = {
                    "document_id": doc.id,
                    "title": doc.title,
                    "file_name": doc.file_name,
                    "department_id": doc.department_id or 0,
                    "service_id": doc.service_id or 0,
                    "category": doc.doc_metadata.get("category", "guideline")
                }
                chunks = chunking_service.chunk_document_pages(pages, doc_metadata=chunk_meta)
                vector_store.add_chunks(chunks)
                knowledge_document_crud.add_chunks(db, document_id=doc.id, chunks_data=chunks)
                reindexed_count += 1
            except Exception as e:
                errors.append({"document_id": doc.id, "error": str(e)})

    return {
        "message": f"Successfully re-indexed {reindexed_count} documents.",
        "reindexed_count": reindexed_count,
        "total_documents": len(docs),
        "errors": errors,
        "total_vectors": vector_store.count()
    }


@router.delete(
    "/{document_id}",
    response_model=KnowledgeDocumentResponse,
    summary="Delete Document (Officer or Admin)",
    description="Delete a document and purge its vectors from ChromaDB."
)
def delete_document(
    document_id: int,
    db: Session = Depends(deps.get_db),
    current_officer: User = Depends(deps.require_officer_or_admin)
) -> Any:
    """Delete document and purge vector index."""
    doc = knowledge_document_crud.get(db, document_id=document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )

    # Purge vectors from ChromaDB
    vector_store.delete_document_chunks(document_id)

    # Delete file from storage if exists
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            logger.warning("Could not remove physical file %s: %s", doc.file_path, e)

    return knowledge_document_crud.delete(db, document_id=document_id)
