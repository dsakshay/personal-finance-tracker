"""
Account schemas for API request/response validation.
Handles conversion between human-readable amounts and minor units.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class AccountCreate(BaseModel):
    """
    Schema for creating a new account.

    Used when: POST /api/v1/accounts
    Amount is in human-readable format (rupees/dollars), converted to minor units internally.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Account name",
        examples=["HDFC Savings", "Cash Wallet"],
    )

    currency: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="ISO 4217 currency code",
        examples=["INR", "USD", "EUR"],
    )

    opening_balance: Decimal = Field(
        default=Decimal("0.00"),
        description="Opening balance in human-readable format (e.g., 1000.50)",
        examples=[1000.50, 0.00, 5000],
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code is uppercase 3-letter code."""
        v = v.upper()
        # Common currency codes (extend as needed)
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

    @field_validator("opening_balance")
    @classmethod
    def validate_opening_balance(cls, v: Decimal) -> Decimal:
        """Ensure opening balance has at most 2 decimal places."""
        if v.as_tuple().exponent < -2:
            raise ValueError("Opening balance must have at most 2 decimal places")
        return v

    def to_minor_units(self) -> int:
        """
        Convert opening_balance to minor units (paise/cents).

        Examples:
        - ₹1000.00 → 100000 paise
        - $50.25 → 5025 cents
        """
        return int(self.opening_balance * 100)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "HDFC Savings Account",
                "currency": "INR",
                "opening_balance": 5000.00,
            }
        }


class AccountRead(BaseModel):
    """
    Schema for reading account data (responses).

    Used when: GET /api/v1/accounts, GET /api/v1/accounts/{id}
    Converts minor units back to human-readable format.
    """

    id: uuid.UUID = Field(..., description="Account unique identifier")
    user_id: uuid.UUID = Field(..., description="Owner user ID")
    name: str = Field(..., description="Account name")
    currency: str = Field(..., description="ISO 4217 currency code")
    opening_balance: Decimal = Field(..., description="Opening balance in human format")
    created_at: datetime = Field(..., description="Account creation timestamp")

    @classmethod
    def from_db_model(cls, account: "Account") -> "AccountRead":
        """
        Create schema from SQLAlchemy model, converting minor units to decimal.

        Args:
            account: SQLAlchemy Account model instance

        Returns:
            AccountRead schema with human-readable amounts
        """
        return cls(
            id=account.id,
            user_id=account.user_id,
            name=account.name,
            currency=account.currency,
            opening_balance=Decimal(account.opening_balance_minor) / 100,
            created_at=account.created_at,
        )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "987fcdeb-51a2-43f1-9876-543210fedcba",
                "name": "HDFC Savings Account",
                "currency": "INR",
                "opening_balance": 5000.00,
                "created_at": "2024-01-15T10:30:00Z",
            }
        }


class AccountWithBalance(AccountRead):
    """
    Extended account schema including calculated current balance.

    Used when: GET /api/v1/accounts (with balance calculation)
    Balance = opening_balance + sum(transactions)
    """

    current_balance: Decimal = Field(
        ..., description="Current balance (opening + all transactions)"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "987fcdeb-51a2-43f1-9876-543210fedcba",
                "name": "HDFC Savings Account",
                "currency": "INR",
                "opening_balance": 5000.00,
                "current_balance": 4200.50,
                "created_at": "2024-01-15T10:30:00Z",
            }
        }
