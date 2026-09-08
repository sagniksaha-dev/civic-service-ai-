from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.department import department_crud
from app.crud.grievance import grievance_crud
from app.crud.notification import notification_crud
from app.models.citizen import Citizen
from app.models.grievance import GrievanceStatus
from app.models.user import User, UserRole
from app.schemas.grievance import (
    GrievanceCreate,
    GrievanceOfficerResponse,
    GrievanceResponse,
)
from app.schemas.notification import NotificationCreate

router = APIRouter()


@router.post(
    "/",
    response_model=GrievanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Citizen Grievance",
    description="File a civic complaint or help request with a public department."
)
def submit_grievance(
    grievance_in: GrievanceCreate,
    db: Session = Depends(deps.get_db),
    citizen: Citizen = Depends(deps.get_current_citizen_profile)
) -> Any:
    """Submit a grievance complaint."""
    department = department_crud.get(db, department_id=grievance_in.department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department with ID {grievance_in.department_id} does not exist."
        )

    g_record = grievance_crud.create(db, obj_in=grievance_in, citizen_id=citizen.id)

    try:
        notification_crud.create(
            db,
            obj_in=NotificationCreate(
                user_id=citizen.user_id,
                title="Grievance Registered",
                message=f"Your grievance '{grievance_in.subject}' has been registered with {department.name}.",
                notification_type="grievance_status",
                reference_id=str(g_record.id)
            )
        )
    except Exception:
        pass

    return g_record


@router.get(
    "/",
    response_model=List[GrievanceResponse],
    summary="List Grievances",
    description="Retrieve grievances. Citizens view only their own submissions; Officers and Admins view all."
)
def list_grievances(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    department_id: Optional[int] = None,
    status: Optional[GrievanceStatus] = None,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """List grievances with role-based visibility."""
    if current_user.role == UserRole.CITIZEN:
        if not current_user.citizen_profile:
            return []
        return grievance_crud.get_multi(
            db,
            skip=skip,
            limit=limit,
            citizen_id=current_user.citizen_profile.id,
            department_id=department_id,
            status=status
        )

    # Admin and Officer view all grievances
    return grievance_crud.get_multi(
        db,
        skip=skip,
        limit=limit,
        department_id=department_id,
        status=status
    )


@router.get(
    "/{grievance_id}",
    response_model=GrievanceResponse,
    summary="Get Grievance by ID",
    description="Retrieve specific grievance details and officer responses."
)
def get_grievance(
    grievance_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Get grievance by ID."""
    grievance = grievance_crud.get(db, grievance_id=grievance_id)
    if not grievance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grievance not found."
        )

    deps.verify_citizen_ownership(current_user, resource_citizen_id=grievance.citizen_id)
    return grievance


@router.put(
    "/{grievance_id}/respond",
    response_model=GrievanceResponse,
    summary="Respond to Grievance (Officer or Admin)",
    description="Provide official resolution notes and update grievance status."
)
def respond_to_grievance(
    grievance_id: int,
    response_in: GrievanceOfficerResponse,
    db: Session = Depends(deps.get_db),
    current_officer: User = Depends(deps.require_officer_or_admin)
) -> Any:
    """Respond to and update a grievance complaint."""
    grievance = grievance_crud.get(db, grievance_id=grievance_id)
    if not grievance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grievance not found."
        )

    updated_grievance = grievance_crud.respond(
        db,
        db_obj=grievance,
        response_in=response_in,
        officer_id=current_officer.id
    )

    # Notify citizen
    if updated_grievance.citizen and updated_grievance.citizen.user_id:
        try:
            notification_crud.create(
                db,
                obj_in=NotificationCreate(
                    user_id=updated_grievance.citizen.user_id,
                    title=f"Grievance Status: {response_in.status.value.upper()}",
                    message=f"Official Response for '{updated_grievance.subject}': {response_in.response}",
                    notification_type="grievance_status",
                    reference_id=str(updated_grievance.id)
                )
            )
        except Exception:
            pass

    return updated_grievance
