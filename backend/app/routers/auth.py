"""
Authentication routes: signup and login.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import CurrentUser
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserLogin, Token

router = APIRouter()


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def signup(
    user_data: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Register a new user account.

    Steps:
    1. Check if email already exists
    2. Hash the password
    3. Create user in database
    4. Return user data (without password)

    Args:
        user_data: Email and password from request body
        db: Database session

    Returns:
        Created user object

    Raises:
        HTTPException 400: If email already registered
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Hash the password (NEVER store plain passwords!)
    password_hash = hash_password(user_data.password)

    # Create new user
    new_user = User(
        email=user_data.email,
        password_hash=password_hash,
    )

    # Save to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # Get the generated id and created_at

    return new_user


@router.post("/login", response_model=Token)
def login(
    credentials: UserLogin,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """
    Authenticate user and return JWT access token.

    Steps:
    1. Find user by email
    2. Verify password
    3. Generate JWT token
    4. Return token

    Args:
        credentials: Email and password from request body
        db: Database session

    Returns:
        JWT access token and token type

    Raises:
        HTTPException 401: If email not found or password incorrect
    """
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()

    # Check if user exists
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT token
    access_token = create_access_token(user_id=user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserRead)
def get_current_user_info(current_user: CurrentUser) -> User:
    """
    Get information about the currently authenticated user.

    Requires: Valid JWT token in Authorization header

    Args:
        current_user: Injected by get_current_user dependency

    Returns:
        Current user data
    """
    return current_user


@router.post("/logout")
def logout() -> dict:
    """
    Logout endpoint (client-side token deletion).

    Note: Since we're using stateless JWT tokens, there's no server-side session to destroy.
    The client must delete the token from storage (localStorage, cookies, etc.).

    In a production system with refresh tokens, this would invalidate the refresh token.

    Returns:
        Success message
    """
    return {"message": "Logged out successfully. Delete token from client storage."}
