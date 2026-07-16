"""
pytest configuration and shared fixtures.

Test strategy:
  - Use SQLite in-memory DB for all unit tests — no Supabase required in CI.
  - Override get_db and get_settings dependencies for isolation.
  - Provide a TestClient fixture that handles auth headers automatically.
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ---------------------------------------------------------------------------
# Set test environment variables BEFORE importing app modules
# (prevents Settings validation from requiring real secrets)
# ---------------------------------------------------------------------------

# Generate a valid Fernet key for testing
from cryptography.fernet import Fernet
_test_fernet_key = Fernet.generate_key().decode()

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("FERNET_KEY", _test_fernet_key)
os.environ.setdefault("DASHBOARD_API_KEY", "test-dashboard-key-for-ci")
os.environ.setdefault("APP_ENV", "development")

# ---------------------------------------------------------------------------
# Now import app modules (settings already initialised with test env)
# ---------------------------------------------------------------------------
from app.main import app
from app.models.base import Base
from app.services.db import get_db
from app.core.config import get_settings, Settings
from app.core.security import _encryption_instance

# ---------------------------------------------------------------------------
# In-memory SQLite engine for tests
# ---------------------------------------------------------------------------

SQLITE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Create all tables once for the entire test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session():
    """
    Yield a clean DB session per test.
    Rolls back after each test so tests are isolated.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    """
    FastAPI TestClient with the DB dependency overridden
    to use the in-memory SQLite session.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client) -> dict:
    """
    Create a test user and return a valid JWT Bearer auth header.
    Uses the real signup + login endpoints against the in-memory DB.
    """
    from app.core.security import get_password_hash
    from app.models.user import User as UserModel

    # Create test user directly in DB
    db = next(client.app.dependency_overrides[get_db]())
    test_email = "admin@example.com"
    test_password = "admin123"

    existing = db.query(UserModel).filter(UserModel.email == test_email).first()
    if not existing:
        user = UserModel(
            email=test_email,
            hashed_password=get_password_hash(test_password),
        )
        db.add(user)
        db.commit()

    # Login to get a JWT
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": test_email, "password": test_password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, f"Auth setup failed: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def authed_client(client, auth_headers):
    """TestClient pre-configured with JWT Bearer auth headers."""
    client.headers.update(auth_headers)
    return client
