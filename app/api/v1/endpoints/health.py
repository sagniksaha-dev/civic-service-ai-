from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from app.core.config import settings


class HealthCheckResponse(BaseModel):
    """Schema for health and readiness check responses."""
    status: str = Field(default="healthy", description="Overall health status")
    service: str = Field(default="AI-Powered Civic Service Assistant", description="Service name")
    version: str = Field(default="1.0.0", description="API Version")
    environment: str = Field(default="development", description="Runtime environment")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp of check")
    llm_provider: str = Field(default="retrieval_only", description="Configured LLM Provider")
    database_status: str = Field(default="configured", description="Database health status")


router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Health and Readiness Check",
    description="Returns the current operational status, environment details, and provider configuration of the civic backend."
)
async def check_health() -> HealthCheckResponse:
    """Check backend operational health and readiness."""
    return HealthCheckResponse(
        status="healthy",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc),
        llm_provider=settings.LLM_PROVIDER,
        database_status="ready"
    )
