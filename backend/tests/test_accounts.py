"""
Account management tests.

Critical for finance correctness:
- Validates currency consistency
- Ensures opening balance is stored correctly
- Prevents unauthorized account access
- Tests decimal string amount handling
"""

import pytest
from fastapi import status
from decimal import Decimal


def test_create_account_success(authenticated_client):
    """
    Test: Create account with valid data.

    Why critical:
    - Validates account creation flow
    - Ensures opening balance is converted to minor units correctly
    - Confirms amounts are returned as decimal strings
    """
    response = authenticated_client.post(
        "/api/v1/accounts",
        json={
            "name": "Savings Account",
            "currency": "INR",
            "opening_balance": "50000.00",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    assert data["name"] == "Savings Account"
    assert data["currency"] == "INR"
    assert data["opening_balance"] == "50000.00"
    assert data["current_balance"] == "50000.00"  # No transactions yet
    assert "id" in data
    assert "created_at" in data


def test_create_account_with_negative_opening_balance(authenticated_client):
    """
    Test: Can create account with negative opening balance (e.g., credit card).

    Why critical:
    - Credit cards and loans start with negative balance
    - Validates signed decimal string handling
    """
    response = authenticated_client.post(
        "/api/v1/accounts",
        json={
            "name": "Credit Card",
            "currency": "USD",
            "opening_balance": "-1000.00",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["opening_balance"] == "-1000.00"
    assert data["current_balance"] == "-1000.00"


def test_create_account_invalid_currency_format(authenticated_client):
    """
    Test: Invalid currency code is rejected.

    Why critical:
    - Prevents invalid currency codes (must be ISO 4217)
    - Ensures 3-letter uppercase format
    """
    response = authenticated_client.post(
        "/api/v1/accounts",
        json={
            "name": "Test Account",
            "currency": "rupees",  # Invalid: not 3-letter code
            "opening_balance": "1000.00",
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_account_invalid_amount_format(authenticated_client):
    """
    Test: Invalid amount format is rejected.

    Why critical:
    - Amounts must have exactly 2 decimal places
    - Prevents precision errors
    - Validates Pydantic pattern matching
    """
    response = authenticated_client.post(
        "/api/v1/accounts",
        json={
            "name": "Test Account",
            "currency": "USD",
            "opening_balance": "1000.5",  # Invalid: only 1 decimal place
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_list_accounts_returns_only_user_accounts(authenticated_client, client):
    """
    Test: Users can only see their own accounts.

    Why critical:
    - Prevents data leakage between users
    - Validates authorization filter (user_id check)
    - Security: multi-user isolation
    """
    # Create account for authenticated user
    authenticated_client.post(
        "/api/v1/accounts",
        json={
            "name": "My Account",
            "currency": "INR",
            "opening_balance": "1000.00",
        },
    )

    # Create another user and their account
    client.post(
        "/api/v1/auth/signup",
        json={"email": "other@example.com", "password": "Password123!"},
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "other@example.com", "password": "Password123!"},
    )
    other_token = login_response.json()["access_token"]

    client.post(
        "/api/v1/accounts",
        json={
            "name": "Other User Account",
            "currency": "USD",
            "opening_balance": "5000.00",
        },
        headers={"Authorization": f"Bearer {other_token}"},
    )

    # First user should only see their account
    response = authenticated_client.get("/api/v1/accounts")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_count"] == 1
    assert data["accounts"][0]["name"] == "My Account"


def test_list_accounts_filter_by_currency(authenticated_client):
    """
    Test: Filter accounts by currency.

    Why critical:
    - Useful for multi-currency portfolios
    - Validates query parameter handling
    """
    # Create accounts in different currencies
    authenticated_client.post(
        "/api/v1/accounts",
        json={"name": "INR Account", "currency": "INR", "opening_balance": "1000.00"},
    )
    authenticated_client.post(
        "/api/v1/accounts",
        json={"name": "USD Account", "currency": "USD", "opening_balance": "100.00"},
    )

    # Filter by INR
    response = authenticated_client.get("/api/v1/accounts?currency=INR")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_count"] == 1
    assert data["accounts"][0]["currency"] == "INR"


def test_account_current_balance_reflects_transactions(authenticated_client, db_session):
    """
    Test: Current balance = opening balance + sum of transactions.

    Why critical:
    - Core finance logic validation
    - Ensures balance calculation is correct
    - Tests aggregation query
    """
    # Create account
    account_response = authenticated_client.post(
        "/api/v1/accounts",
        json={
            "name": "Test Account",
            "currency": "INR",
            "opening_balance": "1000.00",
        },
    )
    account_id = account_response.json()["id"]

    # Add income transaction (+500)
    authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": account_id,
            "amount": "500.00",
            "currency": "INR",
            "transaction_type": "income",
            "tag": "salary",
            "transaction_date": "2026-01-10",
        },
    )

    # Add expense transaction (-200)
    authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": account_id,
            "amount": "200.00",
            "currency": "INR",
            "transaction_type": "expense",
            "tag": "food",
            "transaction_date": "2026-01-11",
        },
    )

    # Get accounts and verify balance
    response = authenticated_client.get("/api/v1/accounts")
    data = response.json()

    account = data["accounts"][0]
    # 1000.00 (opening) + 500.00 (income) - 200.00 (expense) = 1300.00
    assert account["current_balance"] == "1300.00"
    assert account["opening_balance"] == "1000.00"


def test_create_account_without_auth_fails(client):
    """
    Test: Cannot create account without authentication.

    Why critical:
    - Ensures authentication is enforced
    - All accounts must belong to a user
    """
    response = client.post(
        "/api/v1/accounts",
        json={
            "name": "Unauthorized Account",
            "currency": "USD",
            "opening_balance": "1000.00",
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
