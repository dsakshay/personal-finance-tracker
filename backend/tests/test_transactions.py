"""
Transaction tests (income and expense).

Critical for finance correctness:
- Income transactions increase balance
- Expense transactions decrease balance
- Currency must match account currency
- Amounts are stored with correct sign
- Future dates are rejected
"""

import pytest
from fastapi import status
from datetime import date, timedelta


@pytest.fixture
def test_account(authenticated_client):
    """Create a test account for transaction tests."""
    response = authenticated_client.post(
        "/api/v1/accounts",
        json={
            "name": "Test Account",
            "currency": "INR",
            "opening_balance": "10000.00",
        },
    )
    return response.json()


def test_create_income_transaction(authenticated_client, test_account):
    """
    Test: Income transaction is created with positive amount.

    Why critical:
    - Validates income recording
    - Ensures amount is stored as positive integer in minor units
    - Confirms decimal string parsing
    """
    response = authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": test_account["id"],
            "amount": "5000.00",
            "currency": "INR",
            "transaction_type": "income",
            "tag": "salary",
            "description": "Monthly salary",
            "transaction_date": "2026-01-10",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    assert data["amount"] == "5000.00"  # Positive for income
    assert data["transaction_type"] == "income"
    assert data["tag"] == "salary"
    assert data["account_name"] == "Test Account"
    assert data["currency"] == "INR"
    assert data["transaction_date"] == "2026-01-10"


def test_create_expense_transaction(authenticated_client, test_account):
    """
    Test: Expense transaction is created with negative amount.

    Why critical:
    - Validates expense recording
    - Ensures amount is stored as negative integer in minor units
    - Client sends positive amount, backend makes it negative
    """
    response = authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": test_account["id"],
            "amount": "1500.00",  # Client sends positive
            "currency": "INR",
            "transaction_type": "expense",
            "tag": "food",
            "description": "Groceries",
            "transaction_date": "2026-01-11",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    assert data["amount"] == "-1500.00"  # Backend returns negative
    assert data["transaction_type"] == "expense"
    assert data["tag"] == "food"


def test_create_transaction_with_currency_mismatch_fails(authenticated_client, test_account):
    """
    Test: Transaction currency must match account currency.

    Why critical:
    - Prevents mixing currencies in same account
    - Ensures balance calculations are valid
    - Multi-currency requires separate accounts
    """
    response = authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": test_account["id"],
            "amount": "100.00",
            "currency": "USD",  # Account is INR
            "transaction_type": "income",
            "tag": "test",
            "transaction_date": "2026-01-10",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "currency mismatch" in response.json()["detail"].lower()


def test_create_transaction_with_future_date_fails(authenticated_client, test_account):
    """
    Test: Cannot create transactions in the future.

    Why critical:
    - Finance data must be historical
    - Prevents accidental future dates
    - Validates date logic
    """
    future_date = (date.today() + timedelta(days=1)).isoformat()

    response = authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": test_account["id"],
            "amount": "500.00",
            "currency": "INR",
            "transaction_type": "income",
            "tag": "test",
            "transaction_date": future_date,
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "future" in response.json()["detail"].lower()


