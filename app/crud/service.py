from typing import Any, Dict, List, Optional, Union
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.service import Service, ServiceStatus
from app.schemas.service import ServiceCreate, ServiceUpdate


class CRUDService:
    """CRUD operations for Service Catalogue entity."""

    def get(self, db: Session, service_id: int) -> Optional[Service]:
        """Get service by ID."""
        return db.get(Service, service_id)

    def get_by_code(self, db: Session, code: str) -> Optional[Service]:
        """Get service by unique service code."""
        stmt = select(Service).where(Service.code == code.upper().strip())
        return db.execute(stmt).scalar_one_or_none()

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        department_id: Optional[int] = None,
        status: Optional[ServiceStatus] = None,
        search: Optional[str] = None
    ) -> List[Service]:
        """Fetch paginated list of services with optional department, status and text search."""
        stmt = select(Service)
        if department_id is not None:
            stmt = stmt.where(Service.department_id == department_id)
        if status is not None:
            stmt = stmt.where(Service.status == status)
        if search:
            stmt = stmt.where(Service.name.ilike(f"%{search.strip()}%"))

        stmt = stmt.order_by(Service.name).offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())

    def create(self, db: Session, obj_in: ServiceCreate) -> Service:
        """Create a new service catalogue entry."""
        db_obj = Service(
            department_id=obj_in.department_id,
            name=obj_in.name.strip(),
            code=obj_in.code.upper().strip(),
            description=obj_in.description,
            requirements=obj_in.requirements,
            eligibility_criteria=obj_in.eligibility_criteria,
            processing_time_days=obj_in.processing_time_days,
            status=obj_in.status
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        db_obj: Service,
        obj_in: Union[ServiceUpdate, Dict[str, Any]]
    ) -> Service:
        """Update service details."""
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

    def delete(self, db: Session, service_id: int) -> Optional[Service]:
        """Delete service by ID."""
        obj = db.get(Service, service_id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


service_crud = CRUDService()
