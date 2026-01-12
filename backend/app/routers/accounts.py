"""
Account management endpoints.
All operations are scoped to the authenticated user.
"""

from typing import Annotated, List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.models.account import Account
from app.models.transaction import Transaction
from app.schemas.account import AccountCreate, AccountRead, AccountWithBalance

router = APIRouter()


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    account_data: AccountCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Account:
    """
    Create a new account for the authenticated user.

    Authorization:
    - Only authenticated users can create accounts
    - Account is automatically owned by current_user

    Steps:
    1. Validate currency and opening balance (handled by schema)
    2. Convert opening_balance to minor units
    3. Create account with user_id = current_user.id
    4. Save to database

    Args:
        account_data: Account details from request body
        current_user: Injected authenticated user
        db: Database session

    Returns:
        Created account with human-readable amounts

    Example Request:
        POST /api/v1/accounts
        Authorization: Bearer <token>
        {
            "name": "HDFC Savings",
            "currency": "INR",
            "opening_balance": 5000.00
        }

    Example Response:
        201 Created
        {
            "id": "uuid...",
            "user_id": "uuid...",
            "name": "HDFC Savings",
            "currency": "INR",
            "opening_balance": 5000.00,
            "created_at": "2024-01-15T10:30:00Z"
        }
    """
    # Convert opening balance to minor units (paise/cents)
    opening_balance_minor = account_data.to_minor_units()

    # Create new account owned by current user
    new_account = Account(
        user_id=current_user.id,  # Authorization: Owned by current user
        name=account_data.name,
        currency=account_data.currency.upper(),
        opening_balance_minor=opening_balance_minor,
    )

    # Save to database
    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    # Convert back to human-readable format for response
    return AccountRead.from_db_model(new_account)


@router.get("", response_model=List[AccountRead])
def list_accounts(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> List[AccountRead]:
    """
    List all accounts for the authenticated user.

    Authorization:
    - Only returns accounts where user_id = current_user.id
    - Users cannot see other users' accounts

    Steps:
    1. Query accounts table with user_id filter
    2. Convert each account to human-readable format
    3. Return list of accounts

    Args:
        current_user: Injected authenticated user
        db: Database session

    Returns:
        List of accounts owned by current user

    Example Request:
        GET /api/v1/accounts
        Authorization: Bearer <token>

    Example Response:
        200 OK
        [
            {
                "id": "uuid-1",
                "user_id": "uuid-user",
                "name": "HDFC Savings",
                "currency": "INR",
                "opening_balance": 5000.00,
                "created_at": "2024-01-15T10:30:00Z"
            },
            {
                "id": "uuid-2",
                "user_id": "uuid-user",
                "name": "Cash Wallet",
                "currency": "INR",
                "opening_balance": 1000.00,
                "created_at": "2024-01-16T12:00:00Z"
            }
        ]
    """
    # Authorization: Only fetch accounts belonging to current user
    accounts = (
        db.query(Account)
        .filter(Account.user_id == current_user.id)  # Critical security filter!
        .order_by(Account.created_at.desc())
        .all()
    )

    # Convert each account to human-readable format
    return [AccountRead.from_db_model(account) for account in accounts]


@router.get("/with-balance", response_model=List[AccountWithBalance])
def list_accounts_with_balance(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> List[AccountWithBalance]:
    """
    List all accounts with calculated current balances.

    Authorization:
    - Only returns accounts where user_id = current_user.id

    Balance Calculation:
    - current_balance = opening_balance + sum(all transaction amounts)
    - Derived on-demand (ADR-004: No cached balances in MVP)

    Steps:
    1. Query accounts for current user
    2. For each account, sum all transaction amounts
    3. Calculate current_balance = opening + sum(transactions)
    4. Return accounts with balances

    Args:
        current_user: Injected authenticated user
        db: Database session

    Returns:
        List of accounts with current balances

    Example Response:
        200 OK
        [
            {
                "id": "uuid-1",
                "user_id": "uuid-user",
                "name": "HDFC Savings",
                "currency": "INR",
                "opening_balance": 5000.00,
                "current_balance": 4200.50,  // opening + sum(transactions)
                "created_at": "2024-01-15T10:30:00Z"
            }
        ]
    """
    # Authorization: Only fetch accounts belonging to current user
    accounts = (
        db.query(Account)
        .filter(Account.user_id == current_user.id)
        .order_by(Account.created_at.desc())
        .all()
    )

    accounts_with_balance = []

    for account in accounts:
        # Calculate sum of all transactions for this account
        # Uses aggregate function for efficiency
        transaction_sum = (
            db.query(func.sum(Transaction.amount_minor))
            .filter(Transaction.account_id == account.id)
            .scalar()
        ) or 0  # Return 0 if no transactions

        # Calculate current balance in minor units
        current_balance_minor = account.opening_balance_minor + transaction_sum

        # Convert to human-readable format
        from decimal import Decimal

        account_dict = AccountRead.from_db_model(account).model_dump()
        account_dict["current_balance"] = Decimal(current_balance_minor) / 100

        accounts_with_balance.append(AccountWithBalance(**account_dict))

    return accounts_with_balance


@router.get("/{account_id}", response_model=AccountRead)
def get_account(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> AccountRead:
    """
    Get a specific account by ID.

    Authorization:
    - Account must belong to current user
    - Returns 404 if account doesn't exist OR doesn't belong to user

    Steps:
    1. Query account by ID
    2. Verify user_id matches current_user.id
    3. Return account data

    Args:
        account_id: UUID of account to retrieve
        current_user: Injected authenticated user
        db: Database session

    Returns:
        Account data if found and owned by current user

    Raises:
        HTTPException 404: If account not found or not owned by current user

    Example Request:
        GET /api/v1/accounts/123e4567-e89b-12d3-a456-426614174000
        Authorization: Bearer <token>

    Example Response:
        200 OK
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "user_id": "uuid-user",
            "name": "HDFC Savings",
            "currency": "INR",
            "opening_balance": 5000.00,
            "created_at": "2024-01-15T10:30:00Z"
        }
    """
    # Authorization: Query with both account_id AND user_id
    # This ensures users can only access their own accounts
    account = (
        db.query(Account)
        .filter(
            Account.id == account_id,
            Account.user_id == current_user.id,  # Critical security filter!
        )
        .first()
    )

    if not account:
        # Don't reveal whether account exists - just say "not found"
        # This prevents user enumeration
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    return AccountRead.from_db_model(account)
