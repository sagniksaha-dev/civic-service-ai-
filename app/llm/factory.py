from app.core.config import settings
from app.core.logging import logger
from app.llm.base import BaseLLMProvider
from app.llm.retrieval_only import RetrievalOnlyProvider
from app.llm.gemini_provider import GeminiProvider
from app.llm.groq_provider import GroqProvider
from app.llm.openai_provider import OpenAIProvider


class LLMFactory:
    """Factory to instantiate the appropriate LLM provider based on application configuration."""

    _instances: dict[str, BaseLLMProvider] = {}

    @classmethod
    def get_provider(cls) -> BaseLLMProvider:
        """Get or initialize singleton LLM provider instance."""
        provider_name = settings.LLM_PROVIDER.lower().strip()

        # Auto-selection logic if "auto" or empty
        if provider_name in ["auto", ""]:
            if settings.GEMINI_API_KEY:
                provider_name = "gemini"
            elif settings.GROQ_API_KEY:
                provider_name = "groq"
            elif settings.OPENAI_API_KEY:
                provider_name = "openai"
            else:
                provider_name = "retrieval_only"

        if provider_name in cls._instances:
            return cls._instances[provider_name]

        instance: BaseLLMProvider
        if provider_name == "gemini" and settings.GEMINI_API_KEY:
            instance = GeminiProvider()
        elif provider_name == "groq" and settings.GROQ_API_KEY:
            instance = GroqProvider()
        elif provider_name == "openai" and settings.OPENAI_API_KEY:
            instance = OpenAIProvider()
        else:
            if provider_name not in ["retrieval_only", "auto", ""]:
                logger.info("Provider '%s' selected without active API key; defaulting to 'retrieval_only'.", provider_name)
            instance = RetrievalOnlyProvider()

        cls._instances[provider_name] = instance
        return instance


llm_factory = LLMFactory()
