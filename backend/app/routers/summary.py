"""
Financial summary endpoints.
Derived aggregations from transaction data (ADR-004: No cached summaries in MVP).
"""

from typing import Annotated
from datetime import date, datetime
from decimal import Decimal
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.models.account import Account
from app.models.transaction import Transaction, TransactionType
from app.schemas.summary import MonthlySummary, TagBreakdown

router = APIRouter()


@router.get("/monthly", response_model=MonthlySummary)
def get_monthly_summary(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    year: Annotated[int, Query(ge=2000, le=3000)] = None,
    month: Annotated[int, Query(ge=1, le=12)] = None,
) -> MonthlySummary:
    """
    Get monthly financial summary for the authenticated user.

    Aggregates all transactions across all accounts for a specific month.
    All calculations are derived on-demand from transaction data (ADR-004).

    Authorization:
    - Only includes transactions and accounts belonging to current user

    Calculation Logic:
    1. Opening Balance = Sum of (account opening balances + transactions before month)
    2. Total Income = Sum of positive transactions in month (excluding transfers)
    3. Total Expenses = Sum of negative transactions in month (excluding transfers)
    4. Closing Balance = Opening Balance + Total Income - Total Expenses
    5. Transfers are excluded (they net to zero across accounts)

    Query Parameters:
    - year: Year (defaults to current year)
    - month: Month 1-12 (defaults to current month)

    Args:
        current_user: Injected authenticated user
        db: Database session
        year: Year for summary
        month: Month for summary

    Returns:
        Monthly financial summary with breakdowns

    Example Request:
        GET /api/v1/summary/monthly?year=2024&month=1
        Authorization: Bearer <token>

    Example Response:
        200 OK
        {
            "year": 2024,
            "month": 1,
            "opening_balance": 10000.00,
            "total_income": 50000.00,
            "total_expenses": 35000.00,
            "closing_balance": 25000.00,
            "net_change": 15000.00,
            "income_by_tag": [...],
            "expense_by_tag": [...],
            "income_count": 1,
            "expense_count": 14,
            "transfer_count": 2
        }
    """
    # Default to current month if not specified
    today = date.today()
    if year is None:
        year = today.year
    if month is None:
        month = today.month

    # Validate month/year combination isn't in the future
    summary_date = date(year, month, 1)
    if summary_date > today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot generate summary for future month: {year}-{month}",
        )

    # Calculate date range for the month
    # Start: First day of month (inclusive)
    start_date = date(year, month, 1)

    # End: Last day of month (inclusive)
    if month == 12:
        end_date = date(year, 12, 31)
    else:
        # Last day = day before first day of next month
        next_month = date(year, month + 1, 1)
        end_date = date(next_month.year, next_month.month, next_month.day - 1)
        # Better approach: use last day of current month
        import calendar

        last_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, last_day)

    # === STEP 1: Calculate Opening Balance ===
    # Opening balance = Sum of all account opening balances
    #                 + Sum of all transactions before start_date
    #
    # Example:
    # Account A: opening_balance = ₹5000, created Jan 1
    # Account B: opening_balance = ₹3000, created Jan 1
    # Transactions before Feb 1:
    #   - Jan 5: +₹50000 (salary)
    #   - Jan 10: -₹2000 (groceries)
    #   - Jan 15: -₹1000 (utilities)
    #
    # Opening balance for Feb = 5000 + 3000 + 50000 - 2000 - 1000 = ₹55000

    # Get all accounts for user
    accounts = (
        db.query(Account)
        .filter(Account.user_id == current_user.id)
        .all()
    )

    # Sum of account opening balances (in minor units)
    account_opening_balance_minor = sum(acc.opening_balance_minor for acc in accounts)

    # Sum of all transactions BEFORE the summary month (in minor units)
    transactions_before_month = (
        db.query(func.sum(Transaction.amount_minor))
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_date < start_date,
        )
        .scalar()
    ) or 0

    # Opening balance in minor units
    opening_balance_minor = account_opening_balance_minor + transactions_before_month

    # === STEP 2: Get All Transactions for the Month ===
    # Query all transactions in the date range for current user
    monthly_transactions = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .all()
    )

    # === STEP 3: Categorize and Sum Transactions ===
    # Separate into income, expenses, and transfers
    # Note: Transfers are excluded from income/expense totals (they net to zero)
    #
    # Example transactions:
    # - +₹50000, type=income, tag=salary
    # - -₹5000, type=expense, tag=groceries
    # - -₹1000, type=transfer (debit)
    # - +₹1000, type=transfer (credit)
    #
    # Income = ₹50000
    # Expenses = ₹5000
    # Transfers cancel out

    total_income_minor = 0
    total_expenses_minor = 0
    income_count = 0
    expense_count = 0
    transfer_count = 0

    # Dictionaries to track breakdowns by tag
    # Key: tag name, Value: (total_amount_minor, count)
    income_tags = defaultdict(lambda: {"amount_minor": 0, "count": 0})
    expense_tags = defaultdict(lambda: {"amount_minor": 0, "count": 0})

    for txn in monthly_transactions:
        if txn.transaction_type == TransactionType.TRANSFER:
            transfer_count += 1
            # Transfers don't affect total income/expenses
            # They just move money between accounts
            continue

        elif txn.transaction_type == TransactionType.INCOME or txn.amount_minor > 0:
            # Income: positive amounts
            total_income_minor += txn.amount_minor
            income_count += 1
            income_tags[txn.tag]["amount_minor"] += txn.amount_minor
            income_tags[txn.tag]["count"] += 1

        elif txn.transaction_type == TransactionType.EXPENSE or txn.amount_minor < 0:
            # Expense: negative amounts
            # We store as negative, but will display as positive in breakdown
            total_expenses_minor += abs(txn.amount_minor)
            expense_count += 1
            expense_tags[txn.tag]["amount_minor"] += abs(txn.amount_minor)
            expense_tags[txn.tag]["count"] += 1

    # === STEP 4: Calculate Closing Balance ===
    # Closing balance = Opening balance + All transactions in month
    #
    # Example:
    # Opening: ₹55000
    # Transactions in Feb:
    #   +₹50000 (income)
    #   -₹5000 (expenses)
    #   -₹1000 (transfer debit)
    #   +₹1000 (transfer credit)
    # Closing = 55000 + 50000 - 5000 - 1000 + 1000 = ₹100000

    # Sum ALL transactions in month (including transfers)
    all_transactions_minor = sum(txn.amount_minor for txn in monthly_transactions)
    closing_balance_minor = opening_balance_minor + all_transactions_minor

    # === STEP 5: Convert to Human-Readable Format ===
    # Divide by 100 to convert minor units to major units
    opening_balance = Decimal(opening_balance_minor) / 100
    total_income = Decimal(total_income_minor) / 100
    total_expenses = Decimal(total_expenses_minor) / 100
    closing_balance = Decimal(closing_balance_minor) / 100

    # Net change = income - expenses (transfers excluded)
    net_change = total_income - total_expenses

    # === STEP 6: Build Tag Breakdowns ===
    # Convert tag dictionaries to sorted lists
    income_breakdown = [
        TagBreakdown(
            tag=tag,
            amount=Decimal(data["amount_minor"]) / 100,
            count=data["count"],
        )
        for tag, data in income_tags.items()
    ]
    # Sort by amount descending
    income_breakdown.sort(key=lambda x: x.amount, reverse=True)

    expense_breakdown = [
        TagBreakdown(
            tag=tag,
            amount=Decimal(data["amount_minor"]) / 100,
            count=data["count"],
        )
        for tag, data in expense_tags.items()
    ]
    # Sort by amount descending
    expense_breakdown.sort(key=lambda x: x.amount, reverse=True)

    # === STEP 7: Return Summary ===
    return MonthlySummary(
        year=year,
        month=month,
        opening_balance=opening_balance,
        total_income=total_income,
        total_expenses=total_expenses,
        closing_balance=closing_balance,
        net_change=net_change,
        income_by_tag=income_breakdown,
        expense_by_tag=expense_breakdown,
        income_count=income_count,
        expense_count=expense_count,
        transfer_count=transfer_count,
    )
