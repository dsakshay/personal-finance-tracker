"""
Transaction management endpoints.
All operations are scoped to the authenticated user.
Transfers are handled atomically with two linked transactions.
"""

from typing import Annotated, List
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.models.account import Account
from app.models.transaction import Transaction, TransactionType
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionListResponse,
    TransferCreate,
    TransferResponse,
)

router = APIRouter()


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction_data: TransactionCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> TransactionResponse:
    """
    Create a new transaction (income or expense).

    For transfers, use POST /transactions/transfer endpoint instead.

    Authorization:
    - Account must belong to current user
    - Transaction automatically owned by current user

    Validation:
    - Transaction date cannot be in the future
    - Amount cannot be zero
    - Currency must match account currency
    - Type must be income or expense (not transfer)

    Steps:
    1. Validate transaction date (not future)
    2. Fetch and verify account ownership
    3. Validate currency matches account
    4. Create transaction
    5. Save to database

    Args:
        transaction_data: Transaction details from request body
        current_user: Injected authenticated user
        db: Database session

    Returns:
        Created transaction with human-readable amounts

    Raises:
        HTTPException 400: Invalid data or business rule violation
        HTTPException 404: Account not found or not owned by user

    Example Request:
        POST /api/v1/transactions
        Authorization: Bearer <token>
        {
            "account_id": "uuid...",
            "amount": -250.50,
            "currency": "INR",
            "transaction_type": "expense",
            "tag": "groceries",
            "payment_method": "card",
            "description": "Weekly shopping",
            "transaction_date": "2024-01-15"
        }
    """
    # Validate: transaction date cannot be in the future
    today = date.today()
    txn_date = date.fromisoformat(transaction_data.transaction_date)
    if txn_date > today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction date cannot be in the future. Today is {today}",
        )

    # Validate: Use /transfer endpoint for transfers
    if transaction_data.transaction_type == TransactionType.TRANSFER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use POST /transactions/transfer endpoint for transfers",
        )

    # Authorization: Verify account belongs to current user
    account = (
        db.query(Account)
        .filter(
            Account.id == transaction_data.account_id,
            Account.user_id == current_user.id,  # 🔒 Security check
        )
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    # Validate: Currency must match account currency
    if transaction_data.currency.upper() != account.currency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Currency mismatch. Account uses {account.currency}, "
            f"transaction uses {transaction_data.currency}",
        )

    # Convert amount to minor units with sign based on transaction type
    amount_minor = transaction_data.to_minor_units(transaction_data.transaction_type)

    # Create transaction
    new_transaction = Transaction(
        user_id=current_user.id,  # Owned by current user
        account_id=transaction_data.account_id,
        amount_minor=amount_minor,
        currency=transaction_data.currency.upper(),
        transaction_type=transaction_data.transaction_type,
        tag=transaction_data.tag,
        payment_method=transaction_data.payment_method,
        description=transaction_data.description,
        transaction_date=txn_date,
    )

    # Save to database
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    # Return response with account name
    return TransactionResponse.from_db_model(
        new_transaction,
        account_name=account.name,
    )


