"""
Schemas for financial summaries and aggregations.
Matches API contract: docs/backend/api-contracts.md
"""

from decimal import Decimal
from typing import Dict

from pydantic import BaseModel, Field


class TagBreakdown(BaseModel):
    """
    Transaction breakdown by tag for a specific category.

    API Contract: docs/backend/api-contracts.md#5-get-summarymonthly
    Used to show how much was spent/earned per category (groceries, salary, etc.)
    """

    tag: str = Field(..., description="Transaction tag/category")
    total: str = Field(..., description="Total amount for this tag (decimal string, signed)")
    count: int = Field(..., description="Number of transactions with this tag")
    currency: str = Field(..., description="Currency code (ISO 4217)")

    class Config:
        json_schema_extra = {
            "example": {
                "tag": "groceries",
                "total": "-5500.00",
                "count": 15,
                "currency": "INR"
            }
        }


class PeriodInfo(BaseModel):
    """Period information for monthly summary."""

    year: int = Field(..., description="Year")
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    month_name: str = Field(..., description="Month name (e.g., 'January')")
    start_date: str = Field(..., description="First day of month (ISO 8601)")
    end_date: str = Field(..., description="Last day of month (ISO 8601)")

    class Config:
        json_schema_extra = {
            "example": {
                "year": 2026,
                "month": 1,
                "month_name": "January",
                "start_date": "2026-01-01",
                "end_date": "2026-01-31"
            }
        }


class SummaryTotals(BaseModel):
    """Summary totals for the period."""

    total_income: str = Field(..., description="Sum of all income (decimal string)")
    total_expenses: str = Field(..., description="Sum of all expenses (decimal string, unsigned)")
    net_savings: str = Field(..., description="Income minus expenses (decimal string)")
    currency: str = Field(..., description="Currency code or 'MIXED'")

    class Config:
        json_schema_extra = {
            "example": {
                "total_income": "50000.00",
                "total_expenses": "18500.50",
                "net_savings": "31499.50",
                "currency": "INR"
            }
        }


class AccountBalance(BaseModel):
    """Account balance for the period."""

    account_id: str = Field(..., description="Account UUID")
    account_name: str = Field(..., description="Account name")
    opening_balance: str = Field(..., description="Balance at start of month (decimal string)")
    closing_balance: str = Field(..., description="Balance at end of month (decimal string)")
    net_change: str = Field(..., description="Change during month (decimal string, signed)")
    currency: str = Field(..., description="Account currency")
    transaction_count: int = Field(..., description="Number of transactions in this month")

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "550e8400-e29b-41d4-a716-446655440000",
                "account_name": "Checking",
                "opening_balance": "5000.00",
                "closing_balance": "36499.50",
                "net_change": "31499.50",
                "currency": "INR",
                "transaction_count": 35
            }
        }


class TopExpense(BaseModel):
    """Top expense transaction."""

    id: str = Field(..., description="Transaction UUID")
    account_name: str = Field(..., description="Account name")
    amount: str = Field(..., description="Amount (negative, signed)")
    currency: str = Field(..., description="Currency code")
    tag: str = Field(..., description="Tag name")
    description: str | None = Field(None, description="Description if provided")
    transaction_date: str = Field(..., description="Transaction date (ISO 8601)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "e5f6a7b8-c9d0-7e1f-2a3b-4c5d6e7f8a9b",
                "account_name": "Checking",
                "amount": "-12000.00",
                "currency": "INR",
                "tag": "rent",
                "description": "January rent payment",
                "transaction_date": "2026-01-05"
            }
        }


class MonthlySummary(BaseModel):
    """
    Monthly financial summary for a user.

    API Contract: docs/backend/api-contracts.md#5-get-summarymonthly
    Aggregates all transactions for a specific month across all accounts.
    All amounts are decimal strings (not minor units, not floats).
    """

    period: PeriodInfo = Field(..., description="Period information")
    summary: SummaryTotals = Field(..., description="Overall totals")
    by_tag: list[TagBreakdown] = Field(..., description="Breakdown by tag (top 10)")
    by_account: list[AccountBalance] = Field(..., description="Breakdown by account")
    top_expenses: list[TopExpense] = Field(..., description="Top 5 expenses by amount")

    class Config:
        json_schema_extra = {
            "example": {
                "period": {
                    "year": 2026,
                    "month": 1,
                    "month_name": "January",
                    "start_date": "2026-01-01",
                    "end_date": "2026-01-31"
                },
                "summary": {
                    "total_income": "50000.00",
                    "total_expenses": "18500.50",
                    "net_savings": "31499.50",
                    "currency": "INR"
                },
                "by_tag": [
                    {"tag": "salary", "total": "50000.00", "count": 1, "currency": "INR"},
                    {"tag": "groceries", "total": "-5500.00", "count": 15, "currency": "INR"}
                ],
                "by_account": [
                    {
                        "account_id": "550e8400-e29b-41d4-a716-446655440000",
                        "account_name": "Checking",
                        "opening_balance": "5000.00",
                        "closing_balance": "36499.50",
                        "net_change": "31499.50",
                        "currency": "INR",
                        "transaction_count": 35
                    }
                ],
                "top_expenses": [
                    {
                        "id": "e5f6a7b8-c9d0-7e1f-2a3b-4c5d6e7f8a9b",
                        "account_name": "Checking",
                        "amount": "-12000.00",
                        "currency": "INR",
                        "tag": "rent",
                        "description": "January rent payment",
                        "transaction_date": "2026-01-05"
                    }
                ]
            }
        }


class AccountSummary(BaseModel):
    """
    Summary for a specific account.

    Shows balance and transaction counts for one account.
    """

    account_id: str = Field(..., description="Account UUID")
    account_name: str = Field(..., description="Account name")
    currency: str = Field(..., description="Account currency")
    opening_balance: Decimal = Field(..., description="Balance at start of period")
    closing_balance: Decimal = Field(..., description="Balance at end of period")
    total_income: Decimal = Field(..., description="Total income")
    total_expenses: Decimal = Field(..., description="Total expenses")
    transaction_count: int = Field(..., description="Number of transactions")

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "123e4567-e89b-12d3-a456-426614174000",
                "account_name": "HDFC Savings",
                "currency": "INR",
                "opening_balance": 5000.00,
                "closing_balance": 8500.00,
                "total_income": 50000.00,
                "total_expenses": 46500.00,
                "transaction_count": 25,
            }
        }
