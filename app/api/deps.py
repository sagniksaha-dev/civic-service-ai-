from typing import Generator, List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.citizen import Citizen
from app.crud.user import user_crud

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/token",
    auto_error=False
)


def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> User:
    """Validate JWT token and resolve current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_id_str: Optional[str] = payload.get("sub")
    if not user_id_str:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    user = user_crud.get(db, user_id=user_id)
    if not user:
        raise credentials_exception

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verify that current user account is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    return current_user


class RoleChecker:
    """Dependency for Role-Based Access Control (RBAC)."""

    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {[r.value for r in self.allowed_roles]}"
            )
        return current_user


# Pre-configured RBAC dependencies
require_admin = RoleChecker([UserRole.ADMIN])
require_officer = RoleChecker([UserRole.DEPARTMENT_OFFICER])
require_officer_or_admin = RoleChecker([UserRole.ADMIN, UserRole.DEPARTMENT_OFFICER])
require_citizen = RoleChecker([UserRole.CITIZEN])
require_any_authenticated = RoleChecker([UserRole.ADMIN, UserRole.DEPARTMENT_OFFICER, UserRole.CITIZEN])


def get_current_citizen_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Citizen:
    """Resolve citizen profile for current user, creating one if not exists."""
    if current_user.citizen_profile:
        return current_user.citizen_profile

    # Create profile on the fly if missing
    profile = Citizen(
        user_id=current_user.id,
        phone="",
        address={"street": "", "city": "", "district": "", "state": "", "postal_code": ""}
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def verify_citizen_ownership(current_user: User, resource_citizen_id: int) -> None:
    """Verify that citizen user is accessing their own record, or has Officer/Admin privileges."""
    if current_user.role in [UserRole.ADMIN, UserRole.DEPARTMENT_OFFICER]:
        return

    if not current_user.citizen_profile or current_user.citizen_profile.id != resource_citizen_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only access your own civic records."
        )
