from typing import Any, Dict, List, Optional, Union
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.citizen import Citizen
from app.schemas.citizen import CitizenCreate, CitizenUpdate


class CRUDCitizen:
    """CRUD operations for Citizen profile entity."""

    def get(self, db: Session, citizen_id: int) -> Optional[Citizen]:
        """Get citizen profile by ID."""
        return db.get(Citizen, citizen_id)

    def get_by_user_id(self, db: Session, user_id: int) -> Optional[Citizen]:
        """Get citizen profile by associated User ID."""
        stmt = select(Citizen).where(Citizen.user_id == user_id)
        return db.execute(stmt).scalar_one_or_none()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[Citizen]:
        """List paginated citizen profiles (Admin only)."""
        stmt = select(Citizen).offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())

    def create(self, db: Session, obj_in: CitizenCreate, user_id: int) -> Citizen:
        """Create a new citizen profile."""
        db_obj = Citizen(
            user_id=user_id,
            phone=obj_in.phone,
            address=obj_in.address,
            date_of_birth=obj_in.date_of_birth
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        db_obj: Citizen,
        obj_in: Union[CitizenUpdate, Dict[str, Any]]
    ) -> Citizen:
        """Smart partial update for citizen profile."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "address" and isinstance(value, dict) and isinstance(db_obj.address, dict):
                merged_address = dict(db_obj.address)
                merged_address.update(value)
                setattr(db_obj, field, merged_address)
            else:
                setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


citizen_crud = CRUDCitizen()