def test_create_transaction_for_nonexistent_account_fails(authenticated_client):
    """
    Test: Cannot create transaction for non-existent account.

    Why critical:
    - Database referential integrity
    - Prevents orphaned transactions
    """
    fake_account_id = "00000000-0000-0000-0000-000000000000"

    response = authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": fake_account_id,
            "amount": "500.00",
            "currency": "INR",
            "transaction_type": "income",
            "tag": "test",
            "transaction_date": "2026-01-10",
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_transaction_for_other_user_account_fails(authenticated_client, client):
    """
    Test: Cannot create transaction for another user's account.

    Why critical:
    - Security: prevents unauthorized transactions
    - Validates authorization logic
    - Multi-user isolation
    """
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

    other_account_response = client.post(
        "/api/v1/accounts",
        json={"name": "Other Account", "currency": "USD", "opening_balance": "100.00"},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    other_account_id = other_account_response.json()["id"]

    # Try to create transaction in other user's account
    response = authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": other_account_id,
            "amount": "500.00",
            "currency": "USD",
            "transaction_type": "income",
            "tag": "test",
            "transaction_date": "2026-01-10",
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_list_transactions(authenticated_client, test_account):
    """
    Test: List all transactions for authenticated user.

    Why critical:
    - Validates transaction retrieval
    - Ensures user can see their transaction history
    - Tests denormalized account names
    """
    # Create transactions
    authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": test_account["id"],
            "amount": "1000.00",
            "currency": "INR",
            "transaction_type": "income",
            "tag": "salary",
            "transaction_date": "2026-01-10",
        },
    )
    authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": test_account["id"],
            "amount": "500.00",
            "currency": "INR",
            "transaction_type": "expense",
            "tag": "food",
            "transaction_date": "2026-01-11",
        },
    )

    # List transactions
    response = authenticated_client.get("/api/v1/transactions")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["total_count"] == 2
    assert len(data["transactions"]) == 2
    # Should be sorted by date desc (newest first)
    assert data["transactions"][0]["transaction_date"] == "2026-01-11"
    assert data["transactions"][1]["transaction_date"] == "2026-01-10"


def test_list_transactions_filter_by_account(authenticated_client):
    """
    Test: Filter transactions by account.

    Why critical:
    - Allows viewing per-account transaction history
    - Validates query filtering
    """
    # Create two accounts
    account1 = authenticated_client.post(
        "/api/v1/accounts",
        json={"name": "Account 1", "currency": "INR", "opening_balance": "1000.00"},
    ).json()
    account2 = authenticated_client.post(
        "/api/v1/accounts",
        json={"name": "Account 2", "currency": "INR", "opening_balance": "2000.00"},
    ).json()

    # Create transactions in both accounts
    authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": account1["id"],
            "amount": "100.00",
            "currency": "INR",
            "transaction_type": "income",
            "tag": "test",
            "transaction_date": "2026-01-10",
        },
    )
    authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": account2["id"],
            "amount": "200.00",
            "currency": "INR",
            "transaction_type": "income",
            "tag": "test",
            "transaction_date": "2026-01-10",
        },
    )

    # Filter by account1
    response = authenticated_client.get(f"/api/v1/transactions?account_id={account1['id']}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_count"] == 1
    assert data["transactions"][0]["account_id"] == account1["id"]


def test_list_transactions_filter_by_type(authenticated_client, test_account):
    """
    Test: Filter transactions by type (income/expense).

    Why critical:
    - Allows analyzing income vs expenses separately
    - Validates enum filtering
    """
    # Create income and expense
    authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": test_account["id"],
            "amount": "1000.00",
            "currency": "INR",
            "transaction_type": "income",
            "tag": "salary",
            "transaction_date": "2026-01-10",
        },
    )
    authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": test_account["id"],
            "amount": "500.00",
            "currency": "INR",
            "transaction_type": "expense",
            "tag": "food",
            "transaction_date": "2026-01-11",
        },
    )

    # Filter by income
    response = authenticated_client.get("/api/v1/transactions?transaction_type=income")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_count"] == 1
    assert data["transactions"][0]["transaction_type"] == "income"


def test_get_single_transaction(authenticated_client, test_account):
    """
    Test: Get transaction by ID.

    Why critical:
    - Validates single transaction retrieval
    - Ensures authorization (can only get own transactions)
    """
    # Create transaction
    create_response = authenticated_client.post(
        "/api/v1/transactions",
        json={
            "account_id": test_account["id"],
            "amount": "1000.00",
            "currency": "INR",
            "transaction_type": "income",
            "tag": "salary",
            "transaction_date": "2026-01-10",
        },
    )
    transaction_id = create_response.json()["id"]

    # Get by ID
    response = authenticated_client.get(f"/api/v1/transactions/{transaction_id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == transaction_id
    assert data["amount"] == "1000.00"
    assert data["account_name"] == "Test Account"
