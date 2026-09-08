from typing import Any, Dict, List
from app.core.config import settings


class ChunkingService:
    """Service to split extracted document text into overlapping chunks with metadata."""

    def __init__(self, chunk_size: int = settings.CHUNK_SIZE, chunk_overlap: int = settings.CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        """Split text using paragraph/sentence-aware character boundaries."""
        if not text:
            return []

        text = text.strip()
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            chunk = text[start:end]

            # If not at the end of text, try to find a natural sentence or paragraph break
            if end < text_length:
                last_newline = chunk.rfind("\n\n")
                if last_newline > self.chunk_size // 2:
                    end = start + last_newline + 2
                    chunk = text[start:end]
                else:
                    last_period = chunk.rfind(". ")
                    if last_period > self.chunk_size // 2:
                        end = start + last_period + 2
                        chunk = text[start:end]

            chunk_cleaned = chunk.strip()
            if chunk_cleaned:
                chunks.append(chunk_cleaned)

            if end >= text_length:
                break

            # Advance with overlap
            start = max(end - self.chunk_overlap, start + 1)

        return chunks

    def chunk_document_pages(
        self,
        pages: List[Dict[str, Any]],
        doc_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Split a list of page objects into a list of chunk dictionaries with metadata.
        Returns:
        [
            {
                "chunk_index": int,
                "page_number": int,
                "text": str,
                "metadata": dict
            }
        ]
        """
        all_chunks = []
        chunk_idx = 0

        for page in pages:
            page_num = page.get("page_number", 1)
            page_text = page.get("text", "")
            raw_chunks = self.split_text(page_text)

            for text_chunk in raw_chunks:
                chunk_meta = dict(doc_metadata)
                chunk_meta.update({
                    "chunk_index": chunk_idx,
                    "page_number": page_num
                })

                all_chunks.append({
                    "chunk_index": chunk_idx,
                    "page_number": page_num,
                    "text": text_chunk,
                    "metadata": chunk_meta
                })
                chunk_idx += 1

        return all_chunks


chunking_service = ChunkingService()
