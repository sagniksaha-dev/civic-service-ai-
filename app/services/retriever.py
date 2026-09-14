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
        """Retrieve matching document snippets from the vector store with domain prioritization."""
        snippets = vector_store.query_similar(
            query_text=query,
            top_k=max(top_k, 6),
            department_id=department_id,
            service_id=service_id
        )

        if not snippets:
            return []

        # Check for strong topic congruence
        q_lower = query.lower()
        domain_mapping = {
            "birth": ["birth", "vital statistics", "civil registration"],
            "death": ["death", "vital statistics", "civil registration"],
            "trade": ["trade license", "commerce", "renewal"],
            "water": ["water", "pipeline", "supply"],
            "property_tax": ["property tax", "tax assessment", "rebate"],
            "building": ["building plan", "sanction", "urban planning"],
            "fire": ["fire safety", "fire noc", "disaster management"],
            "food": ["food safety", "food hygiene", "fssai"],
            "sanitation": ["solid waste", "sanitation", "garbage"],
            "greenery": ["tree", "greenery", "parks"],
            "traffic": ["transport", "traffic", "road digging"],
            "grievance": ["grievance", "complaint", "redressal"]
        }

        matched_domain = None
        for dom, kws in domain_mapping.items():
            if any(kw in q_lower for kw in kws):
                matched_domain = dom
                break

        if matched_domain:
            target_kws = domain_mapping[matched_domain]
            congruent_snippets = []
            other_snippets = []
            for s in snippets:
                text = s.get("text", "").lower()
                title = s.get("metadata", {}).get("title", "").lower()
                if any(kw in text or kw in title for kw in target_kws):
                    congruent_snippets.append(s)
                else:
                    other_snippets.append(s)

            # If we found congruent snippets, prioritize them and exclude contradictory ones
            if congruent_snippets:
                snippets = congruent_snippets[:top_k]
            else:
                snippets = snippets[:top_k]
        else:
            snippets = snippets[:top_k]

        return snippets

    @staticmethod
    def format_sources(snippets: List[Dict[str, Any]]) -> List[SourceReference]:
        """Convert retrieved snippet metadata into deduplicated SourceReference objects."""
        sources = []
        seen_docs = set()

        for s in snippets:
            meta = s.get("metadata", {})
            doc_id = meta.get("document_id")
            title = meta.get("title", "Approved Civic Guideline")
            page_no = meta.get("page_number", 1)
            chunk_idx = meta.get("chunk_index", 0)

            doc_key = (doc_id, title, page_no)
            if doc_key in seen_docs:
                continue

            seen_docs.add(doc_key)
            sources.append(SourceReference(
                document_id=doc_id,
                title=title,
                file_name=meta.get("file_name", "document.pdf"),
                page_number=page_no,
                chunk_index=chunk_idx,
                similarity_score=s.get("similarity_score"),
                snippet=s.get("text", "")[:300] + ("..." if len(s.get("text", "")) > 300 else "")
            ))
        return sources


retriever_service = RetrieverService()
