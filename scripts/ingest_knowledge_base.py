import os
import sys
from pathlib import Path
import shutil

# Ensure app root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.core.logging import logger
from app.db.session import SessionLocal
from app.models.department import Department
from app.models.service import Service
from app.models.user import User, UserRole
from app.models.knowledge_document import KnowledgeDocument
from app.crud.knowledge_document import knowledge_document_crud
from app.services.document_loader import document_loader
from app.services.chunking import chunking_service
from app.services.vector_store import vector_store


def ingest_knowledge_base_folder() -> None:
    """Ingest and index all documents located in data/knowledge_base/ into database and ChromaDB."""
    db = SessionLocal()
    kb_dir = settings.get_absolute_path(settings.KNOWLEDGE_BASE_PATH)
    storage_dir = settings.get_absolute_path(settings.STORAGE_PATH)

    try:
        # Find admin or officer user to attribute uploads
        officer = db.query(User).filter(User.role.in_([UserRole.ADMIN, UserRole.DEPARTMENT_OFFICER])).first()
        if not officer:
            logger.error("No Admin or Officer user found in database. Please run scripts/create_admin.py first.")
            return

        supported_files = [
            p for p in kb_dir.glob("*") if p.suffix.lower() in document_loader.SUPPORTED_EXTENSIONS
        ]

        if not supported_files:
            logger.info("No documents found in %s", kb_dir)
            return

        logger.info("Found %d documents in %s to index.", len(supported_files), kb_dir)

        # Department / Service keyword matching map
        dept_lookup = {
            "water": "UWSD",
            "tax": "REV",
            "property": "REV",
            "trade": "TRADE",
            "license": "TRADE",
            "birth": "CIV-REG",
            "death": "CIV-REG",
            "building": "URB-PLAN",
            "plan": "URB-PLAN",
            "grievance": "UWSD",
            "fire": "FIRE-EMERG",
            "emerg": "FIRE-EMERG",
            "food": "DPH-FOOD",
            "hygiene": "DPH-FOOD",
            "sanitation": "DPS-SAN",
            "waste": "DPS-SAN",
            "green": "ENV-PARKS",
            "park": "ENV-PARKS",
            "tree": "ENV-PARKS",
            "transport": "MUNI-TRANS",
            "traffic": "MUNI-TRANS",
            "road": "MUNI-TRANS"
        }

        for file_path in supported_files:
            title = file_path.stem.replace("_", " ").title()
            logger.info("Processing: %s ('%s')...", file_path.name, title)

            # Copy to storage
            dest_file = storage_dir / file_path.name
            shutil.copy2(file_path, dest_file)

            # Match department ID
            matched_dept_id = None
            matched_service_id = None
            lower_name = file_path.stem.lower()
            for kw, code in dept_lookup.items():
                if kw in lower_name:
                    dept = db.query(Department).filter(Department.code == code).first()
                    if dept:
                        matched_dept_id = dept.id
                        # Try match first service in department
                        srv = db.query(Service).filter(Service.department_id == dept.id).first()
                        if srv:
                            matched_service_id = srv.id
                    break

            # Check if document record already exists
            existing_doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.file_name == file_path.name).first()
            if existing_doc:
                vector_store.delete_document_chunks(existing_doc.id)
                db.delete(existing_doc)
                db.commit()

            # Create DB entry
            doc_record = knowledge_document_crud.create(
                db=db,
                title=title,
                file_name=file_path.name,
                file_path=str(dest_file),
                file_type=file_path.suffix.lower(),
                department_id=matched_dept_id,
                service_id=matched_service_id,
                uploaded_by_id=officer.id,
                doc_metadata={"source_dir": "knowledge_base", "ingested_by": officer.email}
            )

            # Extract pages & chunk
            pages = document_loader.load_document(str(dest_file))
            chunk_meta = {
                "document_id": doc_record.id,
                "title": doc_record.title,
                "file_name": doc_record.file_name,
                "department_id": matched_dept_id or 0,
                "service_id": matched_service_id or 0,
                "category": "official_guideline"
            }
            chunks = chunking_service.chunk_document_pages(pages, doc_metadata=chunk_meta)

            # Add to ChromaDB
            vector_store.add_chunks(chunks)

            # Save SQL chunk records
            knowledge_document_crud.add_chunks(db, document_id=doc_record.id, chunks_data=chunks)
            logger.info("Ingested '%s' -> %d chunks indexed into vector database.", title, len(chunks))

        print("\n" + "=" * 60)
        print(f"Knowledge Base Ingestion Complete! Total Vector Store Chunks: {vector_store.count()}")
        print("=" * 60)

    except Exception as e:
        logger.error("Ingestion failed: %s", e)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    ingest_knowledge_base_folder()
