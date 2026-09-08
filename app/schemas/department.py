from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DepartmentBase(BaseModel):
    """Shared department properties."""
    name: str = Field(..., min_length=2, max_length=150, description="Department name (e.g. Public Works Department)")
    code: str = Field(..., min_length=2, max_length=50, description="Unique department code (e.g. PWD)")
    description: Optional[str] = Field(None, description="Department responsibilities and description")
    is_active: bool = Field(default=True, description="Active status")


class DepartmentCreate(DepartmentBase):
    """Schema for creating a department."""
    pass


class DepartmentUpdate(BaseModel):
    """Schema for updating a department."""
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    """Schema for department response."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
