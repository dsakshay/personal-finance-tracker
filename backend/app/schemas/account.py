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
    Schema for creating a new account (POST /accounts).

    API Contract: docs/backend/api-contracts.md
    Accepts human-readable amounts, converts to minor units for DB storage.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Account display name",
        examples=["HDFC Savings", "Cash Wallet", "Emergency Fund"],
    )

    currency: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="ISO 4217 currency code (3 uppercase letters)",
        examples=["INR", "USD", "EUR"],
    )

    opening_balance: str = Field(
        default="0.00",
        description="Opening balance in decimal format (e.g., '1000.50')",
        examples=["0.00", "5000.00", "10000.50"],
        pattern=r"^-?\d+\.\d{2}$",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty or only whitespace."""
        if not v or v.strip() == "":
            raise ValueError("Account name cannot be empty or only whitespace")
        return v.strip()

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """
        Validate currency code format and value.

        Requirements:
        - Exactly 3 uppercase letters
        - Must be in supported currencies list
        """
        v = v.upper()

        if len(v) != 3:
            raise ValueError("Currency code must be exactly 3 characters")

        if not v.isalpha():
            raise ValueError("Currency code must contain only letters")

        # Supported currency codes (ISO 4217)
        valid_currencies = {
            "INR",  # Indian Rupee
            "USD",  # US Dollar
            "EUR",  # Euro
            "GBP",  # British Pound
            "JPY",  # Japanese Yen
            "AUD",  # Australian Dollar
            "CAD",  # Canadian Dollar
            "CHF",  # Swiss Franc
            "CNY",  # Chinese Yuan
            "SGD",  # Singapore Dollar
        }

        if v not in valid_currencies:
            raise ValueError(
                f"Unsupported currency '{v}'. Supported: {', '.join(sorted(valid_currencies))}"
            )

        return v

    @field_validator("opening_balance")
    @classmethod
    def validate_opening_balance(cls, v: str) -> str:
        """
        Validate opening balance format.

        Requirements:
        - Valid decimal string with exactly 2 decimal places
        - Format: [-]?[0-9]+\.[0-9]{2}
        - Max: ±9999999999.99 (10 billion limit)
        """
        # Convert to Decimal for validation
        try:
            decimal_value = Decimal(v)
        except Exception:
            raise ValueError("Opening balance must be a valid decimal string")

        # Check decimal places
        if decimal_value.as_tuple().exponent != -2:
            raise ValueError("Opening balance must have exactly 2 decimal places (e.g., '100.00')")

        # Check range
        max_value = Decimal("9999999999.99")
        min_value = Decimal("-9999999999.99")

        if decimal_value > max_value or decimal_value < min_value:
            raise ValueError("Opening balance must be between -9999999999.99 and 9999999999.99")

        return v

    def to_minor_units(self) -> int:
        """
        Convert opening_balance to minor units (paise/cents).

        Examples:
        - "1000.00" → 100000 paise
        - "50.25" → 5025 cents
        - "-250.50" → -25050 paise
        """
        decimal_value = Decimal(self.opening_balance)
        return int(decimal_value * 100)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Emergency Fund",
                "currency": "INR",
                "opening_balance": "50000.00",
            }
        }


class AccountResponse(BaseModel):
    """
    Schema for account responses (POST /accounts, GET /accounts).

    API Contract: docs/backend/api-contracts.md
    Returns human-readable amounts (decimal strings with 2 places).
    """

    id: uuid.UUID = Field(..., description="Account unique identifier")
    name: str = Field(..., description="Account display name")
    currency: str = Field(..., description="ISO 4217 currency code")
    opening_balance: str = Field(..., description="Opening balance (decimal string)")
    current_balance: str = Field(..., description="Current balance including transactions")
    created_at: datetime = Field(..., description="Account creation timestamp (UTC)")

    @classmethod
    def from_db_model(cls, account: "Account", current_balance_minor: int | None = None) -> "AccountResponse":
        """
        Create response schema from SQLAlchemy model.

        Converts minor units to human-readable decimal strings.

        Args:
            account: SQLAlchemy Account model instance
            current_balance_minor: Current balance in minor units (if None, uses opening balance)

        Returns:
            AccountResponse with decimal string amounts
        """
        # Use provided current balance or default to opening balance
        if current_balance_minor is None:
            current_balance_minor = account.opening_balance_minor

        # Convert minor units to decimal strings
        opening_decimal = Decimal(account.opening_balance_minor) / 100
        current_decimal = Decimal(current_balance_minor) / 100

        return cls(
            id=account.id,
            name=account.name,
            currency=account.currency,
            opening_balance=f"{opening_decimal:.2f}",
            current_balance=f"{current_decimal:.2f}",
            created_at=account.created_at,
        )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Emergency Fund",
                "currency": "INR",
                "opening_balance": "50000.00",
                "current_balance": "48200.50",
                "created_at": "2026-01-12T10:30:00Z",
            }
        }


class AccountListResponse(BaseModel):
    """
    Schema for GET /accounts response.

    API Contract: docs/backend/api-contracts.md
    """

    accounts: list[AccountResponse] = Field(..., description="List of user's accounts")
    total_count: int = Field(..., description="Total number of accounts")

    class Config:
        json_schema_extra = {
            "example": {
                "accounts": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Emergency Fund",
                        "currency": "INR",
                        "opening_balance": "50000.00",
                        "current_balance": "48200.50",
                        "created_at": "2026-01-12T10:30:00Z",
                    },
                    {
                        "id": "660e8400-e29b-41d4-a716-446655440111",
                        "name": "Checking",
                        "currency": "INR",
                        "opening_balance": "5000.00",
                        "current_balance": "7850.25",
                        "created_at": "2026-01-01T08:00:00Z",
                    },
                ],
                "total_count": 2,
            }
        }
