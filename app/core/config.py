import os
from pathlib import Path
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application Settings and Environment Variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Project Information
    PROJECT_NAME: str = "AI-Powered Civic Service Assistant"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    VERSION: str = "1.0.0"

    # Base Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    # Security & JWT Token
    SECRET_KEY: str = "civic_ai_assistant_development_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database Configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "civic_ai_db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "sqlite:///./civic_ai.db"

    # CORS Configuration
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "http://localhost:8000"
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return v

    # LLM & AI Provider Configuration
    LLM_PROVIDER: str = "auto"  # "auto", "gemini", "groq", "openai", "retrieval_only"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # RAG & Knowledge Base Paths
    VECTOR_STORE_TYPE: str = "chroma"  # "chroma", "faiss"
    VECTOR_STORE_PATH: str = "data/vector_index"
    KNOWLEDGE_BASE_PATH: str = "data/knowledge_base"
    STORAGE_PATH: str = "data/storage"

    # Document Ingestion Settings
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    SIMILARITY_TOP_K: int = 4

    def get_absolute_path(self, relative_path: str) -> Path:
        """Resolve a relative path against the project base directory."""
        path = self.BASE_DIR / relative_path
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
