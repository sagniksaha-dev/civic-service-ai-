from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class CitizenAddress(BaseModel):
    """Structured citizen address schema."""
    street: str = Field(default="", description="Street or locality")
    city: str = Field(default="", description="City or town")
    district: str = Field(default="", description="District")
    state: str = Field(default="", description="State")
    postal_code: str = Field(default="", description="Postal PIN code")


class CitizenBase(BaseModel):
    """Shared citizen profile fields."""
    phone: Optional[str] = Field(None, description="Contact phone number")
    address: Dict[str, Any] = Field(
        default_factory=lambda: {
            "street": "",
            "city": "",
            "district": "",
            "state": "",
            "postal_code": ""
        },
        description="Structured residential address"
    )
    date_of_birth: Optional[str] = Field(None, description="Date of birth (YYYY-MM-DD)")


class CitizenCreate(CitizenBase):
    """Schema for creating citizen profile (user_id optional if extracted from auth token)."""
    user_id: Optional[int] = None


class CitizenUpdate(BaseModel):
    """Schema for updating citizen profile."""
    phone: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    date_of_birth: Optional[str] = None


class CitizenResponse(CitizenBase):
    """Schema for citizen response."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
