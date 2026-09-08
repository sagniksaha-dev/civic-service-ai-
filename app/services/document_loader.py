import os
from pathlib import Path
from typing import Dict, List, Tuple
from pypdf import PdfReader
from docx import Document as DocxDocument
from app.core.logging import logger


class DocumentLoaderService:
    """Service for parsing and extracting text and metadata from PDF, DOCX, TXT, and Markdown files."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

    @classmethod
    def load_document(cls, file_path: str) -> List[Dict[str, any]]:
        """
        Extract text from file.
        Returns a list of page/section dictionaries:
        [{"page_number": int, "text": str}]
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document file not found at '{file_path}'")

        ext = path.suffix.lower()
        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file extension '{ext}'. Supported: {cls.SUPPORTED_EXTENSIONS}")

        if ext == ".pdf":
            return cls._load_pdf(path)
        elif ext == ".docx":
            return cls._load_docx(path)
        elif ext in [".txt", ".md"]:
            return cls._load_text(path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    @staticmethod
    def _load_pdf(path: Path) -> List[Dict[str, any]]:
        """Extract text from PDF pages."""
        pages = []
        reader = PdfReader(str(path))
        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                pages.append({"page_number": idx + 1, "text": text})
        return pages

    @staticmethod
    def _load_docx(path: Path) -> List[Dict[str, any]]:
        """Extract text from DOCX paragraphs."""
        doc = DocxDocument(str(path))
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text.strip())

        text_content = "\n\n".join(full_text)
        if not text_content:
            return []
        return [{"page_number": 1, "text": text_content}]

    @staticmethod
    def _load_text(path: Path) -> List[Dict[str, any]]:
        """Extract text from TXT or Markdown file."""
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read().strip()
        if not content:
            return []
        return [{"page_number": 1, "text": content}]


document_loader = DocumentLoaderService()
