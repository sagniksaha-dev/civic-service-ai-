from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.user import UserRole
from app.schemas.citizen import CitizenResponse


class UserBase(BaseModel):
    """Shared user properties."""
    name: str = Field(..., min_length=2, max_length=100, description="Full name of user")
    email: str = Field(..., min_length=3, max_length=255, description="Unique email address")
    role: UserRole = Field(default=UserRole.CITIZEN, description="Assigned user role")
    is_active: bool = Field(default=True, description="Active status")


class UserCreate(UserBase):
    """Schema for user registration / creation."""
    password: str = Field(..., min_length=6, max_length=100, description="Plain text password")


class UserUpdate(BaseModel):
    """Schema for updating user details."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[str] = Field(None, min_length=3, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6, max_length=100)


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    created_at: datetime
    updated_at: datetime
    citizen_profile: Optional[CitizenResponse] = None

    model_config = ConfigDict(from_attributes=True)
