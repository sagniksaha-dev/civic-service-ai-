import pytest
from typing import Dict, Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.citizen import Citizen
from app.core.security import get_password_hash, create_access_token

# Use in-memory SQLite database with StaticPool for isolated unit & integration test suites
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables in test database once per session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """Provide a clean isolated transactional database session for each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with get_db dependency overridden to use test session."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db: Session) -> User:
    """Fixture to create and return an Admin user."""
    user = User(
        name="Test Admin",
        email="test_admin@civic.local",
        hashed_password=get_password_hash("AdminPass123!"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def officer_user(db: Session) -> User:
    """Fixture to create and return a Department Officer user."""
    user = User(
        name="Test Officer",
        email="test_officer@civic.local",
        hashed_password=get_password_hash("OfficerPass123!"),
        role=UserRole.DEPARTMENT_OFFICER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def citizen_user(db: Session) -> User:
    """Fixture to create and return a Citizen user with linked Citizen profile."""
    user = User(
        name="Test Citizen",
        email="test_citizen@civic.local",
        hashed_password=get_password_hash("CitizenPass123!"),
        role=UserRole.CITIZEN,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    citizen = Citizen(
        user_id=user.id,
        phone="9876543210",
        address={"street": "100 Civic Lane", "city": "Metropolis", "district": "East", "state": "State", "postal_code": "700001"}
    )
    db.add(citizen)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def citizen_user_2(db: Session) -> User:
    """Fixture to create a second Citizen user for ownership violation testing."""
    user = User(
        name="Test Citizen Two",
        email="test_citizen_two@civic.local",
        hashed_password=get_password_hash("CitizenTwoPass123!"),
        role=UserRole.CITIZEN,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    citizen = Citizen(
        user_id=user.id,
        phone="9876543211",
        address={"street": "200 Civic Road", "city": "Metropolis", "district": "West", "state": "State", "postal_code": "700002"}
    )
    db.add(citizen)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_headers(admin_user: User) -> Dict[str, str]:
    """Authorization headers for Admin."""
    token = create_access_token(subject=admin_user.id, role=admin_user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def officer_headers(officer_user: User) -> Dict[str, str]:
    """Authorization headers for Department Officer."""
    token = create_access_token(subject=officer_user.id, role=officer_user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def citizen_headers(citizen_user: User) -> Dict[str, str]:
    """Authorization headers for Citizen 1."""
    token = create_access_token(subject=citizen_user.id, role=citizen_user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def citizen_2_headers(citizen_user_2: User) -> Dict[str, str]:
    """Authorization headers for Citizen 2."""
    token = create_access_token(subject=citizen_user_2.id, role=citizen_user_2.role.value)
    return {"Authorization": f"Bearer {token}"}
