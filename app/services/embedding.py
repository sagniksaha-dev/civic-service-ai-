from typing import List
from chromadb.utils import embedding_functions
from app.core.config import settings
from app.core.logging import logger


class EmbeddingService:
    """Service to generate dense vector embeddings for text chunks and queries."""

    def __init__(self):
        try:
            # ChromaDB default embedding function using ONNX runtime / all-MiniLM-L6-v2
            self._ef = embedding_functions.DefaultEmbeddingFunction()
            logger.info("Initialized default ChromaDB embedding function.")
        except Exception as e:
            logger.warning("Could not initialize default embedding function (%s), using fallback.", e)
            self._ef = None

    def get_embedding_function(self):
        """Return the embedding function for Chroma collections."""
        return self._ef

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a list of text strings."""
        if not texts:
            return []
        if self._ef is not None:
            return self._ef(texts)
        # Fallback deterministic normalized pseudo-embedding for testing environments
        return [self._fallback_embed(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding vector for a single search query."""
        results = self.embed_texts([query])
        return results[0] if results else [0.0] * 384

    @staticmethod
    def _fallback_embed(text: str, dim: int = 384) -> List[float]:
        """Deterministic fallback embedding generator."""
        import hashlib
        import math
        vec = [0.0] * dim
        for word in text.lower().split():
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            vec[idx] += 1.0
        # Normalize
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]


embedding_service = EmbeddingService()
