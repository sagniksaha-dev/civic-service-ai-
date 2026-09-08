from app.core.config import settings
from app.core.logging import logger
from app.llm.base import BaseLLMProvider
from app.llm.retrieval_only import RetrievalOnlyProvider
from app.llm.groq_provider import GroqProvider


class LLMFactory:
    """Factory to instantiate the appropriate LLM provider based on application configuration."""

    _instances: dict[str, BaseLLMProvider] = {}

    @classmethod
    def get_provider(cls) -> BaseLLMProvider:
        """Get or initialize singleton LLM provider instance."""
        provider_name = settings.LLM_PROVIDER.lower().strip()

        if provider_name in cls._instances:
            return cls._instances[provider_name]

        if provider_name == "groq" and settings.GROQ_API_KEY:
            instance = GroqProvider()
        else:
            if provider_name not in ["retrieval_only", ""]:
                logger.info("Provider '%s' selected without API key; using 'retrieval_only'.", provider_name)
            instance = RetrievalOnlyProvider()

        cls._instances[provider_name] = instance
        return instance


llm_factory = LLMFactory()
