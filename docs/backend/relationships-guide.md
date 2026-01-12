# SQLAlchemy Relationships Guide

## Overview

The personal finance tracker uses SQLAlchemy 2.0 relationships to model connections between Users, Accounts, and Transactions. This document explains each relationship and how they simplify data querying.

## Relationship Diagram

```
User (1) ──────< (many) Account (1) ──────< (many) Transaction
  │                                               │
  └───────────────< (many) Transaction ──────────┘
                            │
                            │ (optional)
                            ▼
                        related_account_id ───> Account
                        (for transfers only)
```

## Model Relationships

### 1. User → Accounts (One-to-Many)

**Location:** [user.py:50-55](../backend/app/models/user.py#L50-L55)

```python
# In User model
accounts: Mapped[list["Account"]] = relationship(
    "Account",
    back_populates="user",
    cascade="all, delete-orphan",
    lazy="selectin",
)
```

**Reverse side:** [account.py:69](../backend/app/models/account.py#L69)

```python
# In Account model
user: Mapped["User"] = relationship("User", back_populates="accounts")
```

**What it represents:**
- One user owns multiple accounts (savings, checking, credit cards, etc.)
- Each account belongs to exactly one user
- Foreign key: `Account.user_id` → `User.id`

**How it helps querying:**

```python
# Without relationship: Manual join required
user = session.get(User, user_id)
accounts = session.query(Account).filter(Account.user_id == user_id).all()

# With relationship: Automatic eager loading
user = session.get(User, user_id)
accounts = user.accounts  # Already loaded due to selectin
```

**Benefits:**
- `cascade="all, delete-orphan"`: Deleting a user automatically deletes all their accounts
- `lazy="selectin"`: Uses efficient SELECT IN query to load accounts
- Type safety with `Mapped[list["Account"]]`

---

### 2. User → Transactions (One-to-Many)

**Location:** [user.py:58-63](../backend/app/models/user.py#L58-L63)

```python
# In User model
transactions: Mapped[list["Transaction"]] = relationship(
    "Transaction",
    back_populates="user",
    cascade="all, delete-orphan",
    lazy="selectin",
)
```

**Reverse side:** [transaction.py:124](../backend/app/models/transaction.py#L124)

```python
# In Transaction model
user: Mapped["User"] = relationship("User", back_populates="transactions")
```

**What it represents:**
- One user has many transactions across all their accounts
- Each transaction belongs to exactly one user
- Foreign key: `Transaction.user_id` → `User.id`

**How it helps querying:**

```python
# Get all user transactions with one query
user = session.get(User, user_id)
all_transactions = user.transactions  # Across all accounts

# Filter user's transactions by type
expenses = [t for t in user.transactions if t.transaction_type == TransactionType.EXPENSE]

# Total user spending
total_expenses = sum(t.amount_minor for t in user.transactions
                    if t.transaction_type == TransactionType.EXPENSE)
```

**Benefits:**
- Direct access to all user transactions without joining through accounts
- Multi-user isolation: Ensures transaction data separation
- Cascade delete: User deletion removes all transactions

---

### 3. Account → Transactions (One-to-Many)

**Location:** [account.py:72-78](../backend/app/models/account.py#L72-L78)

```python
# In Account model
transactions: Mapped[list["Transaction"]] = relationship(
    "Transaction",
    back_populates="account",
    foreign_keys="Transaction.account_id",
    cascade="all, delete-orphan",
    lazy="selectin",
)
```

**Reverse side:** [transaction.py:127-131](../backend/app/models/transaction.py#L127-L131)

```python
# In Transaction model
account: Mapped["Account"] = relationship(
    "Account",
    back_populates="transactions",
    foreign_keys=[account_id],
)
```

**What it represents:**
- One account has many transactions (income, expenses, transfers)
- Each transaction belongs to exactly one account
- Foreign key: `Transaction.account_id` → `Account.id`

**How it helps querying:**

```python
# Calculate current account balance
account = session.get(Account, account_id)
transaction_sum = sum(t.amount_minor for t in account.transactions)
current_balance = account.opening_balance_minor + transaction_sum

# Get account activity for date range
from datetime import date
transactions_this_month = [
    t for t in account.transactions
    if t.transaction_date.month == date.today().month
]

# Access account info from transaction
transaction = session.get(Transaction, transaction_id)
account_name = transaction.account.name  # No extra query needed
account_currency = transaction.account.currency
```

**Benefits:**
- `foreign_keys="Transaction.account_id"`: Disambiguates from `related_account_id`
- Balance calculation becomes simple aggregation
- Cascade delete: Account deletion removes all transactions

---

### 4. Transfer Relationships (Special Case)

**Location:** [account.py:81-86](../backend/app/models/account.py#L81-L86)

```python
# In Account model
incoming_transfers: Mapped[list["Transaction"]] = relationship(
    "Transaction",
    back_populates="related_account",
    foreign_keys="Transaction.related_account_id",
    lazy="selectin",
)
```

**Reverse side:** [transaction.py:134-138](../backend/app/models/transaction.py#L134-L138)

```python
# In Transaction model
related_account: Mapped["Account | None"] = relationship(
    "Account",
    back_populates="incoming_transfers",
    foreign_keys=[related_account_id],
)
```

**What it represents:**
- For transfer transactions: links to the other account involved
- `related_account_id` points to the destination account
- Foreign key: `Transaction.related_account_id` → `Account.id` (nullable)

**How transfers work:**

Transfer from Account A to Account B creates **two transactions**:

```
Transaction 1 (Debit from A):
  account_id: A
  amount_minor: -1000  (negative)
  related_account_id: B
  transaction_type: TRANSFER

Transaction 2 (Credit to B):
  account_id: B
  amount_minor: +1000  (positive)
  related_account_id: A
  transaction_type: TRANSFER
```

**How it helps querying:**

```python
# Get account with all transfer information
account = session.get(Account, account_id)

# Outgoing transfers (money leaving this account)
outgoing = [
    t for t in account.transactions
    if t.transaction_type == TransactionType.TRANSFER and t.amount_minor < 0
]

# Incoming transfers (money entering this account)
incoming = [
    t for t in account.incoming_transfers
    if t.transaction_type == TransactionType.TRANSFER
]

# Get transfer destination
transfer_transaction = outgoing[0]
destination_account = transfer_transaction.related_account
print(f"Transferred to: {destination_account.name}")

# Trace transfer chain
source_account = transfer_transaction.account.name
dest_account = transfer_transaction.related_account.name
print(f"Transfer: {source_account} → {dest_account}")
```

**Benefits:**
- `foreign_keys=[related_account_id]`: Prevents ambiguous relationship with `account_id`
- Bidirectional transfer tracking without N+1 queries
- Nullable: Only set for transfers, not income/expenses

---

## Key Design Decisions

### 1. Avoiding Ambiguous Relationships

**Problem:** Transaction has TWO foreign keys to Account:
- `account_id`: The account this transaction belongs to
- `related_account_id`: The other account (for transfers only)

**Solution:** Explicitly specify `foreign_keys` in relationships:

```python
# Primary relationship uses account_id
transactions: Mapped[list["Transaction"]] = relationship(
    foreign_keys="Transaction.account_id",  # Explicit!
)

# Transfer relationship uses related_account_id
incoming_transfers: Mapped[list["Transaction"]] = relationship(
    foreign_keys="Transaction.related_account_id",  # Explicit!
)
```

### 2. Using `back_populates` (Not `backref`)

SQLAlchemy 2.0 prefers `back_populates` for clarity:

```python
# User model
accounts: Mapped[list["Account"]] = relationship(
    "Account",
    back_populates="user",  # References Account.user
)

# Account model
user: Mapped["User"] = relationship(
    "User",
    back_populates="accounts",  # References User.accounts
)
```

**Benefits:**
- Explicit: Both sides defined clearly
- Type-safe: IDE can validate relationship names
- No magic: Relationships visible in both models

### 3. Cascade Behavior

```python
cascade="all, delete-orphan"
```

**What it does:**
- `all`: Propagates save, delete, merge, refresh operations
- `delete-orphan`: Deletes child if removed from parent collection

**Example:**

```python
user = session.get(User, user_id)
account = user.accounts[0]

# Remove account from collection
user.accounts.remove(account)
session.commit()
# Account is automatically deleted from database
```

### 4. Lazy Loading Strategy

```python
lazy="selectin"
```

**What it does:**
- Loads related objects using `SELECT ... WHERE id IN (...)` query
- Avoids N+1 problem while keeping separate queries

**Comparison:**

```python
# lazy="select" (default): N+1 problem
users = session.query(User).all()
for user in users:
    print(user.accounts)  # Separate query per user!

# lazy="selectin": Optimal
users = session.query(User).all()
# Generates: SELECT * FROM accounts WHERE user_id IN (...)
for user in users:
    print(user.accounts)  # No additional queries!

# lazy="joined": Single query with LEFT JOIN
# Good for single objects, inefficient for collections
```

---

## Query Examples

### Example 1: User Dashboard

```python
from sqlalchemy.orm import selectinload

# Load user with all data
user = session.get(User, user_id, options=[
    selectinload(User.accounts),
    selectinload(User.transactions)
])

# Calculate total net worth
net_worth = sum(
    account.opening_balance_minor +
    sum(t.amount_minor for t in account.transactions)
    for account in user.accounts
)

# Recent activity across all accounts
recent = sorted(
    user.transactions,
    key=lambda t: t.transaction_date,
    reverse=True
)[:10]
```

### Example 2: Account Statement

```python
# Get account with transactions
account = session.get(Account, account_id)

# Group by type
income = [t for t in account.transactions if t.transaction_type == TransactionType.INCOME]
expenses = [t for t in account.transactions if t.transaction_type == TransactionType.EXPENSE]
transfers_out = [t for t in account.transactions if t.transaction_type == TransactionType.TRANSFER]
transfers_in = account.incoming_transfers

# Calculate balance
current_balance = account.opening_balance_minor + sum(t.amount_minor for t in account.transactions)
```

### Example 3: Transfer Analysis

```python
# Find all transfers between two accounts
account_a = session.get(Account, account_a_id)
account_b = session.get(Account, account_b_id)

# Transfers from A to B
a_to_b = [
    t for t in account_a.transactions
    if t.transaction_type == TransactionType.TRANSFER
    and t.related_account_id == account_b.id
]

# Transfers from B to A
b_to_a = [
    t for t in account_a.incoming_transfers
    if t.account_id == account_b.id
]

# Net flow
net_flow = sum(t.amount_minor for t in a_to_b) + sum(t.amount_minor for t in b_to_a)
```

---

## Summary

| Relationship | Type | Purpose | Key Benefit |
|-------------|------|---------|-------------|
| `User.accounts` | One-to-Many | User owns multiple accounts | Multi-user isolation, cascade delete |
| `User.transactions` | One-to-Many | User has all transactions | Direct access without account join |
| `Account.transactions` | One-to-Many | Account has transaction history | Balance calculation, activity tracking |
| `Account.incoming_transfers` | One-to-Many | Track money coming into account | Bidirectional transfer visibility |
| `Transaction.account` | Many-to-One | Transaction belongs to account | Access account details from transaction |
| `Transaction.related_account` | Many-to-One (optional) | Other account in transfer | Complete transfer tracking |

**Relationships eliminate:**
- Manual JOIN queries
- N+1 query problems
- Foreign key management complexity
- Data integrity issues

**Relationships provide:**
- Type-safe property access
- Automatic eager/lazy loading
- Cascade operations
- Bidirectional navigation
