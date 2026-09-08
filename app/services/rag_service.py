from typing import Any, Dict, List, Optional, Tuple
from app.core.logging import logger
from app.schemas.chat import SourceReference
from app.services.civic_guard import civic_guard
from app.services.prompt_builder import prompt_builder
from app.services.retriever import retriever_service
from app.llm.factory import llm_factory


class RAGService:
    """Orchestrates end-to-end grounded Retrieval-Augmented Generation for civic queries."""

    @classmethod
    def answer_civic_query(
        cls,
        question: str,
        department_id: Optional[int] = None,
        service_id: Optional[int] = None,
        language: Optional[str] = "en",
        top_k: int = 4
    ) -> Tuple[str, List[SourceReference], str, bool]:
        """
        Execute RAG workflow:
        1. Sanitize inquiry.
        2. Retrieve relevant approved snippets from vector store.
        3. Enforce grounding and invoke configured LLM provider.
        4. Attach citations and disclaimer.
        Returns:
            (answer_text, sources, disclaimer, is_grounded)
        """
        sanitized_q, had_sensitive = civic_guard.sanitize_input(question)
        if had_sensitive:
            logger.info("Redacted sensitive identifier keywords in citizen inquiry.")

        disclaimer = civic_guard.get_standard_disclaimer()

        # If user sends a greeting or asks for guidance
        if civic_guard.is_greeting(sanitized_q):
            return civic_guard.get_greeting_help_text(), [], disclaimer, True

        # 1. Retrieve context
        snippets = retriever_service.retrieve_context(
            query=sanitized_q,
            top_k=top_k,
            department_id=department_id,
            service_id=service_id
        )

        # If no snippets found in vector database
        if not snippets:
            logger.info("No matching document snippets retrieved for query: '%s'", question[:50])
            return civic_guard.get_no_answer_text(), [], disclaimer, False

        # 2. Invoke LLM provider with language-tailored prompt
        provider = llm_factory.get_provider()
        system_prompt = prompt_builder.get_system_prompt(language=language)
        answer, is_grounded = provider.generate_grounded_response(
            question=sanitized_q,
            context_snippets=snippets,
            system_prompt=system_prompt
        )

        # 3. Format sources
        sources = retriever_service.format_sources(snippets) if is_grounded else []

        return answer, sources, disclaimer, is_grounded


rag_service = RAGService()
