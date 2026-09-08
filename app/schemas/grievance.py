from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.grievance import GrievanceStatus


class GrievanceCreate(BaseModel):
    """Schema for submitting a citizen grievance."""
    department_id: int = Field(..., description="Target department ID")
    service_id: Optional[int] = Field(None, description="Optional associated service ID")
    subject: str = Field(..., min_length=3, max_length=200, description="Subject of complaint")
    details: str = Field(..., min_length=10, description="Detailed explanation of grievance")


class GrievanceOfficerResponse(BaseModel):
    """Schema for officer responding to and updating a grievance."""
    response: str = Field(..., min_length=3, description="Officer response / resolution details")
    status: GrievanceStatus = Field(default=GrievanceStatus.RESOLVED, description="Updated status")


class GrievanceResponse(BaseModel):
    """Schema for grievance response."""
    id: int
    citizen_id: int
    department_id: int
    service_id: Optional[int] = None
    subject: str
    details: str
    status: GrievanceStatus
    response: Optional[str] = None
    assigned_officer_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
