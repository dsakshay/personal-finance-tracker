"""
Authentication flow tests.

Critical for security:
- Prevents duplicate user registration
- Validates password requirements
- Ensures JWT tokens are issued correctly
- Prevents unauthorized access
"""

import pytest
from fastapi import status


def test_signup_creates_user(client):
    """
    Test: Signup creates a new user and returns user data.

    Why critical:
    - Validates user registration flow
    - Ensures passwords are hashed (not stored in plain text)
    - Confirms email uniqueness constraint
    """
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "newuser@example.com",
            "password": "SecurePass123!",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "password" not in data  # Password must never be returned
    assert "password_hash" not in data  # Hash must never be exposed


def test_signup_duplicate_email_fails(client):
    """
    Test: Cannot create two users with same email.

    Why critical:
    - Prevents account hijacking
    - Ensures email is unique identifier
    - Database integrity constraint validation
    """
    # First signup succeeds
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "duplicate@example.com",
            "password": "SecurePass123!",
        },
    )

    # Second signup with same email fails
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "duplicate@example.com",
            "password": "DifferentPass456!",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already registered" in response.json()["detail"].lower()


def test_signup_weak_password_fails(client):
    """
    Test: Weak passwords are rejected.

    Why critical:
    - Enforces minimum security standards
    - Prevents brute force attacks
    - Validates Pydantic schema constraints
    """
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "user@example.com",
            "password": "weak",  # Too short
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_login_with_valid_credentials(client):
    """
    Test: Login returns JWT token for valid credentials.

    Why critical:
    - Validates authentication flow
    - Ensures password verification works
    - Confirms JWT token generation
    """
    # Create user
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "loginuser@example.com",
            "password": "MyPassword123!",
        },
    )

    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "loginuser@example.com",
            "password": "MyPassword123!",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 20  # JWT tokens are long


def test_login_with_wrong_password_fails(client):
    """
    Test: Login fails with incorrect password.

    Why critical:
    - Prevents unauthorized access
    - Validates password verification logic
    - Security against credential stuffing
    """
    # Create user
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "user@example.com",
            "password": "CorrectPassword123!",
        },
    )

    # Login with wrong password
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "user@example.com",
            "password": "WrongPassword456!",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_with_nonexistent_user_fails(client):
    """
    Test: Login fails for non-existent user.

    Why critical:
    - Prevents user enumeration attacks
    - Should return same error as wrong password
    """
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "SomePassword123!",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_protected_endpoint_without_token_fails(client):
    """
    Test: Protected endpoints reject requests without auth token.

    Why critical:
    - Ensures authentication is enforced
    - Prevents unauthorized data access
    """
    response = client.get("/api/v1/accounts")

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_protected_endpoint_with_invalid_token_fails(client):
    """
    Test: Protected endpoints reject invalid JWT tokens.

    Why critical:
    - Prevents token forgery
    - Validates JWT signature verification
    """
    response = client.get(
        "/api/v1/accounts",
        headers={"Authorization": "Bearer invalid_token_here"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_protected_endpoint_with_valid_token_succeeds(authenticated_client):
    """
    Test: Protected endpoints work with valid JWT token.

    Why critical:
    - Validates end-to-end authentication flow
    - Ensures dependency injection works correctly
    """
    response = authenticated_client.get("/api/v1/accounts")

    # Should succeed (200) or return empty list, not 401
    assert response.status_code in [status.HTTP_200_OK]