@router.post("/transfer", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
def create_transfer(
    transfer_data: TransferCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> TransferResponse:
    """
    Create a transfer between two accounts (atomic operation).

    Transfers are represented as TWO linked transactions (ADR-006):
    1. Debit transaction: from_account, negative amount
    2. Credit transaction: to_account, positive amount

    Atomicity:
    - Both transactions are created in a single database transaction
    - If either fails, both are rolled back
    - Uses db.commit() only after both are created

    Authorization:
    - Both accounts must belong to current user
    - Cannot transfer between accounts of different users

    Validation:
    - Amount must be positive
    - Accounts must use same currency
    - Transaction date cannot be in the future
    - Source and destination accounts must be different

    Steps:
    1. Validate transaction date
    2. Fetch both accounts and verify ownership
    3. Validate accounts are different
    4. Validate currencies match
    5. Create debit transaction (from_account)
    6. Create credit transaction (to_account)
    7. Link them via related_account_id
    8. Commit atomically (both or neither)

    Args:
        transfer_data: Transfer details from request body
        current_user: Injected authenticated user
        db: Database session

    Returns:
        List of two created transactions [debit, credit]

    Raises:
        HTTPException 400: Invalid data or business rule violation
        HTTPException 404: Account(s) not found or not owned by user

    Example Request:
        POST /api/v1/transactions/transfer
        Authorization: Bearer <token>
        {
            "from_account_id": "uuid-1",
            "to_account_id": "uuid-2",
            "amount": 1000.00,
            "currency": "INR",
            "tag": "transfer",
            "description": "Moving to savings",
            "transaction_date": "2024-01-15"
        }

    Example Response:
        201 Created
        [
            {
                "id": "txn-1",
                "account_id": "uuid-1",
                "amount": -1000.00,  // Debit (outgoing)
                "transaction_type": "transfer",
                "related_account_id": "uuid-2",
                ...
            },
            {
                "id": "txn-2",
                "account_id": "uuid-2",
                "amount": 1000.00,  // Credit (incoming)
                "transaction_type": "transfer",
                "related_account_id": "uuid-1",
                ...
            }
        ]
    """
    # Validate: transaction date cannot be in the future
    today = date.today()
    txn_date = date.fromisoformat(transfer_data.transaction_date)
    if txn_date > today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction date cannot be in the future. Today is {today}",
        )

    # Validate: Accounts must be different
    if transfer_data.account_id == transfer_data.related_account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot transfer to the same account",
        )

    # Authorization: Fetch both accounts and verify ownership
    from_account = (
        db.query(Account)
        .filter(
            Account.id == transfer_data.account_id,
            Account.user_id == current_user.id,  # 🔒 Security check
        )
        .first()
    )

    to_account = (
        db.query(Account)
        .filter(
            Account.id == transfer_data.related_account_id,
            Account.user_id == current_user.id,  # 🔒 Security check
        )
        .first()
    )

    if not from_account or not to_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both accounts not found",
        )

    # Validate: Currencies must match
    if from_account.currency != to_account.currency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Currency mismatch. From account uses {from_account.currency}, "
            f"to account uses {to_account.currency}",
        )

    # Validate: Transfer currency must match accounts
    if transfer_data.currency.upper() != from_account.currency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Currency mismatch. Accounts use {from_account.currency}, "
            f"transfer uses {transfer_data.currency}",
        )

    # Convert amount to minor units
    amount_minor = int(Decimal(transfer_data.amount) * 100)

    try:
        # === ATOMIC OPERATION START ===
        # Both transactions are created in the same database transaction
        # If either fails, both are rolled back

        # Transaction 1: Debit (money leaving from_account)
        debit_transaction = Transaction(
            user_id=current_user.id,
            account_id=transfer_data.account_id,
            amount_minor=-amount_minor,  # Negative = outgoing
            currency=transfer_data.currency.upper(),
            transaction_type=TransactionType.TRANSFER,
            tag=transfer_data.tag,
            payment_method=transfer_data.payment_method or "transfer",
            related_account_id=transfer_data.related_account_id,  # Link to destination
            description=transfer_data.description,
            transaction_date=txn_date,
        )

        # Transaction 2: Credit (money arriving at to_account)
        credit_transaction = Transaction(
            user_id=current_user.id,
            account_id=transfer_data.related_account_id,
            amount_minor=amount_minor,  # Positive = incoming
            currency=transfer_data.currency.upper(),
            transaction_type=TransactionType.TRANSFER,
            tag=transfer_data.tag,
            payment_method=transfer_data.payment_method or "transfer",
            related_account_id=transfer_data.account_id,  # Link to source
            description=transfer_data.description,
            transaction_date=txn_date,
        )

        # Add both to session
        db.add(debit_transaction)
        db.add(credit_transaction)

        # Commit both together (atomic)
        db.commit()

        # Refresh to get generated IDs
        db.refresh(debit_transaction)
        db.refresh(credit_transaction)

        # === ATOMIC OPERATION END ===

        # Return transfer response with both transactions
        return TransferResponse(
            transfer_id=str(debit_transaction.id),  # Use debit transaction ID as transfer ID
            transactions=[
                TransactionResponse.from_db_model(
                    debit_transaction,
                    account_name=from_account.name,
                    related_account_name=to_account.name,
                ),
                TransactionResponse.from_db_model(
                    credit_transaction,
                    account_name=to_account.name,
                    related_account_name=from_account.name,
                ),
            ],
        )

    except IntegrityError as e:
        # Rollback if any constraint violation
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {str(e)}",
        )


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    account_id: uuid.UUID | None = None,
    transaction_type: TransactionType | None = None,
    tag: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> TransactionListResponse:
    """
    List transactions for the authenticated user with optional filters.

    Authorization:
    - Only returns transactions where user_id = current_user.id
    - If account_id filter is provided, verifies account belongs to user

    Query Parameters:
    - account_id: Filter by specific account (optional)
    - transaction_type: Filter by type (income/expense/transfer) (optional)
    - tag: Filter by tag (optional)
    - limit: Max number of results (default 100, max 500)
    - offset: Number of results to skip for pagination (default 0)

    Args:
        current_user: Injected authenticated user
        db: Database session
        account_id: Optional account filter
        transaction_type: Optional type filter
        tag: Optional tag filter
        limit: Result limit
        offset: Pagination offset

    Returns:
        List of transactions matching filters, sorted by date (newest first)

    Example Request:
        GET /api/v1/transactions?account_id=uuid&transaction_type=expense&limit=50
        Authorization: Bearer <token>

    Example Response:
        200 OK
        [
            {
                "id": "txn-1",
                "user_id": "user-uuid",
                "account_id": "account-uuid",
                "amount": -250.50,
                "currency": "INR",
                "transaction_type": "expense",
                "tag": "groceries",
                "payment_method": "card",
                "description": "Weekly shopping",
                "transaction_date": "2024-01-15",
                "created_at": "2024-01-15T18:30:00Z"
            },
            ...
        ]
    """
    # Validate limit
    if limit > 500:
        limit = 500

    # If account_id is provided, verify it belongs to current user
    if account_id:
        account = (
            db.query(Account)
            .filter(
                Account.id == account_id,
                Account.user_id == current_user.id,  # 🔒 Security check
            )
            .first()
        )

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found",
            )

    # Build query with authorization filter
    query = db.query(Transaction).filter(
        Transaction.user_id == current_user.id  # 🔒 Always filter by user
    )

    # Apply optional filters
    if account_id:
        query = query.filter(Transaction.account_id == account_id)

    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)

    if tag:
        query = query.filter(Transaction.tag == tag.lower())

    # Order by transaction date (newest first), then created_at
    query = query.order_by(
        Transaction.transaction_date.desc(),
        Transaction.created_at.desc(),
    )

    # Get total count before pagination
    total_count = query.count()

    # Apply pagination
    transactions = query.limit(limit).offset(offset).all()

    # Fetch all unique account IDs from transactions
    account_ids = set()
    for txn in transactions:
        account_ids.add(txn.account_id)
        if txn.related_account_id:
            account_ids.add(txn.related_account_id)

    # Fetch all accounts in one query
    accounts_map = {}
    if account_ids:
        accounts = db.query(Account).filter(Account.id.in_(account_ids)).all()
        accounts_map = {account.id: account.name for account in accounts}

    # Convert to response format with denormalized account names
    transaction_responses = []
    for txn in transactions:
        account_name = accounts_map.get(txn.account_id, "Unknown")
        related_account_name = accounts_map.get(txn.related_account_id) if txn.related_account_id else None
        transaction_responses.append(
            TransactionResponse.from_db_model(
                txn,
                account_name=account_name,
                related_account_name=related_account_name,
            )
        )

    return TransactionListResponse(
        transactions=transaction_responses,
        total_count=total_count,
        limit=limit,
        offset=offset,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> TransactionResponse:
    """
    Get a specific transaction by ID.

    Authorization:
    - Transaction must belong to current user
    - Returns 404 if not found or not owned by user

    Args:
        transaction_id: UUID of transaction to retrieve
        current_user: Injected authenticated user
        db: Database session

    Returns:
        Transaction data if found and owned by current user

    Raises:
        HTTPException 404: If transaction not found or not owned by user

    Example Request:
        GET /api/v1/transactions/abc12345-6789-def0-1234-56789abcdef0
        Authorization: Bearer <token>
    """
    # Authorization: Query with both transaction_id AND user_id
    transaction = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id,  # 🔒 Security check
        )
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    # Fetch account name
    account = db.query(Account).filter(Account.id == transaction.account_id).first()
    account_name = account.name if account else "Unknown"

    # Fetch related account name if transfer
    related_account_name = None
    if transaction.related_account_id:
        related_account = db.query(Account).filter(Account.id == transaction.related_account_id).first()
        related_account_name = related_account.name if related_account else "Unknown"

    return TransactionResponse.from_db_model(
        transaction,
        account_name=account_name,
        related_account_name=related_account_name,
    )
