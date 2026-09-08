from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple


class BaseLLMProvider(ABC):
    """Abstract Base Class for Grounded Civic LLM Providers."""

    @abstractmethod
    def generate_grounded_response(
        self,
        question: str,
        context_snippets: List[Dict[str, Any]],
        system_prompt: str
    ) -> Tuple[str, bool]:
        """
        Generate grounded answer based strictly on provided context snippets.
        Returns:
            (answer_text: str, is_grounded: bool)
        """
        pass
