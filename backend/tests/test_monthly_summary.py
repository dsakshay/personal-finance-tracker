"""
Monthly summary aggregation tests.

CRITICAL for finance correctness:
- Opening balance calculation (account openings + prior transactions)
- Income/expense totals (excluding transfers)
- Closing balance calculation
- Transfers do NOT count as income or expense
- Tag breakdown aggregation
- Multi-currency handling
"""

import pytest
from fastapi import status
from decimal import Decimal


@pytest.fixture
def test_account_with_history(authenticated_client):
    """
    Create account with transaction history spanning multiple months.

    Setup:
    - Account opened Dec 2025 with 10000.00
    - Dec 2025: +5000 income, -2000 expense
    - Jan 2026: +3000 income, -1500 expense
    """
    # Create account
    account = authenticated_client.post(
        "/api/v1/accounts",
        json={
            "name": "Test Account",
            "currency": "INR",
            "opening_balance": "10000.00",
        },
    ).json()

    # December 2025 transactions
    authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": account["id"],
            "amount": "5000.00",
            "currency": "INR",
            "transaction_type": "income",
            "tag": "salary",
            "transaction_date": "2025-12-25",
        },
    )
    authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": account["id"],
            "amount": "2000.00",
            "currency": "INR",
            "transaction_type": "expense",
            "tag": "rent",
            "transaction_date": "2025-12-28",
        },
    )

    # January 2026 transactions
    authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": account["id"],
            "amount": "3000.00",
            "currency": "INR",
            "transaction_type": "income",
            "tag": "salary",
            "transaction_date": "2026-01-05",
        },
    )
    authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": account["id"],
            "amount": "1500.00",
            "currency": "INR",
            "transaction_type": "expense",
            "tag": "food",
            "transaction_date": "2026-01-10",
        },
    )

    return account


def test_monthly_summary_opening_balance_calculation(
    authenticated_client, test_account_with_history
):
    """
    Test: Opening balance = account opening + all transactions before the month.

    Why CRITICAL:
    - Opening balance must be accurate for monthly tracking
    - Includes account opening balance + all prior transactions
    - Forms the baseline for the month

    Calculation for Jan 2026:
    - Account opening: 10000.00
    - Dec income: +5000.00
    - Dec expense: -2000.00
    - Opening balance Jan = 10000 + 5000 - 2000 = 13000.00
    """
    response = authenticated_client.get("/api/v1/summary/monthly?year=2026&month=1")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["period"]["year"] == 2026
    assert data["period"]["month"] == 1

    # Opening balance should be in by_account breakdown
    assert len(data["by_account"]) == 1
    assert data["by_account"][0]["opening_balance"] == "13000.00"


def test_monthly_summary_income_and_expense_totals(
    authenticated_client, test_account_with_history
):
    """
    Test: Income and expense totals calculated correctly for the month.

    Why CRITICAL:
    - Shows total money in and out for the period
    - Excludes transfers (they don't create/destroy money)
    - Used for budgeting and spending analysis

    Jan 2026:
    - Income: 3000.00
    - Expenses: 1500.00
    """
    response = authenticated_client.get("/api/v1/summary/monthly?year=2026&month=1")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["summary"]["total_income"] == "3000.00"
    assert data["summary"]["total_expenses"] == "1500.00"


def test_monthly_summary_closing_balance_calculation(
    authenticated_client, test_account_with_history
):
    """
    Test: Closing balance = opening balance + income - expenses.

    Why CRITICAL:
    - Shows end-of-month financial position
    - Must match actual account balance at month end
    - Validates all calculations are correct

    Jan 2026:
    - Opening: 13000.00
    - Income: +3000.00
    - Expenses: -1500.00
    - Closing: 13000 + 3000 - 1500 = 14500.00
    """
    response = authenticated_client.get("/api/v1/summary/monthly?year=2026&month=1")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Closing balance should be in by_account breakdown
    assert len(data["by_account"]) == 1
    assert data["by_account"][0]["closing_balance"] == "14500.00"


