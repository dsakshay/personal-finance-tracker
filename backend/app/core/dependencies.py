"""
FastAPI dependencies for authentication and authorization.
"""

from typing import Annotated
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

# HTTP Bearer token scheme (Authorization: Bearer <token>)
security = HTTPBearer()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    FastAPI dependency to get the currently authenticated user.

    Flow:
    1. Extract token from Authorization header
    2. Decode and validate token
    3. Fetch user from database
    4. Return user object

    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Database session

    Returns:
        User object if authenticated

    Raises:
        HTTPException 401: If token is invalid or user not found

    Usage in routes:
        @app.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_email": current_user.email}
    """
    # Extract token from credentials
    token = credentials.credentials

    # Decode token to get user_id
    user_id = decode_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# Type alias for cleaner dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
