"""
pytest configuration and fixtures for testing.

This module provides:
- Test database setup with automatic cleanup
- FastAPI TestClient with dependency overrides
- Authenticated client fixtures
- Common test data factories
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.models.user import User
from app.core.security import hash_password


# Use in-memory SQLite for tests (fast, isolated, no external dependencies)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine with special settings for SQLite
test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite specific
    poolclass=StaticPool,  # Keep connection alive for in-memory DB
)

# Test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database for each test.

    This fixture:
    1. Creates all tables before the test
    2. Yields a database session
    3. Drops all tables after the test

    Ensures complete isolation between tests.
    """
    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables to ensure clean state
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    FastAPI TestClient with test database dependency override.

    This client:
    - Uses in-memory SQLite instead of PostgreSQL
    - Starts with clean database for each test
    - Does NOT require uvicorn to be running
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    """
    Create a test user in the database.

    Returns:
        User model instance with known credentials
    """
    user = User(
        email="test@example.com",
        password_hash=hash_password("TestPassword123!"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_token(test_user):
    """
    Generate a valid JWT token for the test user.

    Returns:
        Valid access token string
    """
    return create_access_token(test_user.id)


@pytest.fixture(scope="function")
def auth_headers(auth_token):
    """
    HTTP headers with valid authentication.

    Returns:
        Dict with Authorization header
    """
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="function")
def authenticated_client(client, auth_headers):
    """
    TestClient pre-configured with authentication headers.

    Usage:
        response = authenticated_client.get("/api/v1/accounts")
    """
    client.headers.update(auth_headers)
    return client
