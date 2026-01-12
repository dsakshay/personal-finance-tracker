"""
Transfer transaction tests.

CRITICAL for finance correctness:
- Transfers create exactly TWO linked transactions atomically
- Money is conserved (no money created or destroyed)
- One debit (-amount) and one credit (+amount)
- Both transactions succeed or both fail (atomicity)
- Related account links are bidirectional
"""

import pytest
from fastapi import status
from datetime import date, timedelta


@pytest.fixture
def test_accounts(authenticated_client):
    """Create two test accounts for transfer tests."""
    account1 = authenticated_client.post(
        "/api/v1/accounts",
        json={
            "name": "Checking Account",
            "currency": "INR",
            "opening_balance": "10000.00",
        },
    ).json()

    account2 = authenticated_client.post(
        "/api/v1/accounts",
        json={
            "name": "Savings Account",
            "currency": "INR",
            "opening_balance": "50000.00",
        },
    ).json()

    return account1, account2


def test_transfer_creates_two_linked_transactions(authenticated_client, test_accounts):
    """
    Test: Transfer creates exactly TWO transactions atomically.

    Why CRITICAL:
    - Core double-entry bookkeeping principle
    - One debit (source) and one credit (destination)
    - Both must reference each other via related_account_id
    - Transfer ID returned for tracking
    """
    source_account, dest_account = test_accounts

    response = authenticated_client.post(
        "/api/v1/transactions/transfer",
        json={
            "account_id": source_account["id"],
            "amount": "1000.00",
            "currency": "INR",
            "transaction_type": "transfer",
            "tag": "transfer",
            "related_account_id": dest_account["id"],
            "description": "Moving to savings",
            "transaction_date": "2026-01-12",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    # Must return transfer_id and two transactions
    assert "transfer_id" in data
    assert "transactions" in data
    assert len(data["transactions"]) == 2

    txn1, txn2 = data["transactions"]

    # Transaction 1: Debit (money leaving source)
    assert txn1["account_id"] == source_account["id"]
    assert txn1["amount"] == "-1000.00"  # NEGATIVE
    assert txn1["transaction_type"] == "transfer"
    assert txn1["related_account_id"] == dest_account["id"]
    assert txn1["related_account_name"] == "Savings Account"

    # Transaction 2: Credit (money arriving at destination)
    assert txn2["account_id"] == dest_account["id"]
    assert txn2["amount"] == "1000.00"  # POSITIVE
    assert txn2["transaction_type"] == "transfer"
    assert txn2["related_account_id"] == source_account["id"]
    assert txn2["related_account_name"] == "Checking Account"


def test_transfer_money_is_conserved(authenticated_client, test_accounts):
    """
    Test: Transfer does not create or destroy money.

    Why CRITICAL:
    - Sum of both transactions must be zero
    - Total balance across all accounts remains unchanged
    - Validates double-entry accounting
    """
    source_account, dest_account = test_accounts

    # Get initial total balance
    accounts_before = authenticated_client.get("/api/v1/accounts").json()
    total_before = sum(
        float(acc["current_balance"]) for acc in accounts_before["accounts"]
    )

    # Execute transfer
    authenticated_client.post(
        "/api/v1/transactions/transfer",
        json={
            "account_id": source_account["id"],
            "amount": "2000.00",
            "currency": "INR",
            "transaction_type": "transfer",
            "tag": "transfer",
            "related_account_id": dest_account["id"],
            "transaction_date": "2026-01-12",
        },
    )

    # Get final total balance
    accounts_after = authenticated_client.get("/api/v1/accounts").json()
    total_after = sum(
        float(acc["current_balance"]) for acc in accounts_after["accounts"]
    )

    # Total must be unchanged
    assert total_before == total_after

    # Verify individual balances
    for acc in accounts_after["accounts"]:
        if acc["id"] == source_account["id"]:
            # 10000.00 - 2000.00 = 8000.00
            assert acc["current_balance"] == "8000.00"
        elif acc["id"] == dest_account["id"]:
            # 50000.00 + 2000.00 = 52000.00
            assert acc["current_balance"] == "52000.00"


def test_transfer_between_different_currencies_fails(authenticated_client):
    """
    Test: Cannot transfer between accounts with different currencies.

    Why CRITICAL:
    - Prevents invalid currency mixing
    - Exchange rates require separate conversion logic
    - Must use same currency for direct transfers
    """
    # Create INR and USD accounts
    inr_account = authenticated_client.post(
        "/api/v1/accounts",
        json={"name": "INR Account", "currency": "INR", "opening_balance": "10000.00"},
    ).json()

    usd_account = authenticated_client.post(
        "/api/v1/accounts",
        json={"name": "USD Account", "currency": "USD", "opening_balance": "100.00"},
    ).json()

    # Try transfer
    response = authenticated_client.post(
        "/api/v1/transactions/transfer",
        json={
            "account_id": inr_account["id"],
            "amount": "1000.00",
            "currency": "INR",
            "transaction_type": "transfer",
            "tag": "transfer",
            "related_account_id": usd_account["id"],
            "transaction_date": "2026-01-12",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "currency" in response.json()["detail"].lower()


def test_transfer_to_same_account_fails(authenticated_client, test_accounts):
    """
    Test: Cannot transfer to the same account.

    Why CRITICAL:
    - Logically invalid operation
    - Would create meaningless transactions
    - Prevents user errors
    """
    source_account, _ = test_accounts

    response = authenticated_client.post(
        "/api/v1/transactions/transfer",
        json={
            "account_id": source_account["id"],
            "amount": "1000.00",
            "currency": "INR",
            "transaction_type": "transfer",
            "tag": "transfer",
            "related_account_id": source_account["id"],  # Same account
            "transaction_date": "2026-01-12",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "same account" in response.json()["detail"].lower()


def test_transfer_with_future_date_fails(authenticated_client, test_accounts):
    """
    Test: Cannot create transfer with future date.

    Why CRITICAL:
    - Same validation as regular transactions
    - Finance data must be historical
    """
    source_account, dest_account = test_accounts
    future_date = (date.today() + timedelta(days=1)).isoformat()

    response = authenticated_client.post(
        "/api/v1/transactions/transfer",
        json={
            "account_id": source_account["id"],
            "amount": "1000.00",
            "currency": "INR",
            "transaction_type": "transfer",
            "tag": "transfer",
            "related_account_id": dest_account["id"],
            "transaction_date": future_date,
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "future" in response.json()["detail"].lower()


def test_transfer_to_other_user_account_fails(authenticated_client, client):
    """
    Test: Cannot transfer to another user's account.

    Why CRITICAL:
    - Security: prevents unauthorized money movement
    - Validates authorization on both accounts
    - Multi-user isolation
    """
    # Create account for first user
    source_account = authenticated_client.post(
        "/api/v1/accounts",
        json={"name": "My Account", "currency": "INR", "opening_balance": "10000.00"},
    ).json()

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

    other_account = client.post(
        "/api/v1/accounts",
        json={"name": "Other Account", "currency": "INR", "opening_balance": "5000.00"},
        headers={"Authorization": f"Bearer {other_token}"},
    ).json()

    # Try to transfer to other user's account
    response = authenticated_client.post(
        "/api/v1/transactions/transfer",
        json={
            "account_id": source_account["id"],
            "amount": "1000.00",
            "currency": "INR",
            "transaction_type": "transfer",
            "tag": "transfer",
            "related_account_id": other_account["id"],  # Other user's account
            "transaction_date": "2026-01-12",
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_transfer_appears_in_transaction_list(authenticated_client, test_accounts):
    """
    Test: Both transfer transactions appear in transaction list.

    Why CRITICAL:
    - Users must see complete transaction history
    - Both sides of transfer are visible
    - Can filter by account to see account-specific view
    """
    source_account, dest_account = test_accounts

    # Create transfer
    authenticated_client.post(
        "/api/v1/transactions/transfer",
        json={
            "account_id": source_account["id"],
            "amount": "500.00",
            "currency": "INR",
            "transaction_type": "transfer",
            "tag": "transfer",
            "related_account_id": dest_account["id"],
            "transaction_date": "2026-01-12",
        },
    )

    # Get all transactions
    response = authenticated_client.get("/api/v1/transactions")
    data = response.json()

    # Should have 2 transactions
    assert data["total_count"] == 2

    # Verify both are transfers with correct amounts
    transactions = data["transactions"]
    amounts = [txn["amount"] for txn in transactions]
    assert "-500.00" in amounts  # Debit
    assert "500.00" in amounts  # Credit

    # Verify related accounts are populated
    for txn in transactions:
        assert txn["related_account_id"] is not None
        assert txn["related_account_name"] is not None


def test_transfer_atomicity_simulation(authenticated_client, test_accounts, db_session):
    """
    Test: Both transactions are created in single database commit.

    Why CRITICAL:
    - If one fails, both must be rolled back
    - Prevents partial transfers (money lost or duplicated)
    - ACID guarantee: Atomicity

    Note: This test verifies the result. True atomicity testing
    requires database transaction inspection or failure injection.
    """
    source_account, dest_account = test_accounts

    # Create transfer
    response = authenticated_client.post(
        "/api/v1/transactions/transfer",
        json={
            "account_id": source_account["id"],
            "amount": "1000.00",
            "currency": "INR",
            "transaction_type": "transfer",
            "tag": "transfer",
            "related_account_id": dest_account["id"],
            "transaction_date": "2026-01-12",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED

    # Verify BOTH transactions exist
    all_txns = authenticated_client.get("/api/v1/transactions").json()
    assert all_txns["total_count"] == 2

    # If atomicity failed, we'd have 0 or 1 transaction instead of 2
    # This validates that the commit happened after both were created
