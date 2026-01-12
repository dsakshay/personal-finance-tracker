"""
Transaction schemas for API request/response validation.
Handles conversion between human-readable amounts and minor units.
"""

import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.transaction import TransactionType


class TransactionCreate(BaseModel):
    """
    Schema for creating a new transaction.

    Used when: POST /api/v1/transactions
    Amount is in human-readable format (rupees/dollars), converted to minor units internally.
    """

    account_id: uuid.UUID = Field(..., description="Account ID where transaction occurs")

    amount: Decimal = Field(
        ...,
        description="Amount in human format. Positive=income, Negative=expense",
        examples=[500.00, -250.50, 1000],
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

    related_account_id: Optional[uuid.UUID] = Field(
        default=None,
        description="For transfers: the other account involved",
    )

    description: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional description/note",
    )

    transaction_date: date = Field(
        ...,
        description="Date when transaction occurred (can differ from creation time)",
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code is uppercase 3-letter code."""
        v = v.upper()
        valid_currencies = {
            "INR",
            "USD",
            "EUR",
            "GBP",
            "JPY",
            "AUD",
            "CAD",
            "CHF",
            "CNY",
            "SGD",
        }
        if v not in valid_currencies:
            raise ValueError(
                f"Invalid currency code. Must be one of: {', '.join(sorted(valid_currencies))}"
            )
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Ensure amount has at most 2 decimal places and is not zero."""
        if v == 0:
            raise ValueError("Amount cannot be zero")
        if v.as_tuple().exponent < -2:
            raise ValueError("Amount must have at most 2 decimal places")
        return v

    @field_validator("tag")
    @classmethod
    def validate_tag(cls, v: str) -> str:
        """Ensure tag is lowercase and alphanumeric with underscores."""
        v = v.lower().strip()
        if not v:
            raise ValueError("Tag cannot be empty")
        return v

    @field_validator("transaction_type")
    @classmethod
    def validate_transaction_type(cls, v: TransactionType) -> TransactionType:
        """Validate transaction type is one of the allowed enum values."""
        if v not in TransactionType:
            raise ValueError(
                f"Invalid transaction type. Must be one of: {', '.join([t.value for t in TransactionType])}"
            )
        return v

    def to_minor_units(self) -> int:
        """
        Convert amount to minor units (paise/cents).

        Examples:
        - ₹500.00 → 50000 paise
        - -$25.50 → -2550 cents
        """
        return int(self.amount * 100)

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "account_id": "123e4567-e89b-12d3-a456-426614174000",
                    "amount": -250.50,
                    "currency": "INR",
                    "transaction_type": "expense",
                    "tag": "groceries",
                    "payment_method": "card",
                    "description": "Weekly grocery shopping",
                    "transaction_date": "2024-01-15",
                },
                {
                    "account_id": "123e4567-e89b-12d3-a456-426614174000",
                    "amount": 50000.00,
                    "currency": "INR",
                    "transaction_type": "income",
                    "tag": "salary",
                    "payment_method": "bank_transfer",
                    "description": "January salary",
                    "transaction_date": "2024-01-01",
                },
            ]
        }


class TransactionRead(BaseModel):
    """
    Schema for reading transaction data (responses).

    Used when: GET /api/v1/transactions, GET /api/v1/transactions/{id}
    Converts minor units back to human-readable format.
    """

    id: uuid.UUID = Field(..., description="Transaction unique identifier")
    user_id: uuid.UUID = Field(..., description="Owner user ID")
    account_id: uuid.UUID = Field(..., description="Account ID")
    amount: Decimal = Field(..., description="Amount in human format")
    currency: str = Field(..., description="ISO 4217 currency code")
    transaction_type: TransactionType = Field(..., description="Transaction type")
    tag: str = Field(..., description="Category/tag")
    payment_method: Optional[str] = Field(None, description="Payment method")
    related_account_id: Optional[uuid.UUID] = Field(
        None, description="Related account for transfers"
    )
    description: Optional[str] = Field(None, description="Description/note")
    transaction_date: date = Field(..., description="Transaction date")
    created_at: datetime = Field(..., description="Record creation timestamp")

    @classmethod
    def from_db_model(cls, transaction: "Transaction") -> "TransactionRead":
        """
        Create schema from SQLAlchemy model, converting minor units to decimal.

        Args:
            transaction: SQLAlchemy Transaction model instance

        Returns:
            TransactionRead schema with human-readable amounts
        """
        return cls(
            id=transaction.id,
            user_id=transaction.user_id,
            account_id=transaction.account_id,
            amount=Decimal(transaction.amount_minor) / 100,
            currency=transaction.currency,
            transaction_type=transaction.transaction_type,
            tag=transaction.tag,
            payment_method=transaction.payment_method,
            related_account_id=transaction.related_account_id,
            description=transaction.description,
            transaction_date=transaction.transaction_date,
            created_at=transaction.created_at,
        )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "abc12345-6789-def0-1234-56789abcdef0",
                "user_id": "987fcdeb-51a2-43f1-9876-543210fedcba",
                "account_id": "123e4567-e89b-12d3-a456-426614174000",
                "amount": -250.50,
                "currency": "INR",
                "transaction_type": "expense",
                "tag": "groceries",
                "payment_method": "card",
                "related_account_id": None,
                "description": "Weekly grocery shopping",
                "transaction_date": "2024-01-15",
                "created_at": "2024-01-15T18:30:00Z",
            }
        }


class TransferCreate(BaseModel):
    """
    Schema for creating a transfer between two accounts.

    Used when: POST /api/v1/transactions/transfer
    Creates two linked transactions atomically.
    """

    from_account_id: uuid.UUID = Field(..., description="Source account ID")
    to_account_id: uuid.UUID = Field(..., description="Destination account ID")
    amount: Decimal = Field(
        ...,
        gt=0,
        description="Transfer amount (must be positive)",
        examples=[1000.00, 500.50],
    )
    currency: str = Field(..., description="Currency code (must match both accounts)")
    tag: str = Field(
        default="transfer",
        description="Category/tag",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional transfer note",
    )
    transaction_date: date = Field(..., description="Transfer date")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Ensure amount is positive and has at most 2 decimal places."""
        if v <= 0:
            raise ValueError("Transfer amount must be positive")
        if v.as_tuple().exponent < -2:
            raise ValueError("Amount must have at most 2 decimal places")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        v = v.upper()
        valid_currencies = {
            "INR",
            "USD",
            "EUR",
            "GBP",
            "JPY",
            "AUD",
            "CAD",
            "CHF",
            "CNY",
            "SGD",
        }
        if v not in valid_currencies:
            raise ValueError(
                f"Invalid currency code. Must be one of: {', '.join(sorted(valid_currencies))}"
            )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "from_account_id": "123e4567-e89b-12d3-a456-426614174000",
                "to_account_id": "987fcdeb-51a2-43f1-9876-543210fedcba",
                "amount": 1000.00,
                "currency": "INR",
                "tag": "transfer",
                "description": "Transfer to savings",
                "transaction_date": "2024-01-15",
            }
        }
