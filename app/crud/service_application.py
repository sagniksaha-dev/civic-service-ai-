from typing import Any, Dict, List, Optional, Union
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.service_application import ServiceApplication, ApplicationStatus
from app.schemas.service_application import ServiceApplicationCreate, ServiceApplicationStatusUpdate
from app.services.reference_service import reference_service
from app.services.application_service import application_workflow_service


class CRUDServiceApplication:
    """CRUD and workflow operations for Service Applications."""

    def get(self, db: Session, application_id: int) -> Optional[ServiceApplication]:
        """Get application by ID."""
        return db.get(ServiceApplication, application_id)

    def get_by_reference(self, db: Session, reference_no: str) -> Optional[ServiceApplication]:
        """Lookup application by unique reference number."""
        stmt = select(ServiceApplication).where(ServiceApplication.reference_no == reference_no.strip())
        return db.execute(stmt).scalar_one_or_none()

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        citizen_id: Optional[int] = None,
        service_id: Optional[int] = None,
        status: Optional[ApplicationStatus] = None
    ) -> List[ServiceApplication]:
        """Fetch applications with optional citizen isolation, service filter, and status filter."""
        stmt = select(ServiceApplication)
        if citizen_id is not None:
            stmt = stmt.where(ServiceApplication.citizen_id == citizen_id)
        if service_id is not None:
            stmt = stmt.where(ServiceApplication.service_id == service_id)
        if status is not None:
            stmt = stmt.where(ServiceApplication.status == status)

        stmt = stmt.order_by(ServiceApplication.created_at.desc()).offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())

    def create(
        self,
        db: Session,
        obj_in: ServiceApplicationCreate,
        citizen_id: int
    ) -> ServiceApplication:
        """Create and submit a new service application with auto-generated reference number."""
        # Ensure unique reference number
        ref_no = reference_service.generate_application_reference()
        while self.get_by_reference(db, ref_no) is not None:
            ref_no = reference_service.generate_application_reference()

        db_obj = ServiceApplication(
            citizen_id=citizen_id,
            service_id=obj_in.service_id,
            reference_no=ref_no,
            payload=obj_in.payload,
            status=ApplicationStatus.SUBMITTED
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_status(
        self,
        db: Session,
        db_obj: ServiceApplication,
        status_update: ServiceApplicationStatusUpdate,
        officer_id: int
    ) -> ServiceApplication:
        """Validate workflow transition and update application status and officer review notes."""
        application_workflow_service.validate_status_transition(
            current_status=db_obj.status,
            new_status=status_update.status
        )

        db_obj.status = status_update.status
        if status_update.officer_remarks is not None:
            db_obj.officer_remarks = status_update.officer_remarks
        db_obj.reviewed_by_id = officer_id

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


service_application_crud = CRUDServiceApplication()
