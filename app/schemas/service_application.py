from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.service_application import ApplicationStatus


class ServiceApplicationCreate(BaseModel):
    """Schema for submitting a service application."""
    service_id: int = Field(..., description="Target service ID")
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Application form submission data (no real identity documents permitted)"
    )


class ServiceApplicationStatusUpdate(BaseModel):
    """Schema for officer review and status transitions."""
    status: ApplicationStatus = Field(..., description="New application status")
    officer_remarks: Optional[str] = Field(None, description="Officer review notes or feedback")


class ServiceApplicationResponse(BaseModel):
    """Schema for service application response."""
    id: int
    citizen_id: int
    service_id: int
    reference_no: str
    payload: Dict[str, Any]
    status: ApplicationStatus
    officer_remarks: Optional[str] = None
    reviewed_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
