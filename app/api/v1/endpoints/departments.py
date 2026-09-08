from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.department import department_crud
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentResponse, DepartmentUpdate

router = APIRouter()


@router.get(
    "/",
    response_model=List[DepartmentResponse],
    summary="List Departments",
    description="Retrieve all public departments. Public endpoint."
)
def list_departments(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_active: Optional[bool] = None
) -> Any:
    """List departments."""
    return department_crud.get_multi(db, skip=skip, limit=limit, is_active=is_active)


@router.get(
    "/{department_id}",
    response_model=DepartmentResponse,
    summary="Get Department by ID",
    description="Retrieve specific department details."
)
def get_department(
    department_id: int,
    db: Session = Depends(deps.get_db)
) -> Any:
    """Get department details by ID."""
    department = department_crud.get(db, department_id=department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found."
        )
    return department


@router.post(
    "/",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Department (Admin Only)",
    description="Register a new civic department. Restricted to Admin."
)
def create_department(
    department_in: DepartmentCreate,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.require_admin)
) -> Any:
    """Create a new department."""
    existing_code = department_crud.get_by_code(db, code=department_in.code)
    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department with code '{department_in.code}' already exists."
        )
    existing_name = department_crud.get_by_name(db, name=department_in.name)
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department with name '{department_in.name}' already exists."
        )
    return department_crud.create(db, obj_in=department_in)


@router.put(
    "/{department_id}",
    response_model=DepartmentResponse,
    summary="Update Department (Admin Only)",
    description="Modify department details. Restricted to Admin."
)
def update_department(
    department_id: int,
    department_in: DepartmentUpdate,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.require_admin)
) -> Any:
    """Update department."""
    department = department_crud.get(db, department_id=department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found."
        )
    return department_crud.update(db, db_obj=department, obj_in=department_in)


@router.delete(
    "/{department_id}",
    response_model=DepartmentResponse,
    summary="Delete Department (Admin Only)",
    description="Delete a department and cascade removal. Restricted to Admin."
)
def delete_department(
    department_id: int,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.require_admin)
) -> Any:
    """Delete department."""
    department = department_crud.delete(db, department_id=department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found."
        )
    return department
