import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Tests run in debug mode to bypass the production secret key check
os.environ.setdefault("DEBUG", "True")

from app.database import Base, get_db
from app.models import Expense, User  # noqa: F401 — register models


@pytest.fixture()
def test_engine():
    """Create a fresh in-memory SQLite engine for each test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(test_engine):
    """Create a fresh database session for each test."""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    """Create a TestClient with the DB session overridden to use the test session."""
    from app import create_app

    app = create_app()

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
def auth_token(client):
    """Register a test user and return the JWT token."""
    r = client.post(
        "/api/v1/auth/register",
        json={"username": "testuser", "password": "testpass123"},
    )
    assert r.status_code == 201
    return r.json()["access_token"]


@pytest.fixture()
def auth_headers(auth_token):
    """Return Authorization headers with a valid JWT token."""
    return {"Authorization": f"Bearer {auth_token}"}
