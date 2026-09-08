from typing import Any, Dict, List, Tuple
from groq import Groq
from app.core.config import settings
from app.core.logging import logger
from app.llm.base import BaseLLMProvider
from app.llm.retrieval_only import RetrievalOnlyProvider


class GroqProvider(BaseLLMProvider):
    """LLM Provider using Groq Cloud API (e.g. LLaMA-3 models)."""

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.fallback = RetrievalOnlyProvider()
        self.client = None

        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
                logger.info("Initialized Groq client with model %s", self.model)
            except Exception as e:
                logger.warning("Could not initialize Groq client: %s. Using fallback.", e)

    def generate_grounded_response(
        self,
        question: str,
        context_snippets: List[Dict[str, Any]],
        system_prompt: str
    ) -> Tuple[str, bool]:
        """Generate response via Groq API, falling back to retrieval-only if unconfigured."""
        if not self.client or not self.api_key:
            return self.fallback.generate_grounded_response(question, context_snippets, system_prompt)

        if not context_snippets:
            return self.fallback.NO_ANSWER_RESPONSE, False

        # Build context block
        context_block = "\n\n---\n\n".join([
            f"[Source: {s.get('metadata', {}).get('title', 'Document')} (Page {s.get('metadata', {}).get('page_number', 1)})]\n{s.get('text', '')}"
            for s in context_snippets
        ])

        user_content = f"Approved Reference Context:\n{context_block}\n\nCitizen Inquiry: {question}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,
                max_tokens=512
            )
            answer = response.choices[0].message.content.strip()
            # Check if model declared insufficient info
            is_grounded = "could not find" not in answer.lower() and "no information" not in answer.lower()
            return answer, is_grounded
        except Exception as e:
            logger.error("Groq API error: %s. Falling back to offline provider.", e)
            return self.fallback.generate_grounded_response(question, context_snippets, system_prompt)
