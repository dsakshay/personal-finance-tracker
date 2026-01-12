"""
Transaction schemas for API request/response validation.
Handles conversion between human-readable amounts and minor units.
API Contract: docs/backend/api-contracts.md
"""

import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.transaction import TransactionType


class TransactionCreate(BaseModel):
    """
    Schema for creating a new transaction (POST /transactions).

    API Contract: docs/backend/api-contracts.md#3-post-transactions
    Client sends POSITIVE amounts only. Backend applies sign based on transaction_type.
    """

    account_id: uuid.UUID = Field(..., description="Account ID where transaction occurs")

    amount: str = Field(
        ...,
        description="Transaction amount (positive decimal string, e.g., '500.00')",
        examples=["500.00", "250.50", "1000.00"],
        pattern=r"^\d+\.\d{2}$",
    )

    currency: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="ISO 4217 currency code (must match account currency)",
        examples=["INR", "USD"],
    )

    transaction_type: TransactionType = Field(
        ...,
        description="Transaction type: income, expense, or transfer",
    )

    tag: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Category/tag for the transaction",
        examples=["groceries", "salary", "rent", "utilities"],
    )

    payment_method: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Payment method used",
        examples=["cash", "card", "upi", "bank_transfer"],
    )

    description: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional description/note",
    )

    transaction_date: str = Field(
        ...,
        description="Date when transaction occurred (ISO 8601: YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        examples=["2026-01-12", "2026-01-15"],
    )

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: str) -> str:
        """
        Validate amount format.

        Requirements:
        - Valid decimal string with exactly 2 decimal places
        - Must be positive (sign applied by backend based on transaction_type)
        - Format: [0-9]+\.[0-9]{2}
        - Max: 9999999999.99 (10 billion limit)
        """
        try:
            decimal_value = Decimal(v)
        except Exception:
            raise ValueError("Amount must be a valid decimal string")

        # Must be positive
        if decimal_value <= 0:
            raise ValueError("Amount must be positive (sign determined by transaction_type)")

        # Check decimal places
        if decimal_value.as_tuple().exponent != -2:
            raise ValueError("Amount must have exactly 2 decimal places (e.g., '500.00')")

        # Check range
        max_value = Decimal("9999999999.99")
        if decimal_value > max_value:
            raise ValueError("Amount must be less than 9999999999.99")

        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code format and value."""
        v = v.upper()

        if len(v) != 3:
            raise ValueError("Currency code must be exactly 3 characters")

        if not v.isalpha():
            raise ValueError("Currency code must contain only letters")

        valid_currencies = {
            "INR", "USD", "EUR", "GBP", "JPY",
            "AUD", "CAD", "CHF", "CNY", "SGD",
        }
        if v not in valid_currencies:
            raise ValueError(
                f"Unsupported currency '{v}'. Supported: {', '.join(sorted(valid_currencies))}"
            )
        return v

    @field_validator("tag")
    @classmethod
    def validate_tag(cls, v: str) -> str:
        """Ensure tag is not empty."""
        v = v.lower().strip()
        if not v:
            raise ValueError("Tag cannot be empty")
        return v

    @field_validator("transaction_date")
    @classmethod
    def validate_transaction_date(cls, v: str) -> str:
        """Validate date is in ISO 8601 format."""
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError("Transaction date must be in ISO 8601 format (YYYY-MM-DD)")
        return v

    def to_minor_units(self, transaction_type: TransactionType) -> int:
        """
        Convert amount to minor units with appropriate sign.

        Args:
            transaction_type: Transaction type to determine sign

        Returns:
            Signed amount in minor units (paise/cents)

        Examples:
        - "500.00", expense → -50000 paise
        - "500.00", income → +50000 paise
        - "1000.00", transfer → handled separately (creates two transactions)
        """
        decimal_value = Decimal(self.amount)
        amount_minor = int(decimal_value * 100)

        # Apply sign based on transaction type
        if transaction_type == TransactionType.EXPENSE:
            return -amount_minor  # Negative for expenses
        else:
            return amount_minor  # Positive for income

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "550e8400-e29b-41d4-a716-446655440000",
                "amount": "500.00",
                "currency": "INR",
                "transaction_type": "expense",
                "tag": "groceries",
                "payment_method": "card",
                "description": "Weekly grocery shopping",
                "transaction_date": "2026-01-12",
            }
        }


class TransactionResponse(BaseModel):
    """
    Schema for transaction responses (POST /transactions, GET /transactions).

    API Contract: docs/backend/api-contracts.md#3-post-transactions
    Returns signed decimal strings (negative for outflow, positive for inflow).
    """

    id: str = Field(..., description="Transaction unique identifier (UUID)")
    account_id: str = Field(..., description="Account ID (UUID)")
    account_name: str = Field(..., description="Account name (denormalized)")
    amount: str = Field(..., description="Signed amount (decimal string, e.g., '-500.00')")
    currency: str = Field(..., description="ISO 4217 currency code")
    transaction_type: str = Field(..., description="Transaction type")
    tag: str = Field(..., description="Category/tag")
    payment_method: Optional[str] = Field(None, description="Payment method")
    related_account_id: Optional[str] = Field(None, description="Related account UUID (for transfers)")
    related_account_name: Optional[str] = Field(None, description="Related account name (for transfers)")
    description: Optional[str] = Field(None, description="Description/note")
    transaction_date: str = Field(..., description="Transaction date (ISO 8601)")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")

    @classmethod
    def from_db_model(
        cls,
        transaction: "Transaction",
        account_name: str,
        related_account_name: Optional[str] = None,
    ) -> "TransactionResponse":
        """
        Create response schema from SQLAlchemy model.

        Converts minor units to signed decimal strings.

        Args:
            transaction: SQLAlchemy Transaction model instance
            account_name: Account name (from join or separate query)
            related_account_name: Related account name (for transfers)

        Returns:
            TransactionResponse with decimal string amounts
        """
        # Convert amount to decimal string
        amount_decimal = Decimal(transaction.amount_minor) / 100

        return cls(
            id=str(transaction.id),
            account_id=str(transaction.account_id),
            account_name=account_name,
            amount=f"{amount_decimal:.2f}",
            currency=transaction.currency,
            transaction_type=transaction.transaction_type.value,
            tag=transaction.tag,
            payment_method=transaction.payment_method,
            related_account_id=str(transaction.related_account_id) if transaction.related_account_id else None,
            related_account_name=related_account_name,
            description=transaction.description,
            transaction_date=transaction.transaction_date.isoformat(),
            created_at=transaction.created_at.isoformat(),
        )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "c3d4e5f6-a7b8-5c9d-0e1f-2a3b4c5d6e7f",
                "account_id": "550e8400-e29b-41d4-a716-446655440000",
                "account_name": "Checking",
                "amount": "-500.00",
                "currency": "INR",
                "transaction_type": "expense",
                "tag": "groceries",
                "payment_method": "card",
                "related_account_id": None,
                "related_account_name": None,
                "description": "Weekly grocery shopping",
                "transaction_date": "2026-01-12",
                "created_at": "2026-01-12T10:30:00Z",
            }
        }


class TransactionListResponse(BaseModel):
    """
    Schema for GET /transactions response.

    API Contract: docs/backend/api-contracts.md#4-get-transactions
    """

    transactions: list[TransactionResponse] = Field(..., description="List of transactions")
    total_count: int = Field(..., description="Total transactions matching filters")
    limit: int = Field(..., description="Results per page")
    offset: int = Field(..., description="Current offset")

    class Config:
        json_schema_extra = {
            "example": {
                "transactions": [
                    {
                        "id": "c3d4e5f6-a7b8-5c9d-0e1f-2a3b4c5d6e7f",
                        "account_id": "550e8400-e29b-41d4-a716-446655440000",
                        "account_name": "Checking",
                        "amount": "-500.00",
                        "currency": "INR",
                        "transaction_type": "expense",
                        "tag": "groceries",
                        "payment_method": "card",
                        "related_account_id": None,
                        "related_account_name": None,
                        "description": "Weekly shopping",
                        "transaction_date": "2026-01-12",
                        "created_at": "2026-01-12T10:30:00Z",
                    }
                ],
                "total_count": 1,
                "limit": 50,
                "offset": 0,
            }
        }


class TransferCreate(BaseModel):
    """
    Schema for creating a transfer between two accounts.

    API Contract: docs/backend/api-contracts.md#3-post-transactions (transfer)
    Creates two linked transactions atomically.
    """

    account_id: uuid.UUID = Field(..., description="Source account ID")
    amount: str = Field(
        ...,
        description="Transfer amount (positive decimal string, e.g., '1000.00')",
        examples=["1000.00", "500.50"],
        pattern=r"^\d+\.\d{2}$",
    )
    currency: str = Field(..., description="Currency code (must match both accounts)")
    transaction_type: str = Field(
        default="transfer",
        description="Must be 'transfer'",
        pattern=r"^transfer$",
    )
    tag: str = Field(
        default="transfer",
        description="Category/tag",
    )
    payment_method: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Payment method",
    )
    related_account_id: uuid.UUID = Field(..., description="Destination account ID")
    description: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional transfer note",
    )
    transaction_date: str = Field(
        ...,
        description="Transfer date (ISO 8601: YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: str) -> str:
        """Ensure amount is positive and has exactly 2 decimal places."""
        try:
            decimal_value = Decimal(v)
        except Exception:
            raise ValueError("Amount must be a valid decimal string")

        if decimal_value <= 0:
            raise ValueError("Transfer amount must be positive")

        if decimal_value.as_tuple().exponent != -2:
            raise ValueError("Amount must have exactly 2 decimal places (e.g., '1000.00')")

        max_value = Decimal("9999999999.99")
        if decimal_value > max_value:
            raise ValueError("Amount must be less than 9999999999.99")

        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        v = v.upper()

        if len(v) != 3 or not v.isalpha():
            raise ValueError("Currency must be 3 letters")

        valid_currencies = {
            "INR", "USD", "EUR", "GBP", "JPY",
            "AUD", "CAD", "CHF", "CNY", "SGD",
        }
        if v not in valid_currencies:
            raise ValueError(
                f"Unsupported currency '{v}'. Supported: {', '.join(sorted(valid_currencies))}"
            )
        return v

    @field_validator("transaction_date")
    @classmethod
    def validate_transaction_date(cls, v: str) -> str:
        """Validate date is in ISO 8601 format."""
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError("Transaction date must be in ISO 8601 format (YYYY-MM-DD)")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "550e8400-e29b-41d4-a716-446655440000",
                "amount": "1000.00",
                "currency": "INR",
                "transaction_type": "transfer",
                "tag": "transfer",
                "related_account_id": "660e8400-e29b-41d4-a716-446655440111",
                "description": "Moving to savings",
                "transaction_date": "2026-01-12",
            }
        }


class TransferResponse(BaseModel):
    """
    Schema for transfer response (returns 2 transactions).

    API Contract: docs/backend/api-contracts.md#3-post-transactions (transfer response)
    """

    transfer_id: str = Field(..., description="Logical transfer identifier")
    transactions: list[TransactionResponse] = Field(..., description="Two linked transactions")

    class Config:
        json_schema_extra = {
            "example": {
                "transfer_id": "e5f6a7b8-c9d0-7e1f-2a3b-4c5d6e7f8a9b",
                "transactions": [
                    {
                        "id": "f6a7b8c9-d0e1-8f2a-3b4c-5d6e7f8a9b0c",
                        "account_id": "550e8400-e29b-41d4-a716-446655440000",
                        "account_name": "Checking",
                        "amount": "-1000.00",
                        "currency": "INR",
                        "transaction_type": "transfer",
                        "tag": "transfer",
                        "payment_method": None,
                        "related_account_id": "660e8400-e29b-41d4-a716-446655440111",
                        "related_account_name": "Savings",
                        "description": "Moving to savings",
                        "transaction_date": "2026-01-12",
                        "created_at": "2026-01-12T10:40:00Z",
                    },
                    {
                        "id": "a7b8c9d0-e1f2-9a3b-4c5d-6e7f8a9b0c1d",
                        "account_id": "660e8400-e29b-41d4-a716-446655440111",
                        "account_name": "Savings",
                        "amount": "1000.00",
                        "currency": "INR",
                        "transaction_type": "transfer",
                        "tag": "transfer",
                        "payment_method": None,
                        "related_account_id": "550e8400-e29b-41d4-a716-446655440000",
                        "related_account_name": "Checking",
                        "description": "Moving to savings",
                        "transaction_date": "2026-01-12",
                        "created_at": "2026-01-12T10:40:00Z",
                    },
                ],
            }
        }