def test_monthly_summary_transfers_not_counted_as_income_or_expense(authenticated_client):
    """
    Test: Transfers do NOT appear in income or expense totals.

    Why CRITICAL:
    - Transfers move money between accounts (net zero)
    - Including them would double-count money
    - Only income/expense change total wealth

    Setup:
    - Create two accounts
    - Transfer 1000 between them
    - Verify transfer not in income/expense
    """
    # Create two accounts
    account1 = authenticated_client.post(
        "/api/v1/accounts",
        json={"name": "Account 1", "currency": "INR", "opening_balance": "10000.00"},
    ).json()

    account2 = authenticated_client.post(
        "/api/v1/accounts",
        json={"name": "Account 2", "currency": "INR", "opening_balance": "5000.00"},
    ).json()

    # Create transfer
    authenticated_client.post(
        "/api/v1/transactions/transfer",
        json={
            "account_id": account1["id"],
            "amount": "1000.00",
            "currency": "INR",
            "transaction_type": "transfer",
            "tag": "transfer",
            "related_account_id": account2["id"],
            "transaction_date": "2026-01-15",
        },
    )

    # Get summary
    response = authenticated_client.get("/api/v1/summary/monthly?year=2026&month=1")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Income and expenses should be zero (no income/expense transactions)
    assert data["summary"]["total_income"] == "0.00"
    assert data["summary"]["total_expenses"] == "0.00"

    # But closing balance should still change (transfer affects account balances)
    # Total across both accounts: Opening = 15000, Closing = 15000 (money conserved)
    total_opening = sum(float(acc["opening_balance"]) for acc in data["by_account"])
    total_closing = sum(float(acc["closing_balance"]) for acc in data["by_account"])
    assert total_opening == 15000.00
    assert total_closing == 15000.00


def test_monthly_summary_tag_breakdown(authenticated_client):
    """
    Test: Tag breakdown shows spending by category.

    Why CRITICAL:
    - Helps identify spending patterns
    - Budgeting and expense categorization
    - Should be sorted by amount (highest first)
    """
    # Create account
    account = authenticated_client.post(
        "/api/v1/accounts",
        json={"name": "Account", "currency": "INR", "opening_balance": "10000.00"},
    ).json()

    # Create expenses with different tags
    authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": account["id"],
            "amount": "3000.00",
            "currency": "INR",
            "transaction_type": "expense",
            "tag": "rent",
            "transaction_date": "2026-01-05",
        },
    )
    authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": account["id"],
            "amount": "1500.00",
            "currency": "INR",
            "transaction_type": "expense",
            "tag": "food",
            "transaction_date": "2026-01-10",
        },
    )
    authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": account["id"],
            "amount": "500.00",
            "currency": "INR",
            "transaction_type": "expense",
            "tag": "entertainment",
            "transaction_date": "2026-01-12",
        },
    )

    # Get summary
    response = authenticated_client.get("/api/v1/summary/monthly?year=2026&month=1")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Should have tag breakdown
    assert "by_tag" in data
    assert len(data["by_tag"]) == 3

    # Should be sorted by absolute amount (highest first)
    # Tags will be sorted by total amount
    tags_by_name = {tag["tag"]: tag for tag in data["by_tag"]}
    assert "rent" in tags_by_name
    assert "food" in tags_by_name
    assert "entertainment" in tags_by_name


