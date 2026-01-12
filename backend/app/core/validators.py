"""
Validation helpers for financial operations.
Ensures data integrity and business rule compliance.
"""

from datetime import date
from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.user import User
from app.core.exceptions import (
    ValidationException,
    InvalidAmountException,
    InvalidDateException,
    CurrencyMismatchException,
    InvalidTransferException,
    AccountOwnershipException,
    NotFoundException,
)


def validate_transaction_date(transaction_date: date) -> None:
    """
    Validate that transaction date is not in the future.

    Args:
        transaction_date: Date to validate

    Raises:
        InvalidDateException: If date is in the future
    """
    today = date.today()
    if transaction_date > today:
        raise InvalidDateException(
            message=f"Transaction date cannot be in the future. Today is {today}",
            date_value=str(transaction_date),
        )


def validate_amount_not_zero(amount: Decimal, context: str = "Amount") -> None:
    """
    Validate that amount is not zero.

    Args:
        amount: Amount to validate
        context: Description of what the amount is for

    Raises:
        InvalidAmountException: If amount is zero
    """
    if amount == 0:
        raise InvalidAmountException(
            message=f"{context} cannot be zero",
            amount=float(amount),
        )


def validate_amount_positive(amount: Decimal, context: str = "Amount") -> None:
    """
    Validate that amount is positive (greater than zero).

    Args:
        amount: Amount to validate
        context: Description of what the amount is for

    Raises:
        InvalidAmountException: If amount is not positive
    """
    if amount <= 0:
        raise InvalidAmountException(
            message=f"{context} must be positive. Got: {amount}",
            amount=float(amount),
        )


def validate_currency_code(currency: str) -> str:
    """
    Validate currency code format and value.

    Args:
        currency: Currency code to validate

    Returns:
        Uppercase currency code

    Raises:
        ValidationException: If currency code is invalid
    """
    currency = currency.upper().strip()

    if len(currency) != 3:
        raise ValidationException(
            message="Currency code must be exactly 3 characters",
            field="currency",
        )

    # List of supported currencies
    SUPPORTED_CURRENCIES = {
        "INR", "USD", "EUR", "GBP", "JPY",
        "AUD", "CAD", "CHF", "CNY", "SGD",
    }

    if currency not in SUPPORTED_CURRENCIES:
        raise ValidationException(
            message=f"Unsupported currency: {currency}. "
            f"Supported: {', '.join(sorted(SUPPORTED_CURRENCIES))}",
            field="currency",
        )

    return currency


def validate_account_ownership(
    db: Session,
    account_id: uuid.UUID,
    user: User,
) -> Account:
    """
    Validate that account exists and belongs to user.

    Args:
        db: Database session
        account_id: Account ID to validate
        user: User who should own the account

    Returns:
        Account object if valid

    Raises:
        NotFoundException: If account not found or doesn't belong to user
    """
    account = (
        db.query(Account)
        .filter(
            Account.id == account_id,
            Account.user_id == user.id,
        )
        .first()
    )

    if not account:
        # Don't reveal if account exists - just say "not found"
        # This prevents user enumeration attacks
        raise NotFoundException(resource="Account")

    return account


def validate_currency_match(
    currency1: str,
    currency2: str,
    context: str = "operation",
) -> None:
    """
    Validate that two currency codes match.

    Args:
        currency1: First currency code
        currency2: Second currency code
        context: Description of the operation

    Raises:
        CurrencyMismatchException: If currencies don't match
    """
    if currency1.upper() != currency2.upper():
        raise CurrencyMismatchException(
            expected=currency1.upper(),
            received=currency2.upper(),
            context=context,
        )


def validate_transfer_accounts(
    db: Session,
    from_account_id: uuid.UUID,
    to_account_id: uuid.UUID,
    user: User,
) -> tuple[Account, Account]:
    """
    Validate accounts for a transfer operation.

    Checks:
    1. Both accounts exist
    2. Both belong to the same user
    3. Accounts are different
    4. Currencies match

    Args:
        db: Database session
        from_account_id: Source account ID
        to_account_id: Destination account ID
        user: User making the transfer

    Returns:
        Tuple of (from_account, to_account)

    Raises:
        InvalidTransferException: If transfer is invalid
        AccountOwnershipException: If accounts belong to different users
        CurrencyMismatchException: If currencies don't match
    """
    # Check accounts are different
    if from_account_id == to_account_id:
        raise InvalidTransferException(
            message="Cannot transfer to the same account",
            details={
                "from_account_id": str(from_account_id),
                "to_account_id": str(to_account_id),
            },
        )

    # Fetch and validate both accounts
    from_account = validate_account_ownership(db, from_account_id, user)
    to_account = validate_account_ownership(db, to_account_id, user)

    # Verify both accounts belong to the same user (redundant but explicit)
    if from_account.user_id != to_account.user_id:
        raise AccountOwnershipException(
            message="Cannot transfer between accounts of different users"
        )

    # Verify currencies match
    validate_currency_match(
        from_account.currency,
        to_account.currency,
        context="transfer",
    )

    return from_account, to_account


def validate_decimal_places(
    amount: Decimal,
    max_places: int = 2,
    context: str = "Amount",
) -> None:
    """
    Validate that amount has at most N decimal places.

    Args:
        amount: Amount to validate
        max_places: Maximum allowed decimal places
        context: Description of what the amount is for

    Raises:
        ValidationException: If too many decimal places
    """
    if amount.as_tuple().exponent < -max_places:
        raise ValidationException(
            message=f"{context} must have at most {max_places} decimal places",
            field="amount",
        )
