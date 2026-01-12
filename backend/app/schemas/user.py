"""
User schemas for API request/response validation.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """
    Schema for creating a new user (registration).

    Used when: POST /api/v1/auth/register
    """

    email: EmailStr = Field(
        ...,
        description="User email address (must be unique)",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=72,
        description="Password (min 8 characters, max 72 bytes for bcrypt, will be hashed)",
        examples=["SecurePassword123!"],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "password": "MySecurePass123!",
            }
        }


class UserRead(BaseModel):
    """
    Schema for reading user data (responses).

    Used when: GET /api/v1/users/me
    Never includes password_hash in responses.
    """

    id: uuid.UUID = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email address")
    created_at: datetime = Field(..., description="Account creation timestamp")

    class Config:
        from_attributes = True  # Allows creating from SQLAlchemy models
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "john@example.com",
                "created_at": "2024-01-15T10:30:00Z",
            }
        }


class UserLogin(BaseModel):
    """
    Schema for user login.

    Used when: POST /api/v1/auth/login
    """

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "password": "MySecurePass123!",
            }
        }


class Token(BaseModel):
    """
    Schema for JWT token response.

    Used when: POST /api/v1/auth/login (response)
    """

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }
