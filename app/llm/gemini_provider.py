import json
from typing import Any, Dict, List, Tuple
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.llm.base import BaseLLMProvider
from app.llm.retrieval_only import RetrievalOnlyProvider


class GeminiProvider(BaseLLMProvider):
    """LLM Provider using Google Gemini REST API (e.g. gemini-1.5-flash, gemini-2.0-flash)."""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL or "gemini-1.5-flash"
        self.fallback = RetrievalOnlyProvider()

    def generate_grounded_response(
        self,
        question: str,
        context_snippets: List[Dict[str, Any]],
        system_prompt: str
    ) -> Tuple[str, bool]:
        """Generate response via Google Gemini API, falling back to retrieval-only if unconfigured."""
        if not self.api_key:
            return self.fallback.generate_grounded_response(question, context_snippets, system_prompt)

        if not context_snippets:
            return self.fallback.NO_ANSWER_RESPONSE, False

        # Build context block
        context_block = "\n\n---\n\n".join([
            f"[Source: {s.get('metadata', {}).get('title', 'Document')} (Page {s.get('metadata', {}).get('page_number', 1)})]\n{s.get('text', '')}"
            for s in context_snippets
        ])

        user_content = (
            f"{system_prompt}\n\n"
            f"Approved Reference Context:\n{context_block}\n\n"
            f"Citizen Inquiry: {question}\n\n"
            f"Please provide an accurate, grounded, helpful response based strictly on the approved reference context."
        )

        endpoint_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": user_content}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 800,
            }
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(
                    endpoint_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts:
                            answer = parts[0].get("text", "").strip()
                            is_grounded = "could not find" not in answer.lower() and "no information" not in answer.lower()
                            return answer, is_grounded

                logger.warning("Gemini API non-200 or empty response (%s): %s", res.status_code, res.text[:200])
                return self.fallback.generate_grounded_response(question, context_snippets, system_prompt)

        except Exception as e:
            logger.error("Gemini API error: %s. Falling back to offline provider.", e)
            return self.fallback.generate_grounded_response(question, context_snippets, system_prompt)
