from typing import Any, Dict, List, Optional, Union
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate


class CRUDDepartment:
    """CRUD operations for Department entity."""

    def get(self, db: Session, department_id: int) -> Optional[Department]:
        """Get department by ID."""
        return db.get(Department, department_id)

    def get_by_code(self, db: Session, code: str) -> Optional[Department]:
        """Get department by unique code."""
        stmt = select(Department).where(Department.code == code.upper().strip())
        return db.execute(stmt).scalar_one_or_none()

    def get_by_name(self, db: Session, name: str) -> Optional[Department]:
        """Get department by name."""
        stmt = select(Department).where(Department.name.ilike(name.strip()))
        return db.execute(stmt).scalar_one_or_none()

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Department]:
        """Get paginated list of departments."""
        stmt = select(Department)
        if is_active is not None:
            stmt = stmt.where(Department.is_active == is_active)
        stmt = stmt.order_by(Department.name).offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())

    def create(self, db: Session, obj_in: DepartmentCreate) -> Department:
        """Create a new department."""
        db_obj = Department(
            name=obj_in.name.strip(),
            code=obj_in.code.upper().strip(),
            description=obj_in.description,
            is_active=obj_in.is_active
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        db_obj: Department,
        obj_in: Union[DepartmentUpdate, Dict[str, Any]]
    ) -> Department:
        """Update department."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        if "code" in update_data and update_data["code"]:
            update_data["code"] = update_data["code"].upper().strip()

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, department_id: int) -> Optional[Department]:
        """Delete department by ID."""
        obj = db.get(Department, department_id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


department_crud = CRUDDepartment()
