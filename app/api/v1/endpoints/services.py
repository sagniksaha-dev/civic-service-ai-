from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, select

from app.api import deps
from app.crud.department import department_crud
from app.crud.service import service_crud
from app.models.department import Department
from app.models.grievance import Grievance, GrievanceStatus
from app.models.service import Service, ServiceStatus
from app.models.service_application import ApplicationStatus, ServiceApplication
from app.models.user import User
from app.schemas.service import ServiceCreate, ServiceResponse, ServiceUpdate

router = APIRouter()


@router.get(
    "/",
    response_model=List[ServiceResponse],
    summary="List Public Services",
    description="Retrieve public service catalogue with optional department, category, and search filters."
)
def list_services(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    department_id: Optional[int] = None,
    status: Optional[ServiceStatus] = None,
    search: Optional[str] = None
) -> Any:
    """List service catalogue."""
    return service_crud.get_multi(
        db,
        skip=skip,
        limit=limit,
        department_id=department_id,
        status=status,
        search=search
    )


@router.get(
    "/stats/sla-dashboard",
    summary="Officer SLA & Civic Operations Dashboard",
    description="Provides real-time SLA metrics, application processing counts, and grievance redressal statistics."
)
def get_sla_dashboard(
    db: Session = Depends(deps.get_db),
    current_officer: User = Depends(deps.require_officer_or_admin)
) -> Dict[str, Any]:
    """Retrieve operational SLA and performance metrics."""
    # Applications count by status
    app_stats = {}
    for s in ApplicationStatus:
        count = db.scalar(select(func.count(ServiceApplication.id)).where(ServiceApplication.status == s)) or 0
        app_stats[s.value] = count

    # Grievances count by status
    grievance_stats = {}
    for g in GrievanceStatus:
        count = db.scalar(select(func.count(Grievance.id)).where(Grievance.status == g)) or 0
        grievance_stats[g.value] = count

    total_services = db.scalar(select(func.count(Service.id))) or 0
    total_departments = db.scalar(select(func.count(Department.id))) or 0
    total_apps = sum(app_stats.values())
    total_grievances = sum(grievance_stats.values())

    # SLA Resolution Rate
    resolved_apps = app_stats.get("approved", 0) + app_stats.get("rejected", 0)
    app_resolution_rate = round((resolved_apps / total_apps * 100), 1) if total_apps > 0 else 100.0

    resolved_grievances = grievance_stats.get("resolved", 0) + grievance_stats.get("closed", 0)
    grievance_resolution_rate = round((resolved_grievances / total_grievances * 100), 1) if total_grievances > 0 else 100.0

    return {
        "total_departments": total_departments,
        "total_services": total_services,
        "total_applications": total_apps,
        "applications_by_status": app_stats,
        "application_resolution_rate_pct": app_resolution_rate,
        "total_grievances": total_grievances,
        "grievances_by_status": grievance_stats,
        "grievance_resolution_rate_pct": grievance_resolution_rate,
        "active_officer": current_officer.name,
        "sla_target_days_avg": 15
    }


@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Get Service Details",
    description="Retrieve service details including JSON required documents and eligibility criteria."
)
def get_service(
    service_id: int,
    db: Session = Depends(deps.get_db)
) -> Any:
    """Get service details."""
    service = service_crud.get(db, service_id=service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found in catalogue."
        )
    return service


@router.post(
    "/",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Service (Officer or Admin)",
    description="Add a new service to the catalogue with JSON requirements & eligibility."
)
def create_service(
    service_in: ServiceCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_officer_or_admin)
) -> Any:
    """Create service catalogue entry."""
    department = department_crud.get(db, department_id=service_in.department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Associated department with ID {service_in.department_id} does not exist."
        )

    existing_code = service_crud.get_by_code(db, code=service_in.code)
    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Service with code '{service_in.code}' already exists."
        )

    return service_crud.create(db, obj_in=service_in)


@router.put(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Update Service (Officer or Admin)",
    description="Modify service details, SLA days, or requirements."
)
def update_service(
    service_id: int,
    service_in: ServiceUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_officer_or_admin)
) -> Any:
    """Update service entry."""
    service = service_crud.get(db, service_id=service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found."
        )

    if service_in.department_id is not None:
        department = department_crud.get(db, department_id=service_in.department_id)
        if not department:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Associated department with ID {service_in.department_id} does not exist."
            )

    return service_crud.update(db, db_obj=service, obj_in=service_in)


@router.delete(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Delete Service (Admin Only)",
    description="Remove service from catalogue. Restricted to Admin."
)
def delete_service(
    service_id: int,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.require_admin)
) -> Any:
    """Delete service."""
    service = service_crud.delete(db, service_id=service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found."
        )
    return service
