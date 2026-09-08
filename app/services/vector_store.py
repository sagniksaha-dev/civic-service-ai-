from pathlib import Path
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings
from app.core.logging import logger
from app.services.embedding import embedding_service


class VectorStoreService:
    """Manages persistent ChromaDB vector store for civic knowledge indexing and retrieval."""

    COLLECTION_NAME = "civic_knowledge_base"

    def __init__(self):
        self.persist_dir = settings.get_absolute_path(settings.VECTOR_STORE_PATH)
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        """Retrieve or initialize the Chroma collection with embedding function."""
        ef = embedding_service.get_embedding_function()
        try:
            return self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                embedding_function=ef,
                metadata={"description": "Approved Civic Service Knowledge Base"}
            )
        except Exception as e:
            logger.error("Error initializing Chroma collection: %s", e)
            return self.client.get_or_create_collection(name=self.COLLECTION_NAME)

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """
        Add extracted chunks to vector database.
        Each chunk is expected to have:
        - "text": str
        - "metadata": dict (e.g. document_id, title, file_name, page_number, chunk_index)
        Returns list of vector IDs.
        """
        if not chunks:
            return []

        ids = []
        documents = []
        metadatas = []

        for c in chunks:
            meta = c.get("metadata", {})
            doc_id = meta.get("document_id", "0")
            chunk_idx = meta.get("chunk_index", 0)
            vector_id = f"doc_{doc_id}_chk_{chunk_idx}"

            # Ensure all metadata values are str, int, float, or bool for ChromaDB
            clean_meta = {}
            for k, v in meta.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                elif v is not None:
                    clean_meta[k] = str(v)

            ids.append(vector_id)
            documents.append(c.get("text", ""))
            metadatas.append(clean_meta)

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        logger.info("Indexed %d chunks into vector store collection '%s'.", len(ids), self.COLLECTION_NAME)
        return ids

    def delete_document_chunks(self, document_id: int) -> int:
        """Remove all indexed chunks belonging to a document."""
        try:
            # Delete where metadata document_id matches
            self.collection.delete(
                where={"document_id": document_id}
            )
            logger.info("Deleted vector chunks for document_id %d.", document_id)
            return 1
        except Exception as e:
            logger.warning("Could not delete chunks for document_id %d: %s", document_id, e)
            return 0

    def query_similar(
        self,
        query_text: str,
        top_k: int = settings.SIMILARITY_TOP_K,
        department_id: Optional[int] = None,
        service_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search against vector store.
        Returns list of retrieved snippet objects with text, metadata, and distance.
        """
        if not query_text.strip():
            return []

        where_filter = None
        if department_id and service_id:
            where_filter = {"$and": [{"department_id": department_id}, {"service_id": service_id}]}
        elif department_id:
            where_filter = {"department_id": department_id}
        elif service_id:
            where_filter = {"service_id": service_id}

        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=top_k,
                where=where_filter
            )
        except Exception as e:
            logger.warning("Query failed with filter (%s), retrying without filter...", e)
            results = self.collection.query(
                query_texts=[query_text],
                n_results=top_k
            )

        output_snippets = []
        if not results or not results.get("documents") or not results["documents"][0]:
            return []

        docs = results["documents"][0]
        metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
        ids = results["ids"][0] if results.get("ids") else [""] * len(docs)

        for doc_text, meta, dist, vec_id in zip(docs, metas, distances, ids):
            # Calculate a normalized similarity score (0.0 to 1.0)
            sim_score = max(0.0, min(1.0, 1.0 - (dist / 2.0))) if dist is not None else 0.85
            output_snippets.append({
                "vector_id": vec_id,
                "text": doc_text,
                "metadata": meta,
                "distance": dist,
                "similarity_score": round(sim_score, 4)
            })

        return output_snippets

    def count(self) -> int:
        """Return total indexed chunks in collection."""
        return self.collection.count()


vector_store = VectorStoreService()
