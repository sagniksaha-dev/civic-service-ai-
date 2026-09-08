from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.service import ServiceStatus


class ServiceRequirements(BaseModel):
    """Structured requirements schema for public services."""
    required_documents: List[str] = Field(
        default_factory=list,
        description="List of required non-sensitive document types (e.g. Utility Bill, Application Form, Address Proof)"
    )
    instructions: List[str] = Field(
        default_factory=list,
        description="Step-by-step submission instructions"
    )
    fee_amount: float = Field(default=0.0, description="Standard processing fee if any")


class EligibilityCriteria(BaseModel):
    """Structured eligibility criteria."""
    min_age: int = Field(default=18, description="Minimum age requirement")
    residency_required: bool = Field(default=True, description="Local residency required")
    details: List[str] = Field(default_factory=list, description="Specific eligibility conditions")


class ServiceBase(BaseModel):
    """Shared service properties."""
    department_id: int = Field(..., description="ID of associated department")
    name: str = Field(..., min_length=2, max_length=150, description="Service name")
    code: str = Field(..., min_length=2, max_length=50, description="Unique service code (e.g. WAT-CONN-01)")
    description: Optional[str] = Field(None, description="Service details and scope")
    requirements: Dict[str, Any] = Field(
        default_factory=lambda: {"required_documents": [], "instructions": [], "fee_amount": 0.0},
        description="JSON requirements including required documents and guidelines"
    )
    eligibility_criteria: Dict[str, Any] = Field(
        default_factory=lambda: {"min_age": 18, "residency_required": True, "details": []},
        description="JSON eligibility conditions"
    )
    processing_time_days: int = Field(default=15, ge=1, le=365, description="Standard SLA processing days")
    status: ServiceStatus = Field(default=ServiceStatus.ACTIVE, description="Service availability status")


class ServiceCreate(ServiceBase):
    """Schema for service creation."""
    pass


class ServiceUpdate(BaseModel):
    """Schema for updating a service."""
    department_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    requirements: Optional[Dict[str, Any]] = None
    eligibility_criteria: Optional[Dict[str, Any]] = None
    processing_time_days: Optional[int] = Field(None, ge=1, le=365)
    status: Optional[ServiceStatus] = None


class ServiceResponse(ServiceBase):
    """Schema for service response."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
