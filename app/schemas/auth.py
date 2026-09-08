from typing import Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    """JWT Token response schema."""
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    name: str
    email: str


class TokenPayload(BaseModel):
    """Payload decoded from JWT access token."""
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None


class LoginRequest(BaseModel):
    """User credentials for authentication."""
    email: str = Field(..., min_length=3, description="User email address")
    password: str = Field(..., min_length=4, description="User password")
