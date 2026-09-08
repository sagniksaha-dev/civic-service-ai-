from typing import Any, Dict, List, Optional, Union
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.grievance import Grievance, GrievanceStatus
from app.schemas.grievance import GrievanceCreate, GrievanceOfficerResponse


class CRUDGrievance:
    """CRUD operations for citizen grievance complaints."""

    def get(self, db: Session, grievance_id: int) -> Optional[Grievance]:
        """Get grievance by ID."""
        return db.get(Grievance, grievance_id)

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        citizen_id: Optional[int] = None,
        department_id: Optional[int] = None,
        status: Optional[GrievanceStatus] = None
    ) -> List[Grievance]:
        """Fetch grievances with optional citizen isolation, department filter, and status filter."""
        stmt = select(Grievance)
        if citizen_id is not None:
            stmt = stmt.where(Grievance.citizen_id == citizen_id)
        if department_id is not None:
            stmt = stmt.where(Grievance.department_id == department_id)
        if status is not None:
            stmt = stmt.where(Grievance.status == status)

        stmt = stmt.order_by(Grievance.created_at.desc()).offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())

    def create(
        self,
        db: Session,
        obj_in: GrievanceCreate,
        citizen_id: int
    ) -> Grievance:
        """Create and submit a new citizen grievance."""
        db_obj = Grievance(
            citizen_id=citizen_id,
            department_id=obj_in.department_id,
            service_id=obj_in.service_id,
            subject=obj_in.subject.strip(),
            details=obj_in.details.strip(),
            status=GrievanceStatus.SUBMITTED
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def respond(
        self,
        db: Session,
        db_obj: Grievance,
        response_in: GrievanceOfficerResponse,
        officer_id: int
    ) -> Grievance:
        """Add officer response and update grievance status."""
        db_obj.response = response_in.response.strip()
        db_obj.status = response_in.status
        db_obj.assigned_officer_id = officer_id

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


grievance_crud = CRUDGrievance()
