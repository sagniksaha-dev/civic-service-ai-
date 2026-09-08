from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.notification import notification_crud
from app.crud.service import service_crud
from app.crud.service_application import service_application_crud
from app.models.citizen import Citizen
from app.models.service import ServiceStatus
from app.models.service_application import ApplicationStatus
from app.models.user import User, UserRole
from app.schemas.notification import NotificationCreate
from app.schemas.service_application import (
    ServiceApplicationCreate,
    ServiceApplicationResponse,
    ServiceApplicationStatusUpdate,
)

router = APIRouter()


@router.post(
    "/",
    response_model=ServiceApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Service Application (Citizen)",
    description="Submit an application for a civic service. Generates unique tracking reference number (e.g. APP-YYYYMMDD-XXXX)."
)
def submit_application(
    app_in: ServiceApplicationCreate,
    db: Session = Depends(deps.get_db),
    citizen: Citizen = Depends(deps.get_current_citizen_profile)
) -> Any:
    """Submit a service application."""
    # Verify service existence and active status
    service = service_crud.get(db, service_id=app_in.service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target service not found in catalogue."
        )
    if service.status != ServiceStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Service '{service.name}' is currently {service.status.value} and not accepting applications."
        )

    # Privacy guardrail: Reject any payload containing sensitive keywords like aadhaar
    payload_str = str(app_in.payload).lower()
    if "aadhaar" in payload_str or "aadhar" in payload_str or "ssn" in payload_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security Policy Violation: Do not submit real identity documents or sensitive numbers like Aadhaar."
        )

    app_record = service_application_crud.create(db, obj_in=app_in, citizen_id=citizen.id)

    # Log submission notification
    try:
        notification_crud.create(
            db,
            obj_in=NotificationCreate(
                user_id=citizen.user_id,
                title="Application Submitted",
                message=f"Your application for '{service.name}' was submitted successfully (Reference: {app_record.reference_no}).",
                notification_type="application_status",
                reference_id=app_record.reference_no
            )
        )
    except Exception:
        pass

    return app_record


@router.get(
    "/",
    response_model=List[ServiceApplicationResponse],
    summary="List Service Applications",
    description="Retrieve applications. Citizens view their own submissions only; Officers and Admins view all."
)
def list_applications(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service_id: Optional[int] = None,
    status: Optional[ApplicationStatus] = None,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """List service applications based on role permissions."""
    if current_user.role == UserRole.CITIZEN:
        if not current_user.citizen_profile:
            return []
        return service_application_crud.get_multi(
            db,
            skip=skip,
            limit=limit,
            citizen_id=current_user.citizen_profile.id,
            service_id=service_id,
            status=status
        )

    # Admin and Officer view all applications
    return service_application_crud.get_multi(
        db,
        skip=skip,
        limit=limit,
        service_id=service_id,
        status=status
    )


@router.get(
    "/ref/{reference_no}",
    response_model=ServiceApplicationResponse,
    summary="Lookup Application by Reference Number",
    description="Find application status using tracking reference number."
)
def get_application_by_reference(
    reference_no: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Lookup application by reference."""
    app_obj = service_application_crud.get_by_reference(db, reference_no=reference_no)
    if not app_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application with reference '{reference_no}' not found."
        )

    deps.verify_citizen_ownership(current_user, resource_citizen_id=app_obj.citizen_id)
    return app_obj


@router.get(
    "/{application_id}",
    response_model=ServiceApplicationResponse,
    summary="Get Application by ID",
    description="Retrieve application details. Ownership rules apply."
)
def get_application_by_id(
    application_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Get application by ID."""
    app_obj = service_application_crud.get(db, application_id=application_id)
    if not app_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found."
        )

    deps.verify_citizen_ownership(current_user, resource_citizen_id=app_obj.citizen_id)
    return app_obj


@router.put(
    "/{application_id}/status",
    response_model=ServiceApplicationResponse,
    summary="Update Application Status (Officer or Admin)",
    description="Advance application through workflow stages (e.g. SUBMITTED -> UNDER_REVIEW -> APPROVED/REJECTED)."
)
def update_application_status(
    application_id: int,
    status_in: ServiceApplicationStatusUpdate,
    db: Session = Depends(deps.get_db),
    current_officer: User = Depends(deps.require_officer_or_admin)
) -> Any:
    """Update application status."""
    app_obj = service_application_crud.get(db, application_id=application_id)
    if not app_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found."
        )

    updated_app = service_application_crud.update_status(
        db,
        db_obj=app_obj,
        status_update=status_in,
        officer_id=current_officer.id
    )

    # Trigger notification to citizen
    if updated_app.citizen and updated_app.citizen.user_id:
        try:
            remarks_text = f" Remarks: {status_in.officer_remarks}" if status_in.officer_remarks else ""
            notification_crud.create(
                db,
                obj_in=NotificationCreate(
                    user_id=updated_app.citizen.user_id,
                    title=f"Application Status: {status_in.status.value.upper()}",
                    message=f"Application {updated_app.reference_no} status changed to '{status_in.status.value}'.{remarks_text}",
                    notification_type="application_status",
                    reference_id=updated_app.reference_no
                )
            )
        except Exception:
            pass

    return updated_app