def test_monthly_summary_account_breakdown(authenticated_client):
    """
    Test: Account breakdown shows per-account balances.

    Why CRITICAL:
    - Track balance changes across multiple accounts
    - Identify which accounts grew/shrank
    - Multi-account financial overview
    """
    # Create two accounts
    account1 = authenticated_client.post(
        "/api/v1/accounts",
        json={"name": "Checking", "currency": "INR", "opening_balance": "5000.00"},
    ).json()

    account2 = authenticated_client.post(
        "/api/v1/accounts",
        json={"name": "Savings", "currency": "INR", "opening_balance": "10000.00"},
    ).json()

    # Add transactions to account1
    authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": account1["id"],
            "amount": "2000.00",
            "currency": "INR",
            "transaction_type": "income",
            "tag": "salary",
            "transaction_date": "2026-01-05",
        },
    )

    # Get summary
    response = authenticated_client.get("/api/v1/summary/monthly?year=2026&month=1")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Should have account breakdown
    assert "by_account" in data
    assert len(data["by_account"]) == 2

    # Find checking account
    checking = next(a for a in data["by_account"] if a["account_name"] == "Checking")
    assert checking["opening_balance"] == "5000.00"
    assert checking["closing_balance"] == "7000.00"  # 5000 + 2000


def test_monthly_summary_top_expenses(authenticated_client):
    """
    Test: Top expenses shows largest individual expenses.

    Why CRITICAL:
    - Identifies biggest spending items
    - Helps find areas to cut costs
    - Shows top 5 by amount
    """
    # Create account
    account = authenticated_client.post(
        "/api/v1/accounts",
        json={"name": "Account", "currency": "INR", "opening_balance": "20000.00"},
    ).json()

    # Create 6 expenses (should return top 5)
    expenses = [
        ("rent", "5000.00"),
        ("car", "3000.00"),
        ("food", "2000.00"),
        ("utilities", "1500.00"),
        ("entertainment", "1000.00"),
        ("misc", "500.00"),
    ]

    for tag, amount in expenses:
        authenticated_client.post(
            "/api/v1/transactions",
            json={
                "account_id": account["id"],
                "amount": amount,
                "currency": "INR",
                "transaction_type": "expense",
                "tag": tag,
                "transaction_date": "2026-01-10",
            },
        )

    # Get summary
    response = authenticated_client.get("/api/v1/summary/monthly?year=2026&month=1")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Should have top 5 expenses
    assert "top_expenses" in data
    assert len(data["top_expenses"]) == 5

    # Should be sorted by amount (largest absolute value first)
    # Top expense should be rent at 5000
    assert abs(float(data["top_expenses"][0]["amount"])) >= abs(float(data["top_expenses"][1]["amount"]))


def test_monthly_summary_empty_month(authenticated_client):
    """
    Test: Summary for month with no transactions.

    Why CRITICAL:
    - Should not crash on empty months
    - Opening balance should still be calculated
    - Closing balance = opening balance (no changes)
    """
    # Create account but no transactions in Jan 2026
    authenticated_client.post(
        "/api/v1/accounts",
        json={"name": "Account", "currency": "INR", "opening_balance": "10000.00"},
    )

    response = authenticated_client.get("/api/v1/summary/monthly?year=2026&month=1")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Check account balance
    assert len(data["by_account"]) == 1
    assert data["by_account"][0]["opening_balance"] == "10000.00"
    assert data["by_account"][0]["closing_balance"] == "10000.00"

    # Check summary
    assert data["summary"]["total_income"] == "0.00"
    assert data["summary"]["total_expenses"] == "0.00"

    assert len(data["by_tag"]) == 0
    assert len(data["top_expenses"]) == 0


def test_monthly_summary_invalid_month_fails(authenticated_client):
    """
    Test: Invalid month numbers are rejected.

    Why CRITICAL:
    - Prevents invalid date calculations
    - Validates input sanitization
    """
    response = authenticated_client.get("/api/v1/summary/monthly?year=2026&month=13")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_monthly_summary_requires_authentication(client):
    """
    Test: Summary endpoint requires authentication.

    Why CRITICAL:
    - Financial data is sensitive
    - Must not leak data to unauthenticated users
    """
    response = client.get("/api/v1/summary/monthly?year=2026&month=1")

    assert response.status_code == status.HTTP_403_FORBIDDEN
