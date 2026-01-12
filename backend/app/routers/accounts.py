"""
Account management endpoints.
All operations are scoped to the authenticated user.
"""

from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.models.account import Account
from app.models.transaction import Transaction
from app.schemas.account import AccountCreate, AccountResponse, AccountListResponse

router = APIRouter()


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    account_data: AccountCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> AccountResponse:
    """
    Create a new account for the authenticated user.

    API Contract: docs/backend/api-contracts.md#1-post-accounts

    Data Flow:
    1. Request → FastAPI validates via AccountCreate schema
    2. Convert human-readable amount ("5000.00") to minor units (500000)
    3. Create Account model with user_id from auth token
    4. Save to database (PostgreSQL)
    5. Convert back to human-readable format
    6. Return AccountResponse

    Authorization:
    - Requires valid JWT token in Authorization header
    - Account automatically owned by authenticated user
    - user_id comes from token, NOT request body

    Validation:
    - name: 1-100 chars, not empty/whitespace
    - currency: Exactly 3 uppercase letters, must be supported
    - opening_balance: Decimal string with 2 places (e.g., "1000.50")

    Args:
        account_data: Validated account details from request body
        current_user: Injected from JWT token via Depends(get_current_user)
        db: Database session via Depends(get_db)

    Returns:
        Created account with current_balance = opening_balance

    Raises:
        400: Validation error (invalid currency, format, etc.)
        401: Unauthorized (missing/invalid token)
    """
    # Step 1: Convert opening balance to minor units for database storage
    # "5000.00" → 500000 paise
    opening_balance_minor = account_data.to_minor_units()

    # Step 2: Create SQLAlchemy model instance
    # user_id comes from authenticated user (security!)
    new_account = Account(
        user_id=current_user.id,  # From JWT token, not request
        name=account_data.name,
        currency=account_data.currency.upper(),
        opening_balance_minor=opening_balance_minor,
    )

    # Step 3: Save to database
    db.add(new_account)
    db.commit()  # Insert into accounts table
    db.refresh(new_account)  # Reload to get auto-generated id, created_at

    # Step 4: Convert back to API response format
    # Minor units → decimal strings for frontend
    return AccountResponse.from_db_model(new_account)


@router.get("", response_model=AccountListResponse)
def list_accounts(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    currency: str | None = Query(None, description="Filter by currency (ISO 4217)"),
) -> AccountListResponse:
    """
    List all accounts for the authenticated user.

    API Contract: docs/backend/api-contracts.md#2-get-accounts

    Data Flow:
    1. Extract user_id from JWT token (via CurrentUser dependency)
    2. Query accounts table: WHERE user_id = ? [AND currency = ?]
    3. For each account, calculate current balance:
       - Query SUM(amount_minor) from transactions WHERE account_id = ?
       - current_balance = opening_balance + transaction_sum
    4. Convert minor units to decimal strings
    5. Return AccountListResponse with accounts array + total_count

    Authorization:
    - Multi-user isolation: Only returns accounts owned by authenticated user
    - Cannot see other users' accounts (enforced by WHERE user_id filter)

    Balance Calculation:
    - On-demand calculation (no cached balances)
    - current_balance = opening_balance + sum(all transactions)
    - Accurate but may be slow with many accounts/transactions

    Args:
        current_user: Injected from JWT token via Depends(get_current_user)
        db: Database session via Depends(get_db)
        currency: Optional filter (e.g., "INR", "USD")

    Returns:
        AccountListResponse with accounts list and total count

    Raises:
        401: Unauthorized (missing/invalid token)
    """
    # Step 1: Build query with user_id filter (security!)
    query = db.query(Account).filter(Account.user_id == current_user.id)

    # Step 2: Optional currency filter
    if currency:
        query = query.filter(Account.currency == currency.upper())

    # Step 3: Execute query, ordered by creation date (newest first)
    accounts = query.order_by(Account.created_at.desc()).all()

    # Step 4: Calculate current balance for each account
    account_responses = []

    for account in accounts:
        # Sum all transaction amounts in minor units
        transaction_sum = (
            db.query(func.sum(Transaction.amount_minor))
            .filter(Transaction.account_id == account.id)
            .scalar()
        ) or 0  # Default to 0 if no transactions

        # Calculate current balance
        current_balance_minor = account.opening_balance_minor + transaction_sum

        # Convert to response format (minor units → decimal strings)
        account_responses.append(
            AccountResponse.from_db_model(account, current_balance_minor)
        )

    # Step 5: Return wrapped response
    return AccountListResponse(
        accounts=account_responses,
        total_count=len(account_responses),
    )


