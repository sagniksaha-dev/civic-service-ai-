from typing import List, Optional, Union, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import User, UserRole
from app.models.citizen import Citizen
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


class CRUDUser:
    """CRUD operations for User entity and authentication."""

    def get(self, db: Session, user_id: int) -> Optional[User]:
        """Fetch user by primary key ID."""
        return db.get(User, user_id)

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Fetch user by unique email address."""
        stmt = select(User).where(User.email == email.lower().strip())
        return db.execute(stmt).scalar_one_or_none()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100, role: Optional[UserRole] = None) -> List[User]:
        """Fetch paginated list of users, optionally filtered by role."""
        stmt = select(User)
        if role:
            stmt = stmt.where(User.role == role)
        stmt = stmt.offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())

    def create(self, db: Session, obj_in: UserCreate) -> User:
        """Create a new user with hashed password and auto-create citizen profile if citizen."""
        db_obj = User(
            name=obj_in.name.strip(),
            email=obj_in.email.lower().strip(),
            hashed_password=get_password_hash(obj_in.password),
            role=obj_in.role,
            is_active=obj_in.is_active
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        # Automatically create citizen profile if registered as citizen
        if db_obj.role == UserRole.CITIZEN and not db_obj.citizen_profile:
            citizen_obj = Citizen(
                user_id=db_obj.id,
                phone="",
                address={"street": "", "city": "", "district": "", "state": "", "postal_code": ""}
            )
            db.add(citizen_obj)
            db.commit()
            db.refresh(db_obj)

        return db_obj

    def update(self, db: Session, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]) -> User:
        """Update existing user fields."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            db_obj.hashed_password = hashed_password
            del update_data["password"]

        if "email" in update_data and update_data["email"]:
            update_data["email"] = update_data["email"].lower().strip()

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def authenticate(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password."""
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        """Check if user is active."""
        return user.is_active

    def is_admin(self, user: User) -> bool:
        """Check if user has Admin role."""
        return user.role == UserRole.ADMIN

    def is_officer(self, user: User) -> bool:
        """Check if user has Department Officer role."""
        return user.role == UserRole.DEPARTMENT_OFFICER

    def remove(self, db: Session, user_id: int) -> Optional[User]:
        """Delete user account by ID."""
        obj = db.get(User, user_id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


user_crud = CRUDUser()
