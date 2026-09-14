import json
from typing import Any, Dict, List, Tuple
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.llm.base import BaseLLMProvider
from app.llm.retrieval_only import RetrievalOnlyProvider


class OpenAIProvider(BaseLLMProvider):
    """LLM Provider using OpenAI API (e.g. gpt-4o-mini, gpt-4o)."""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL or "gpt-4o-mini"
        self.fallback = RetrievalOnlyProvider()

    def generate_grounded_response(
        self,
        question: str,
        context_snippets: List[Dict[str, Any]],
        system_prompt: str
    ) -> Tuple[str, bool]:
        """Generate response via OpenAI API, falling back to retrieval-only if unconfigured."""
        if not self.api_key:
            return self.fallback.generate_grounded_response(question, context_snippets, system_prompt)

        if not context_snippets:
            return self.fallback.NO_ANSWER_RESPONSE, False

        # Build context block
        context_block = "\n\n---\n\n".join([
            f"[Source: {s.get('metadata', {}).get('title', 'Document')} (Page {s.get('metadata', {}).get('page_number', 1)})]\n{s.get('text', '')}"
            for s in context_snippets
        ])

        user_content = f"Approved Reference Context:\n{context_block}\n\nCitizen Inquiry: {question}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.1,
            "max_tokens": 800
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )

                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        answer = choices[0]["message"]["content"].strip()
                        is_grounded = "could not find" not in answer.lower() and "no information" not in answer.lower()
                        return answer, is_grounded

                logger.warning("OpenAI API non-200 (%s): %s", res.status_code, res.text[:200])
                return self.fallback.generate_grounded_response(question, context_snippets, system_prompt)

        except Exception as e:
            logger.error("OpenAI API error: %s. Falling back to offline provider.", e)
            return self.fallback.generate_grounded_response(question, context_snippets, system_prompt)
