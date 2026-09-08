from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.citizen import citizen_crud
from app.models.citizen import Citizen
from app.models.user import User, UserRole
from app.schemas.citizen import CitizenResponse, CitizenUpdate

router = APIRouter()


@router.get(
    "/me",
    response_model=CitizenResponse,
    summary="Get My Citizen Profile",
    description="Retrieve the current citizen's profile and address."
)
def get_my_profile(
    citizen: Citizen = Depends(deps.get_current_citizen_profile)
) -> Any:
    """Get current citizen profile."""
    return citizen


@router.put(
    "/me",
    response_model=CitizenResponse,
    summary="Update My Citizen Profile",
    description="Update the current citizen's contact phone or structured address."
)
def update_my_profile(
    citizen_in: CitizenUpdate,
    db: Session = Depends(deps.get_db),
    citizen: Citizen = Depends(deps.get_current_citizen_profile)
) -> Any:
    """Update current citizen profile."""
    return citizen_crud.update(db, db_obj=citizen, obj_in=citizen_in)


@router.get(
    "/",
    response_model=List[CitizenResponse],
    summary="List Citizen Profiles (Admin Only)",
    description="Retrieve all citizen profiles in the system."
)
def list_citizens(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_admin: User = Depends(deps.require_admin)
) -> Any:
    """List citizen profiles (Admin only)."""
    return citizen_crud.get_multi(db, skip=skip, limit=limit)


@router.get(
    "/{citizen_id}",
    response_model=CitizenResponse,
    summary="Get Citizen Profile by ID",
    description="Retrieve specific citizen profile. Allowed for Admin, Officer, or owner."
)
def get_citizen(
    citizen_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Get citizen by ID."""
    deps.verify_citizen_ownership(current_user, resource_citizen_id=citizen_id)
    citizen = citizen_crud.get(db, citizen_id=citizen_id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen profile not found."
        )
    return citizen


@router.put(
    "/{citizen_id}",
    response_model=CitizenResponse,
    summary="Update Citizen Profile by ID",
    description="Modify specific citizen profile. Allowed for Admin or owner."
)
def update_citizen(
    citizen_id: int,
    citizen_in: CitizenUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Update citizen by ID."""
    deps.verify_citizen_ownership(current_user, resource_citizen_id=citizen_id)
    citizen = citizen_crud.get(db, citizen_id=citizen_id)
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen profile not found."
        )
    return citizen_crud.update(db, db_obj=citizen, obj_in=citizen_in)
