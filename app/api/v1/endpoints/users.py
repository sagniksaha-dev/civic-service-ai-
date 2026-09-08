from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.user import user_crud
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter()


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="List Users (Admin Only)",
    description="Retrieve all registered users with optional role filtering."
)
def list_users(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    role: Optional[UserRole] = None,
    current_admin: User = Depends(deps.require_admin)
) -> Any:
    """List users with pagination (Admin only)."""
    users = user_crud.get_multi(db, skip=skip, limit=limit, role=role)
    return users


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create User with Role (Admin Only)",
    description="Create a user with explicit role assignment (Admin, Department Officer, Citizen)."
)
def create_user_admin(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.require_admin)
) -> Any:
    """Create user with role (Admin only)."""
    existing_user = user_crud.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )
    return user_crud.create(db, obj_in=user_in)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get User by ID",
    description="Retrieve specific user details. Allowed for Admin or the user themselves."
)
def get_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Get user by ID."""
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user profile."
        )

    user = user_crud.get(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    return user


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update User",
    description="Update user profile. Non-admin users cannot change their role."
)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Update user by ID."""
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user profile."
        )

    user = user_crud.get(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    # Non-admins cannot elevate roles or deactivate others
    if current_user.role != UserRole.ADMIN:
        user_in.role = None
        user_in.is_active = None

    return user_crud.update(db, db_obj=user, obj_in=user_in)
