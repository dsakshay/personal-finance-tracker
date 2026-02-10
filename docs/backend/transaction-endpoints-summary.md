# Transaction Endpoints Implementation Summary

## Overview

This document summarizes the implementation of transaction-related API endpoints, highlighting key design decisions, security measures, and data flow.

---

## Implemented Endpoints

### 1. POST /transactions (Income/Expense)

**Location:** [routers/transactions.py:24-138](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/transactions.py#L24-L138)

**Purpose:** Create income or expense transaction

**Request Example:**
```json
POST /api/v1/transactions
Authorization: Bearer <token>

{
  "account_id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": "500.00",
  "currency": "INR",
  "transaction_type": "expense",
  "tag": "groceries",
  "payment_method": "card",
  "description": "Weekly shopping",
  "transaction_date": "2026-01-12"
}
```

**Key Features:**
-  Client sends **positive amounts** only (`"500.00"`)
-  Backend applies sign based on type (expense → negative)
-  Validates account belongs to current user
-  Prevents future transaction dates
-  Validates currency matches account
-  Rejects transfer type (use separate endpoint)

**Data Flow:**
```
Request: amount="500.00" (string)
   ↓
Validate: Decimal("500.00")
   ↓
Convert: 50000 paise (integer)
   ↓
Store: amount_minor=-50000 (negative for expense)
   ↓
Response: amount="-500.00" (signed string)
```

---

### 2. POST /transactions/transfer (Transfers)

**Location:** [routers/transactions.py:141-343](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/transactions.py#L141-L343)

**Purpose:** Create transfer between two accounts (atomic)

**Request Example:**
```json
POST /api/v1/transactions/transfer
Authorization: Bearer <token>

{
  "from_account_id": "550e8400-e29b-41d4-a716-446655440000",
  "to_account_id": "660e8400-e29b-41d4-a716-446655440111",
  "amount": "1000.00",
  "currency": "INR",
  "tag": "transfer",
  "description": "Moving to savings",
  "transaction_date": "2026-01-12"
}
```

**Response Example:**
```json
201 Created

[
  {
    "id": "debit-uuid",
    "account_id": "550e8400-e29b-41d4-a716-446655440000",
    "amount": "-1000.00",
    "transaction_type": "transfer",
    "related_account_id": "660e8400-e29b-41d4-a716-446655440111",
    ...
  },
  {
    "id": "credit-uuid",
    "account_id": "660e8400-e29b-41d4-a716-446655440111",
    "amount": "1000.00",
    "transaction_type": "transfer",
    "related_account_id": "550e8400-e29b-41d4-a716-446655440000",
    ...
  }
]
```

**Key Features:**
-  Creates **TWO transactions atomically**
-  Validates both accounts belong to same user
-  Validates currencies match
-  Links transactions via `related_account_id`
-  Uses database transaction for atomicity
-  Rolls back both on any failure

**Why Two Transactions?**

See [transfer-modeling-guide.md](transfer-modeling-guide.md) for full explanation.

**Short answer:**
1. **Consistent balance calculation:** `SUM(amounts)` works for all transaction types
2. **Complete history:** Each account shows its own transaction record
3. **Audit trail:** Clear "from" and "to" for each account
4. **Accounting standard:** Double-entry bookkeeping

**Atomicity Flow:**
```python
try:
    # Transaction 1: Debit (from_account)
    debit = Transaction(
        account_id=from_account_id,
        amount_minor=-100000,  # -₹1,000
        related_account_id=to_account_id,
    )

    # Transaction 2: Credit (to_account)
    credit = Transaction(
        account_id=to_account_id,
        amount_minor=100000,  # +₹1,000
        related_account_id=from_account_id,
    )

    # Stage both (not yet in database)
    db.add(debit)
    db.add(credit)

    # ATOMIC: Both saved together or both discarded
    db.commit()

except Exception:
    # Automatic rollback
    db.rollback()
    raise
```

**PostgreSQL Transaction:**
```sql
BEGIN;

INSERT INTO transactions (...) VALUES (...);  -- Debit
INSERT INTO transactions (...) VALUES (...);  -- Credit

COMMIT;  -- Both saved together!
-- OR
ROLLBACK;  -- Both discarded together!
```

---

### 3. GET /transactions (List Transactions)

**Location:** [routers/transactions.py:345-450](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/transactions.py#L345-L450)

**Purpose:** List transactions with filters

**Request Example:**
```
GET /api/v1/transactions?account_id=550e8400...&transaction_type=expense&limit=50
Authorization: Bearer <token>
```

**Key Features:**
-  Filters: account_id, transaction_type, tag
-  Pagination: limit (max 500), offset
-  Authorization: Only current user's transactions
-  Ordering: Newest first (transaction_date DESC)
-  Includes account name (denormalized for display)

**Query Filters:**
```python
query = db.query(Transaction).filter(
    Transaction.user_id == current_user.id  # Always filter by user!
)

if account_id:
    query = query.filter(Transaction.account_id == account_id)

if transaction_type:
    query = query.filter(Transaction.transaction_type == transaction_type)

if tag:
    query = query.filter(Transaction.tag == tag.lower())

query = query.order_by(
    Transaction.transaction_date.desc(),
    Transaction.created_at.desc()
).limit(limit).offset(offset)
```

---

## Security Measures

### 1. Multi-User Isolation

**Every endpoint checks:**
```python
# Account must belong to current user
account = db.query(Account).filter(
    Account.id == account_id,
    Account.user_id == current_user.id,  #  Critical!
).first()

if not account:
    raise HTTPException(404, "Account not found")
```

**Prevents:**
- User A accessing User B's accounts
- User A creating transactions in User B's accounts
- User A transferring money from User B's account

### 2. Authorization Before Modification

**Transfer validation order:**
```python
# 1. Validate input
if from_account_id == to_account_id:
    raise HTTPException(400, "Cannot transfer to same account")

# 2. Check ownership (BEFORE creating any data)
from_account = db.query(Account).filter(
    Account.id == from_account_id,
    Account.user_id == current_user.id,
).first()

to_account = db.query(Account).filter(
    Account.id == to_account_id,
    Account.user_id == current_user.id,
).first()

if not from_account or not to_account:
    raise HTTPException(404, "Account(s) not found")

# 3. Only now create transactions
```

**Why this order matters:**
- Fail fast on invalid input
- Check permissions before making changes
- No partial state if authorization fails

### 3. Currency Validation

```python
# Transaction currency must match account
if transaction.currency != account.currency:
    raise HTTPException(400, f"Currency mismatch: {transaction.currency} ≠ {account.currency}")

# Transfer: both accounts must have same currency
if from_account.currency != to_account.currency:
    raise HTTPException(400, f"Cannot transfer between {from_account.currency} and {to_account.currency}")
```

**Prevents:**
- Recording $100 expense in INR account
- Transferring ₹1,000 to USD account

### 4. Date Validation

```python
# Prevent future transactions
today = date.today()
if transaction_date > today:
    raise HTTPException(400, f"Transaction date cannot be in the future. Today is {today}")
```

**Prevents:**
- Recording transactions that haven't happened yet
- Data integrity issues from future-dated transactions

---

## Data Transformations

### Request → Database

**Client sends human-readable amounts:**
```json
{
  "amount": "500.00",
  "currency": "INR",
  "transaction_type": "expense"
}
```

**Backend processes:**
```python
# 1. Validate
amount_decimal = Decimal("500.00")

# 2. Convert to minor units
amount_minor = int(amount_decimal * 100)  # 50000 paise

# 3. Apply sign based on type
if transaction_type == "expense":
    amount_minor = -amount_minor  # -50000

# 4. Store
transaction = Transaction(amount_minor=-50000)
```

**Database stores:**
```sql
INSERT INTO transactions (amount_minor, currency, ...)
VALUES (-50000, 'INR', ...);
```

### Database → Response

**Database returns:**
```python
Transaction(
    amount_minor=-50000,
    currency="INR",
    transaction_type=TransactionType.EXPENSE,
)
```

**Backend converts:**
```python
# 1. Convert to decimal
amount_decimal = Decimal(amount_minor) / 100  # Decimal("-500.00")

# 2. Format as string
amount_string = f"{amount_decimal:.2f}"  # "-500.00"

# 3. Return in response
response = {
    "amount": "-500.00",  # Signed string
    "currency": "INR",
    "transaction_type": "expense"
}
```

**Client receives:**
```json
{
  "amount": "-500.00",
  "currency": "INR",
  "transaction_type": "expense"
}
```

---

## Validation Rules

### Amount Validation

```python
# Must be non-zero
if amount == "0.00":
    raise ValueError("Amount cannot be zero")

# Must have exactly 2 decimal places
if not re.match(r"^\d+\.\d{2}$", amount):
    raise ValueError("Amount must have exactly 2 decimal places")

# Must be within range
if abs(Decimal(amount)) > Decimal("9999999999.99"):
    raise ValueError("Amount exceeds maximum")
```

### Currency Validation

```python
# Must be 3 uppercase letters
if len(currency) != 3 or not currency.isalpha():
    raise ValueError("Currency must be 3 letters")

# Must be supported
SUPPORTED_CURRENCIES = {"INR", "USD", "EUR", "GBP", "JPY", ...}
if currency.upper() not in SUPPORTED_CURRENCIES:
    raise ValueError(f"Unsupported currency: {currency}")
```

### Tag Validation

```python
# Must not be empty
if not tag or tag.strip() == "":
    raise ValueError("Tag cannot be empty")

# Normalize to lowercase
tag = tag.lower().strip()
```

### Date Validation

```python
# Must be valid ISO 8601 date
try:
    transaction_date = date.fromisoformat("2026-01-12")
except ValueError:
    raise ValueError("Invalid date format. Use YYYY-MM-DD")

# Must not be in future
if transaction_date > date.today():
    raise ValueError("Transaction date cannot be in the future")

# Must not be too old (optional)
if transaction_date < date.today() - timedelta(days=3650):  # 10 years
    raise ValueError("Transaction date is too old")
```

---

## Error Handling

### Validation Errors (400/422)

```python
# Pydantic validation
{
  "error": "validation_error",
  "message": "Invalid request data",
  "details": {
    "amount": ["Amount must have exactly 2 decimal places"],
    "currency": ["Unsupported currency 'XYZ'"]
  }
}
```

### Authorization Errors (401/403/404)

```python
# Account not found OR not owned by user
# Don't reveal which (security)
raise HTTPException(404, "Account not found")

# Never say "Account exists but belongs to another user"
```

### Business Logic Errors (400)

```python
# Currency mismatch
{
  "error": "currency_mismatch",
  "message": "Transaction currency 'USD' does not match account currency 'INR'"
}

# Same account transfer
{
  "error": "invalid_transfer",
  "message": "Cannot transfer to the same account"
}

# Future date
{
  "error": "invalid_date",
  "message": "Transaction date cannot be in the future. Today is 2026-01-12"
}
```

### Database Errors (500)

```python
# Rollback on integrity error
try:
    db.commit()
except IntegrityError as e:
    db.rollback()
    raise HTTPException(400, f"Database constraint violation: {e}")
```

---

## Atomicity Deep Dive

### What is Atomicity?

**Definition:** All operations in a transaction succeed together, or all fail together.

**Example:**
```
Operation 1: Debit Account A by ₹1,000
Operation 2: Credit Account B by ₹1,000

Atomicity guarantees:
 Both succeed → Transfer complete
 Either fails → Both rolled back, no partial state
```

### How We Implement It

**1. Database Transaction (Implicit)**

```python
# SQLAlchemy session automatically starts transaction
db = SessionLocal()

# All operations within session are part of transaction
db.add(debit)
db.add(credit)

# Commit makes it permanent
db.commit()

# Rollback discards all changes
db.rollback()
```

**2. Single Commit Point**

```python
#  BAD: Multiple commits
db.add(debit)
db.commit()  # First commit

db.add(credit)
db.commit()  # Second commit
# → If second fails, first is already saved!

#  GOOD: Single commit
db.add(debit)
db.add(credit)
db.commit()  # Both committed together
```

**3. Exception Handling**

```python
try:
    db.add(debit)
    db.add(credit)
    db.commit()  # Atomic point
    return [debit, credit]

except IntegrityError:
    db.rollback()  # Undo both
    raise HTTPException(400, "Constraint violation")

except Exception:
    db.rollback()  # Undo both
    raise HTTPException(500, "Internal error")
```

### What Can Go Wrong?

**Scenario 1: Network Failure**
```python
db.add(debit)
db.add(credit)
db.commit()  # Network error!

# PostgreSQL never receives commit command
# → Automatic rollback after timeout
# → Both transactions discarded 
```

**Scenario 2: Constraint Violation**
```python
debit = Transaction(account_id="INVALID_UUID", ...)
credit = Transaction(account_id=valid_uuid, ...)

db.add(debit)
db.add(credit)
db.commit()

# PostgreSQL rejects: Foreign key violation
# → Automatic rollback
# → Both discarded 
```

**Scenario 3: Server Crash**
```python
db.add(debit)
db.add(credit)
db.commit()  #  Success!

#  Server crashes immediately after

# What happens?
# → Data was already written to PostgreSQL
# → Durability (ACID: D) guarantees persistence
# → Both transactions safe 
```

### ACID Properties

**A - Atomicity**
```
Both transactions save together, or both fail together.
No partial transfers.
```

**C - Consistency**
```
Database constraints enforced:
- Foreign keys valid
- Check constraints pass
- NOT NULL enforced
If any violation → rollback all
```

**I - Isolation**
```
Concurrent transfers don't interfere:
- Transfer A→B: ₹1,000
- Transfer A→C: ₹500
Both can happen simultaneously without corruption.
```

**D - Durability**
```
Once db.commit() succeeds:
- Data is on disk
- Survives crashes
- Permanent (until explicitly deleted)
```

---

## Testing Strategies

### Unit Tests

```python
def test_create_expense():
    # Test single expense creation
    response = client.post("/transactions", json={
        "account_id": account.id,
        "amount": "500.00",
        "currency": "INR",
        "transaction_type": "expense",
        "tag": "groceries",
        "transaction_date": "2026-01-12"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == "-500.00"  # Note: negative
    assert data["transaction_type"] == "expense"
```

```python
def test_create_transfer_atomic():
    # Test atomic transfer creation
    initial_balance_a = get_balance(account_a.id)
    initial_balance_b = get_balance(account_b.id)

    response = client.post("/transactions/transfer", json={
        "from_account_id": account_a.id,
        "to_account_id": account_b.id,
        "amount": "1000.00",
        "currency": "INR",
        "transaction_date": "2026-01-12"
    })

    assert response.status_code == 201
    data = response.json()
    assert len(data) == 2  # Two transactions

    # Verify balances changed correctly
    assert get_balance(account_a.id) == initial_balance_a - 100000
    assert get_balance(account_b.id) == initial_balance_b + 100000
```

### Integration Tests

```python
def test_transfer_rollback_on_error():
    # Simulate constraint violation
    with mock.patch("db.commit", side_effect=IntegrityError):
        response = client.post("/transactions/transfer", json={...})

        assert response.status_code == 400

        # Verify NO transactions were created
        assert count_transactions(account_a.id) == 0
        assert count_transactions(account_b.id) == 0

        # Verify balances unchanged
        assert get_balance(account_a.id) == initial_balance_a
        assert get_balance(account_b.id) == initial_balance_b
```

### Security Tests

```python
def test_cannot_access_other_user_account():
    # User A tries to create transaction in User B's account
    response = client.post(
        "/transactions",
        headers={"Authorization": f"Bearer {user_a_token}"},
        json={
            "account_id": user_b_account.id,  # Different user!
            "amount": "500.00",
            ...
        }
    )

    assert response.status_code == 404  # Not 403!
    assert "not found" in response.json()["detail"].lower()
```

---

## Performance Considerations

### Current Implementation

**POST /transactions:**
-  O(1) queries (1 account lookup, 1 insert)
-  Efficient

**POST /transactions/transfer:**
-  O(1) queries (2 account lookups, 2 inserts)
-  Atomic with minimal overhead

**GET /transactions:**
-  O(1) query with filters
-  Pagination prevents large result sets
- No account name denormalization yet (requires JOIN)

### Optimization Opportunities

**1. Denormalize account names in response**

```python
# Current: Requires separate query or JOIN
transaction.account_name  # Not in model

# Future: Include in response schema
query = db.query(Transaction, Account.name).join(Account).filter(...)
```

**2. Add database indexes**

```sql
-- For common queries
CREATE INDEX idx_transactions_user_date
ON transactions (user_id, transaction_date DESC);

CREATE INDEX idx_transactions_account_date
ON transactions (account_id, transaction_date DESC);

CREATE INDEX idx_transactions_tag
ON transactions (tag);
```

**3. Connection pooling**

Already handled by SQLAlchemy `create_engine(pool_size=...)`.

---

## Summary

### Key Implementation Points

1. **Two-transaction model for transfers**
   - Each account has its own transaction record
   - Linked via `related_account_id`
   - Created atomically in single database transaction

2. **Atomicity prevents money loss**
   - Single `db.commit()` for both transactions
   - Rollback on any error
   - ACID guarantees by PostgreSQL

3. **Security at every layer**
   - User ID from JWT token (not request)
   - Account ownership verified before modification
   - Currency validation prevents mismatches
   - Date validation prevents future transactions

4. **Data transformations**
   - Client: Decimal strings (`"500.00"`)
   - Database: Integer minor units (`50000`)
   - Conversion at API boundaries

5. **Comprehensive validation**
   - Amount: Non-zero, 2 decimal places
   - Currency: Match account currency
   - Dates: Not in future
   - Accounts: Belong to same user

### Files Modified/Created

-  [schemas/transaction.py](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/schemas/transaction.py) - Request/response schemas
-  [routers/transactions.py](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/transactions.py) - Endpoint implementations
-  [transfer-modeling-guide.md](transfer-modeling-guide.md) - Why two transactions, atomicity explanation
-  [transaction-endpoints-summary.md](transaction-endpoints-summary.md) - This document

### Next Steps

- Implement GET /summary/monthly endpoint
- Add comprehensive tests
- Set up database indexes
- Implement balance caching (optional, ADR-004)
