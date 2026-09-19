import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.utils.rate_limit import limiter

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def reset_db():
    """Builds and tears down tables independently of active sessions."""
    Base.metadata.create_all(bind=engine)
    limiter.reset()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Provides a fresh isolated database session."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """Overrides the FastAPI get_db dependency."""
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": "testuser@example.com",
            "password": "Password123!",
        },
    )
    token = response.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_task(client, auth_headers):
    response = client.post(
        "/tasks",
        json={
            "title": "Clean",
            "description": "Clean my room monday",
            "priority": "low",
            "completed": False,
        },
        headers=auth_headers,
    )
    return response.json()
