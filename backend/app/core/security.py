"""
Security utilities for password hashing and JWT token generation.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    Args:
        password: Plain-text password from user input

    Returns:
        Hashed password string safe for database storage

    Example:
        >>> hash_password("MyPassword123")
        "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYbY8j4s3vC"
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a hashed password.

    Args:
        plain_password: Plain-text password from login attempt
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise

    Example:
        >>> hashed = hash_password("MyPassword123")
        >>> verify_password("MyPassword123", hashed)
        True
        >>> verify_password("WrongPassword", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: uuid.UUID, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token containing user_id.

    Args:
        user_id: User UUID to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string

    Token payload structure:
        {
            "sub": "user-uuid-here",  # Subject (user_id)
            "exp": 1234567890         # Expiration timestamp
        }

    Example:
        >>> token = create_access_token(uuid.uuid4())
        >>> # Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # JWT payload (claims)
    to_encode = {
        "sub": str(user_id),  # Subject: user identifier
        "exp": expire,  # Expiration time
    }

    # Encode token using secret key and algorithm
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[uuid.UUID]:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT token string

    Returns:
        User UUID if token is valid, None otherwise

    Example:
        >>> token = create_access_token(user_id)
        >>> user_id = decode_access_token(token)
        >>> print(user_id)
        UUID('123e4567-e89b-12d3-a456-426614174000')
    """
    try:
        # Decode token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Extract user_id from "sub" claim
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            return None

        # Convert to UUID
        user_id = uuid.UUID(user_id_str)
        return user_id

    except JWTError:
        # Token is invalid, expired, or tampered with
        return None
    except ValueError:
        # Invalid UUID format
        return None
