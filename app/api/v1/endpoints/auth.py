from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core.security import create_access_token
from app.crud.user import user_crud
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User",
    description="Public registration for citizens. Defaults to citizen role."
)
def register(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db)
) -> Any:
    """Register a new user account."""
    existing_user = user_crud.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # Protect against unprivileged users self-assigning Admin role via public registration
    if user_in.role == UserRole.ADMIN:
        user_in.role = UserRole.CITIZEN

    user = user_crud.create(db, obj_in=user_in)
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="User Login (JSON Body)",
    description="Authenticate user with email & password and return a signed JWT access token."
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    """Authenticate user and return JWT bearer token."""
    user = user_crud.authenticate(db, email=login_data.email, password=login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )

    access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
        extra_claims={"email": user.email, "name": user.name}
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role.value,
        user_id=user.id,
        name=user.name,
        email=user.email
    )


@router.post(
    "/token",
    response_model=Token,
    include_in_schema=False,
    summary="OAuth2 Form Login (for Swagger UI)"
)
def login_for_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(deps.get_db)
) -> Any:
    """OAuth2 compatible token login for interactive Swagger UI docs."""
    user = user_crud.authenticate(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )

    access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
        extra_claims={"email": user.email, "name": user.name}
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role.value,
        user_id=user.id,
        name=user.name,
        email=user.email
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User Profile",
    description="Retrieve details of currently logged in user."
)
def get_current_user_profile(
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Return current user."""
    return current_user
