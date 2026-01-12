"""
Schemas for financial summaries and aggregations.
"""

from decimal import Decimal
from typing import Dict

from pydantic import BaseModel, Field


class TagBreakdown(BaseModel):
    """
    Transaction breakdown by tag for a specific category.

    Used to show how much was spent/earned per category (groceries, salary, etc.)
    """

    tag: str = Field(..., description="Transaction tag/category")
    amount: Decimal = Field(..., description="Total amount for this tag")
    count: int = Field(..., description="Number of transactions with this tag")

    class Config:
        json_schema_extra = {
            "example": {
                "tag": "groceries",
                "amount": -1250.50,
                "count": 5,
            }
        }


class MonthlySummary(BaseModel):
    """
    Monthly financial summary for a user.

    Aggregates all transactions for a specific month across all accounts.
    All amounts are in human-readable format (rupees/dollars, not minor units).
    """

    year: int = Field(..., description="Year of summary", examples=[2024])
    month: int = Field(..., ge=1, le=12, description="Month (1-12)", examples=[1])

    # Opening balance: Sum of all account balances at start of month
    opening_balance: Decimal = Field(
        ...,
        description="Total balance across all accounts at start of month",
    )

    # Income: Sum of all positive transactions
    total_income: Decimal = Field(
        ...,
        description="Total income for the month (positive transactions)",
    )

    # Expenses: Sum of all negative transactions
    total_expenses: Decimal = Field(
        ...,
        description="Total expenses for the month (negative transactions, shown as positive)",
    )

    # Transfers are netted out (don't affect total balance)
    # Closing balance: opening + income - expenses
    closing_balance: Decimal = Field(
        ...,
        description="Total balance across all accounts at end of month",
    )

    # Net change for the month
    net_change: Decimal = Field(
        ...,
        description="Net change (income - expenses)",
    )

    # Breakdown by transaction tags
    income_by_tag: list[TagBreakdown] = Field(
        ...,
        description="Income breakdown by category/tag",
    )

    expense_by_tag: list[TagBreakdown] = Field(
        ...,
        description="Expense breakdown by category/tag",
    )

    # Transaction counts
    income_count: int = Field(..., description="Number of income transactions")
    expense_count: int = Field(..., description="Number of expense transactions")
    transfer_count: int = Field(..., description="Number of transfer transactions")

    class Config:
        json_schema_extra = {
            "example": {
                "year": 2024,
                "month": 1,
                "opening_balance": 10000.00,
                "total_income": 50000.00,
                "total_expenses": 35000.00,
                "closing_balance": 25000.00,
                "net_change": 15000.00,
                "income_by_tag": [
                    {"tag": "salary", "amount": 50000.00, "count": 1},
                ],
                "expense_by_tag": [
                    {"tag": "groceries", "amount": 5000.00, "count": 8},
                    {"tag": "rent", "amount": 20000.00, "count": 1},
                    {"tag": "utilities", "amount": 10000.00, "count": 5},
                ],
                "income_count": 1,
                "expense_count": 14,
                "transfer_count": 2,
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
