"""
Financial summary endpoints.
Derived aggregations from transaction data (ADR-004: No cached summaries in MVP).
"""

from typing import Annotated
from datetime import date, datetime
from decimal import Decimal
from collections import defaultdict
import calendar
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.models.account import Account
from app.models.transaction import Transaction, TransactionType
from app.schemas.summary import (
    MonthlySummary,
    PeriodInfo,
    SummaryTotals,
    TagBreakdown,
    AccountBalance,
    TopExpense,
)

router = APIRouter()


@router.get("/monthly", response_model=MonthlySummary)
def get_monthly_summary(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    year: Annotated[int, Query(ge=2000, le=3000)],
    month: Annotated[int, Query(ge=1, le=12)],
    currency: str | None = Query(None, description="Filter by currency (ISO 4217)"),
) -> MonthlySummary:
    """
    Get monthly financial summary for the authenticated user.

    API Contract: docs/backend/api-contracts.md#5-get-summarymonthly

    Aggregation Logic:
    1. Opening Balance = Sum of (account opening balances + transactions before month start)
    2. Total Income = Sum of income transactions in month (excludes transfers)
    3. Total Expenses = Sum of expense transactions in month (excludes transfers)
    4. Closing Balance = Opening Balance + All transactions in month (includes transfers)
    5. Net Savings = Total Income - Total Expenses
    6. Transfers are excluded from income/expenses (they net to zero)

    Authorization:
    - Only includes transactions and accounts belonging to current user
    - Multi-user isolation enforced

    Query Parameters:
    - year: Year (2000-3000) - REQUIRED
    - month: Month 1-12 - REQUIRED
    - currency: Optional currency filter (e.g., "INR", "USD")

    Args:
        current_user: Injected authenticated user
        db: Database session
        year: Year for summary
        month: Month for summary
        currency: Optional currency filter

    Returns:
        Monthly financial summary with period info, totals, tag breakdown,
        account breakdown, and top expenses

    Raises:
        400: Invalid date or future month

    Example Request:
        GET /api/v1/summary/monthly?year=2026&month=1&currency=INR
        Authorization: Bearer <token>

    Example Response:
        200 OK
        {
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
            "by_tag": [...],
            "by_account": [...],
            "top_expenses": [...]
        }
    """
    # === STEP 1: Validate and Calculate Date Range ===

    # Validate month/year combination isn't in the future
    today = date.today()
    try:
        summary_date = date(year, month, 1)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date: year={year}, month={month}",
        )

    if summary_date > today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot generate summary for future month: {year}-{month:02d}",
        )

    # Calculate date range for the month
    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    # Month name for display
    month_name = calendar.month_name[month]

    # === STEP 2: Get All User Accounts ===

    # Build account query
    account_query = db.query(Account).filter(Account.user_id == current_user.id)

    # Optional currency filter
    if currency:
        account_query = account_query.filter(Account.currency == currency.upper())

    accounts = account_query.all()

    if not accounts:
        # No accounts (or no accounts matching currency filter)
        # Return empty summary
        return MonthlySummary(
            period=PeriodInfo(
                year=year,
                month=month,
                month_name=month_name,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            ),
            summary=SummaryTotals(
                total_income="0.00",
                total_expenses="0.00",
                net_savings="0.00",
                currency=currency.upper() if currency else "MIXED",
            ),
            by_tag=[],
            by_account=[],
            top_expenses=[],
        )

    # === STEP 3: Calculate Opening Balances ===

    # Opening balance = Sum of account opening balances + transactions before month
    #
    # Example:
    # Account A: opening_balance_minor = 500000 (₹5,000)
    # Account B: opening_balance_minor = 300000 (₹3,000)
    # Total account opening: ₹8,000
    #
    # Transactions before Feb 1, 2026:
    # - Jan 5: +₹50,000 (salary)
    # - Jan 10: -₹2,000 (groceries)
    # - Jan 15: -₹1,000 (utilities)
    # Sum: +₹47,000
    #
    # Opening balance for Feb 2026: ₹8,000 + ₹47,000 = ₹55,000

    # Map: account_id → opening_balance_minor (for this period)
    account_opening_balances: dict[uuid.UUID, int] = {}

    for account in accounts:
        # Start with account's original opening balance
        opening_minor = account.opening_balance_minor

        # Add all transactions BEFORE the summary period
        transactions_before = (
            db.query(func.sum(Transaction.amount_minor))
            .filter(
                Transaction.account_id == account.id,
                Transaction.transaction_date < start_date,
            )
            .scalar()
        ) or 0

        account_opening_balances[account.id] = opening_minor + transactions_before

    # === STEP 4: Get All Transactions for the Month ===

    # Build transaction query
    txn_query = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
    )

    # Optional currency filter
    if currency:
        txn_query = txn_query.filter(Transaction.currency == currency.upper())

    monthly_transactions = txn_query.all()

    # === STEP 5: Aggregate Transactions by Type and Tag ===

    total_income_minor = 0
    total_expenses_minor = 0

    # Map: tag → {amount_minor, count, currency}
    tag_aggregates: dict[str, dict] = defaultdict(
        lambda: {"amount_minor": 0, "count": 0, "currency": set()}
    )

    # Map: account_id → {transaction_sum_minor, count}
    account_txn_aggregates: dict[uuid.UUID, dict] = defaultdict(
        lambda: {"sum_minor": 0, "count": 0}
    )

    # List of expense transactions (for top expenses)
    expense_transactions = []

    for txn in monthly_transactions:
        # Track per-account aggregates
        account_txn_aggregates[txn.account_id]["sum_minor"] += txn.amount_minor
        account_txn_aggregates[txn.account_id]["count"] += 1

        # Skip transfers for income/expense totals
        if txn.transaction_type == TransactionType.TRANSFER:
            continue

        # Track by tag
        tag_aggregates[txn.tag]["amount_minor"] += txn.amount_minor
        tag_aggregates[txn.tag]["count"] += 1
        tag_aggregates[txn.tag]["currency"].add(txn.currency)

        # Categorize as income or expense
        if txn.transaction_type == TransactionType.INCOME or txn.amount_minor > 0:
            total_income_minor += txn.amount_minor

        elif txn.transaction_type == TransactionType.EXPENSE or txn.amount_minor < 0:
            total_expenses_minor += abs(txn.amount_minor)
            expense_transactions.append(txn)

    # === STEP 6: Build Tag Breakdown ===

    tag_breakdown = []
    for tag, data in tag_aggregates.items():
        # Determine currency (single or MIXED)
        currencies = data["currency"]
        tag_currency = list(currencies)[0] if len(currencies) == 1 else "MIXED"

        # Convert to decimal string
        amount_decimal = Decimal(data["amount_minor"]) / 100

        tag_breakdown.append(
            TagBreakdown(
                tag=tag,
                total=f"{amount_decimal:.2f}",
                count=data["count"],
                currency=tag_currency,
            )
        )

    # Sort by absolute amount descending, limit to top 10
    tag_breakdown.sort(key=lambda x: abs(Decimal(x.total)), reverse=True)
    tag_breakdown = tag_breakdown[:10]

    # === STEP 7: Build Account Breakdown ===

    account_breakdown = []
    for account in accounts:
        opening_balance_minor = account_opening_balances.get(account.id, 0)
        txn_sum_minor = account_txn_aggregates[account.id]["sum_minor"]
        txn_count = account_txn_aggregates[account.id]["count"]

        closing_balance_minor = opening_balance_minor + txn_sum_minor
        net_change_minor = txn_sum_minor

        # Convert to decimal strings
        opening_decimal = Decimal(opening_balance_minor) / 100
        closing_decimal = Decimal(closing_balance_minor) / 100
        net_change_decimal = Decimal(net_change_minor) / 100

        account_breakdown.append(
            AccountBalance(
                account_id=str(account.id),
                account_name=account.name,
                opening_balance=f"{opening_decimal:.2f}",
                closing_balance=f"{closing_decimal:.2f}",
                net_change=f"{net_change_decimal:.2f}",
                currency=account.currency,
                transaction_count=txn_count,
            )
        )

    # === STEP 8: Build Top Expenses ===

    # Sort by amount (most negative first)
    expense_transactions.sort(key=lambda t: t.amount_minor)

    top_expenses = []
    for txn in expense_transactions[:5]:
        # Find account name
        account = next((a for a in accounts if a.id == txn.account_id), None)
        account_name = account.name if account else "Unknown"

        # Convert amount
        amount_decimal = Decimal(txn.amount_minor) / 100

        top_expenses.append(
            TopExpense(
                id=str(txn.id),
                account_name=account_name,
                amount=f"{amount_decimal:.2f}",
                currency=txn.currency,
                tag=txn.tag,
                description=txn.description,
                transaction_date=txn.transaction_date.isoformat(),
            )
        )

    # === STEP 9: Build Summary Totals ===

    # Convert to decimal strings
    total_income_decimal = Decimal(total_income_minor) / 100
    total_expenses_decimal = Decimal(total_expenses_minor) / 100
    net_savings_decimal = total_income_decimal - total_expenses_decimal

    # Determine currency
    currencies = set(account.currency for account in accounts)
    summary_currency = list(currencies)[0] if len(currencies) == 1 else "MIXED"

    # === STEP 10: Build Period Info ===

    period = PeriodInfo(
        year=year,
        month=month,
        month_name=month_name,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
    )

    summary = SummaryTotals(
        total_income=f"{total_income_decimal:.2f}",
        total_expenses=f"{total_expenses_decimal:.2f}",
        net_savings=f"{net_savings_decimal:.2f}",
        currency=summary_currency,
    )

    # === STEP 11: Return Complete Summary ===

    return MonthlySummary(
        period=period,
        summary=summary,
        by_tag=tag_breakdown,
        by_account=account_breakdown,
        top_expenses=top_expenses,
    )
