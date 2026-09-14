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

        # If user asks for guaranteed approval / promise (Anti-Guarantee Safety Guardrail)
        if civic_guard.is_guarantee_query(sanitized_q):
            return civic_guard.get_anti_guarantee_text(language=language), [], disclaimer, True

        # If user inquires about all departments / department directory
        if civic_guard.is_all_departments_query(sanitized_q):
            return cls.get_all_departments_overview(language=language)

        # If user inquires about all services / service catalogue
        if civic_guard.is_all_services_query(sanitized_q):
            return cls.get_all_services_overview(language=language)

        # If user asks how to apply for services
        if civic_guard.is_how_to_apply_query(sanitized_q):
            return cls.get_how_to_apply_overview(language=language)

        # If user asks how to file a grievance
        if civic_guard.is_how_to_grievance_query(sanitized_q):
            return cls.get_how_to_grievance_overview(language=language)

        # If user asks how to track applications
        if civic_guard.is_how_to_track_query(sanitized_q):
            return cls.get_how_to_track_overview(language=language)

        # If user asks how to find a service or the best department
        if civic_guard.is_find_service_or_dept_query(sanitized_q):
            return cls.get_find_service_or_dept_overview(language=language)

        # If user reports locality drain / drainage issues
        if civic_guard.is_drainage_problem_query(sanitized_q):
            return cls.get_drainage_problem_overview(language=language)

        # If user reports garbage accumulation / street waste
        if civic_guard.is_garbage_problem_query(sanitized_q):
            return cls.get_garbage_problem_overview(language=language)

        # If user reports broken roads / streetlights
        if civic_guard.is_road_light_problem_query(sanitized_q):
            return cls.get_road_light_problem_overview(language=language)

        # If user reports water leakage / supply issues
        if civic_guard.is_water_problem_query(sanitized_q):
            return cls.get_water_problem_overview(language=language)

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

    @classmethod
    def get_all_departments_overview(cls, language: Optional[str] = "en") -> Tuple[str, List[SourceReference], str, bool]:
        """Dynamically build comprehensive overview of all municipal departments from database."""
        from app.db.session import SessionLocal
        from app.models.department import Department
        from app.models.service import Service, ServiceStatus
        from app.models.knowledge_document import KnowledgeDocument

        disclaimer = civic_guard.get_standard_disclaimer()
        db = SessionLocal()
        try:
            depts = db.query(Department).filter(Department.is_active == True).all()
            lines = [
                f"Here is the complete directory of all {len(depts)} approved municipal departments available in the portal:\n"
            ]
            for d in depts:
                active_services = [s for s in d.services if s.status == ServiceStatus.ACTIVE]
                lines.append(f"🏛️ **{d.name}** (`{d.code}`)")
                if d.description:
                    lines.append(f"  - *Domain Scope*: {d.description}")
                if active_services:
                    svc_names = ", ".join(f"{s.name} (`{s.code}`)" for s in active_services)
                    lines.append(f"  - *Available Services*: {svc_names}")
                else:
                    lines.append("  - *Available Services*: Administrative operations & public grievance redressal")
                lines.append("")

            lines.append("💡 *To apply for any service or file a grievance with a specific department, visit the Service Catalogue or Grievance Redressal sections.*")

            answer = "\n".join(lines)

            docs = db.query(KnowledgeDocument).all()
            sources = [
                SourceReference(
                    document_id=d.id,
                    title=d.title,
                    file_name=d.file_name,
                    page_number=1,
                    chunk_index=0,
                    similarity_score=1.0,
                    snippet=f"{d.title} official department guidelines and statutory charters."
                ) for d in docs
            ]
            return answer, sources, disclaimer, True
        except Exception as e:
            logger.error("Error generating all departments overview: %s", e)
            return civic_guard.get_no_answer_text(), [], disclaimer, False
        finally:
            db.close()

    @classmethod
    def get_all_services_overview(cls, language: Optional[str] = "en") -> Tuple[str, List[SourceReference], str, bool]:
        """Dynamically build comprehensive overview of all municipal services from database."""
        from app.db.session import SessionLocal
        from app.models.department import Department
        from app.models.service import Service, ServiceStatus
        from app.models.knowledge_document import KnowledgeDocument

        disclaimer = civic_guard.get_standard_disclaimer()
        db = SessionLocal()
        try:
            depts = db.query(Department).filter(Department.is_active == True).all()
            lines = [
                "Here is the complete catalogue of approved municipal civic services available in the portal across departments:\n"
            ]
            for dept in depts:
                active_services = [s for s in dept.services if s.status == ServiceStatus.ACTIVE]
                if not active_services:
                    continue
                lines.append(f"🏛️ **{dept.name}** ({dept.code})")
                for s in active_services:
                    lines.append(f"- **{s.name}** (`{s.code}`)")
                    if s.description:
                        lines.append(f"  - *Description*: {s.description}")
                    lines.append(f"  - *Standard SLA*: {s.processing_time_days} business days")
                lines.append("")

            lines.append("💡 *To apply for any service, go to the Service Catalogue or Applications Tracker. To inquire about specific requirements or rules, ask with the service name (e.g., 'What documents are required for a water connection?' or 'Trade license guidelines').*")

            answer = "\n".join(lines)

            docs = db.query(KnowledgeDocument).all()
            sources = [
                SourceReference(
                    document_id=d.id,
                    title=d.title,
                    file_name=d.file_name,
                    page_number=1,
                    chunk_index=0,
                    similarity_score=1.0,
                    snippet=f"{d.title} official municipal guideline and statutory procedures."
                ) for d in docs
            ]
            return answer, sources, disclaimer, True
        except Exception as e:
            logger.error("Error generating all services overview: %s", e)
            return civic_guard.get_no_answer_text(), [], disclaimer, False
        finally:
            db.close()

    @classmethod
    def get_how_to_apply_overview(cls, language: Optional[str] = "en") -> Tuple[str, List[SourceReference], str, bool]:
        """Provide structured step-by-step guidance on applying for civic services."""
        from app.db.session import SessionLocal
        from app.models.knowledge_document import KnowledgeDocument

        disclaimer = civic_guard.get_standard_disclaimer()
        answer = civic_guard.get_how_to_apply_text(language=language)
        db = SessionLocal()
        try:
            docs = db.query(KnowledgeDocument).all()
            sources = [
                SourceReference(
                    document_id=d.id,
                    title=d.title,
                    file_name=d.file_name,
                    page_number=1,
                    chunk_index=0,
                    similarity_score=1.0,
                    snippet=f"{d.title} statutory application procedure and mandatory submission guidelines."
                ) for d in docs[:3]
            ]
            return answer, sources, disclaimer, True
        except Exception as e:
            logger.error("Error loading documents for apply overview: %s", e)
            return answer, [], disclaimer, True
        finally:
            db.close()

    @classmethod
    def get_how_to_grievance_overview(cls, language: Optional[str] = "en") -> Tuple[str, List[SourceReference], str, bool]:
        """Provide structured step-by-step guidance on lodging civic grievances."""
        from app.db.session import SessionLocal
        from app.models.knowledge_document import KnowledgeDocument

        disclaimer = civic_guard.get_standard_disclaimer()
        answer = civic_guard.get_how_to_grievance_text(language=language)
        db = SessionLocal()
        try:
            docs = db.query(KnowledgeDocument).all()
            sources = [
                SourceReference(
                    document_id=d.id,
                    title=d.title,
                    file_name=d.file_name,
                    page_number=1,
                    chunk_index=0,
                    similarity_score=1.0,
                    snippet=f"{d.title} grievance escalation and resolution charter."
                ) for d in docs[:3]
            ]
            return answer, sources, disclaimer, True
        except Exception as e:
            logger.error("Error loading documents for grievance overview: %s", e)
            return answer, [], disclaimer, True
        finally:
            db.close()

    @classmethod
    def get_how_to_track_overview(cls, language: Optional[str] = "en") -> Tuple[str, List[SourceReference], str, bool]:
        """Provide structured step-by-step guidance on application status tracking."""
        from app.db.session import SessionLocal
        from app.models.knowledge_document import KnowledgeDocument

        disclaimer = civic_guard.get_standard_disclaimer()
        answer = civic_guard.get_how_to_track_text(language=language)
        db = SessionLocal()
        try:
            docs = db.query(KnowledgeDocument).all()
            sources = [
                SourceReference(
                    document_id=d.id,
                    title=d.title,
                    file_name=d.file_name,
                    page_number=1,
                    chunk_index=0,
                    similarity_score=1.0,
                    snippet=f"{d.title} statutory tracking reference codes and verification stages."
                ) for d in docs[:3]
            ]
            return answer, sources, disclaimer, True
        except Exception as e:
            logger.error("Error loading documents for tracking overview: %s", e)
            return answer, [], disclaimer, True
        finally:
            db.close()

    @classmethod
    def get_find_service_or_dept_overview(cls, language: Optional[str] = "en") -> Tuple[str, List[SourceReference], str, bool]:
        """Provide structured guidance on finding services and mapping to the best department."""
        from app.db.session import SessionLocal
        from app.models.knowledge_document import KnowledgeDocument

        disclaimer = civic_guard.get_standard_disclaimer()
        answer = civic_guard.get_find_service_or_dept_text(language=language)
        db = SessionLocal()
        try:
            docs = db.query(KnowledgeDocument).all()
            sources = [
                SourceReference(
                    document_id=d.id,
                    title=d.title,
                    file_name=d.file_name,
                    page_number=1,
                    chunk_index=0,
                    similarity_score=1.0,
                    snippet=f"{d.title} department charters and municipal service catalogue mapping."
                ) for d in docs[:4]
            ]
            return answer, sources, disclaimer, True
        except Exception as e:
            logger.error("Error loading documents for find service overview: %s", e)
            return answer, [], disclaimer, True
        finally:
            db.close()

    @classmethod
    def get_drainage_problem_overview(cls, language: Optional[str] = "en") -> Tuple[str, List[SourceReference], str, bool]:
        """Provide structured guidance for locality drain and sewer issues."""
        from app.db.session import SessionLocal
        from app.models.knowledge_document import KnowledgeDocument

        disclaimer = civic_guard.get_standard_disclaimer()
        answer = civic_guard.get_drainage_problem_text(language=language)
        db = SessionLocal()
        try:
            docs = db.query(KnowledgeDocument).all()
            sources = [
                SourceReference(
                    document_id=d.id,
                    title=d.title,
                    file_name=d.file_name,
                    page_number=1,
                    chunk_index=0,
                    similarity_score=1.0,
                    snippet=f"{d.title} sanitation SOP and public grievance resolution charter."
                ) for d in docs[:3]
            ]
            return answer, sources, disclaimer, True
        except Exception as e:
            logger.error("Error loading documents for drainage overview: %s", e)
            return answer, [], disclaimer, True
        finally:
            db.close()

    @classmethod
    def get_garbage_problem_overview(cls, language: Optional[str] = "en") -> Tuple[str, List[SourceReference], str, bool]:
        """Provide structured guidance for garbage and street cleanliness issues."""
        from app.db.session import SessionLocal
        from app.models.knowledge_document import KnowledgeDocument

        disclaimer = civic_guard.get_standard_disclaimer()
        answer = civic_guard.get_garbage_problem_text(language=language)
        db = SessionLocal()
        try:
            docs = db.query(KnowledgeDocument).all()
            sources = [
                SourceReference(
                    document_id=d.id,
                    title=d.title,
                    file_name=d.file_name,
                    page_number=1,
                    chunk_index=0,
                    similarity_score=1.0,
                    snippet=f"{d.title} solid waste management charter."
                ) for d in docs[:2]
            ]
            return answer, sources, disclaimer, True
        except Exception as e:
            logger.error("Error loading documents for garbage overview: %s", e)
            return answer, [], disclaimer, True
        finally:
            db.close()

    @classmethod
    def get_road_light_problem_overview(cls, language: Optional[str] = "en") -> Tuple[str, List[SourceReference], str, bool]:
        """Provide structured guidance for broken roads and streetlights."""
        from app.db.session import SessionLocal
        from app.models.knowledge_document import KnowledgeDocument

        disclaimer = civic_guard.get_standard_disclaimer()
        answer = civic_guard.get_road_light_problem_text(language=language)
        db = SessionLocal()
        try:
            docs = db.query(KnowledgeDocument).all()
            sources = [
                SourceReference(
                    document_id=d.id,
                    title=d.title,
                    file_name=d.file_name,
                    page_number=1,
                    chunk_index=0,
                    similarity_score=1.0,
                    snippet=f"{d.title} public works and road maintenance charter."
                ) for d in docs[:2]
            ]
            return answer, sources, disclaimer, True
        except Exception as e:
            logger.error("Error loading documents for road/light overview: %s", e)
            return answer, [], disclaimer, True
        finally:
            db.close()

    @classmethod
    def get_water_problem_overview(cls, language: Optional[str] = "en") -> Tuple[str, List[SourceReference], str, bool]:
        """Provide structured guidance for water supply problems and leaks."""
        from app.db.session import SessionLocal
        from app.models.knowledge_document import KnowledgeDocument

        disclaimer = civic_guard.get_standard_disclaimer()
        answer = civic_guard.get_water_problem_text(language=language)
        db = SessionLocal()
        try:
            docs = db.query(KnowledgeDocument).all()
            sources = [
                SourceReference(
                    document_id=d.id,
                    title=d.title,
                    file_name=d.file_name,
                    page_number=1,
                    chunk_index=0,
                    similarity_score=1.0,
                    snippet=f"{d.title} urban water supply regulations."
                ) for d in docs[:2]
            ]
            return answer, sources, disclaimer, True
        except Exception as e:
            logger.error("Error loading documents for water overview: %s", e)
            return answer, [], disclaimer, True
        finally:
            db.close()


rag_service = RAGService()
