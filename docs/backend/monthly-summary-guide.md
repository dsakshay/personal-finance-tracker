# Monthly Summary Aggregation Guide

## Overview

This document explains how the monthly summary endpoint aggregates transaction data to provide comprehensive financial insights without using cached balances.

**Key Principle:** All summaries are **derived entirely from transactions** on-demand (ADR-004: No cached summaries in MVP).

---

## Table of Contents

1. [Aggregation Logic](#aggregation-logic)
2. [Step-by-Step Calculation](#step-by-step-calculation)
3. [Data Structures](#data-structures)
4. [Query Performance](#query-performance)
5. [Examples](#examples)

---

## Aggregation Logic

### Core Formula

```
Opening Balance = Sum of (Account Opening Balances + All Transactions Before Month)
Total Income    = Sum of Income Transactions in Month (excludes transfers)
Total Expenses  = Sum of Expense Transactions in Month (excludes transfers)
Closing Balance = Opening Balance + All Transactions in Month (includes transfers)
Net Savings     = Total Income - Total Expenses
```

### Why Transfers are Excluded

**Transfers don't create or destroy money—they just move it between accounts:**

```
Before transfer:
Account A: ₹10,000
Account B: ₹5,000
Total: ₹15,000

Transfer ₹1,000 from A to B:
Transaction 1: Account A, -₹1,000
Transaction 2: Account B, +₹1,000

After transfer:
Account A: ₹9,000
Account B: ₹6,000
Total: ₹15,000  (unchanged!)

Income: ₹0 (no money came in)
Expenses: ₹0 (no money went out)
Net change: ₹0
```

**If we counted transfers as income/expense:**
```
 Wrong:
Income: +₹1,000 (credit to B)
Expenses: -₹1,000 (debit from A)
Net: ₹0 (correct by accident, but misleading)

User sees: "I earned ₹1,000 income!" (false)
```

**Correct approach:**
```
 Right:
Income: ₹0
Expenses: ₹0
Net: ₹0
Transfers: 1 transaction pair

User sees: "No income or expenses, just moved money" (accurate)
```

---

## Step-by-Step Calculation

### Example Scenario

**User has:**
- Account A (Checking): opened with ₹5,000
- Account B (Savings): opened with ₹3,000

**January 2026 transactions:**
```
Jan 1:  +₹50,000 (salary to Checking)
Jan 5:  -₹2,000 (groceries from Checking)
Jan 10: -₹1,000 (utilities from Checking)
Jan 15: Transfer ₹10,000 from Checking to Savings
         → -₹10,000 (Checking)
         → +₹10,000 (Savings)
Jan 20: -₹500 (dining from Checking)
Jan 25: -₹3,000 (rent from Checking)
```

**User requests:** `GET /summary/monthly?year=2026&month=2`

---

### Step 1: Calculate Opening Balance (Feb 1, 2026)

**Opening balance = Account opening balances + Transactions before Feb 1**

```python
# Account opening balances
Account A: ₹5,000
Account B: ₹3,000
Total: ₹8,000

# Transactions before Feb 1 (all of January)
Jan 1:  +₹50,000 (income)
Jan 5:  -₹2,000 (expense)
Jan 10: -₹1,000 (expense)
Jan 15: -₹10,000 (transfer debit)
Jan 15: +₹10,000 (transfer credit)
Jan 20: -₹500 (expense)
Jan 25: -₹3,000 (expense)
Sum: ₹43,500

# Opening balance for Feb
₹8,000 + ₹43,500 = ₹51,500
```

**SQL queries:**
```sql
-- Get account opening balances
SELECT SUM(opening_balance_minor) FROM accounts
WHERE user_id = 'user-uuid';
-- Result: 800000 paise (₹8,000)

-- Get transaction sum before Feb 1
SELECT SUM(amount_minor) FROM transactions
WHERE user_id = 'user-uuid'
  AND transaction_date < '2026-02-01';
-- Result: 4350000 paise (₹43,500)

-- Opening balance for Feb
800000 + 4350000 = 5150000 paise (₹51,500)
```

---

### Step 2: Get All February Transactions

```python
# Query all transactions in Feb 1-28, 2026
transactions = db.query(Transaction).filter(
    Transaction.user_id == current_user.id,
    Transaction.transaction_date >= '2026-02-01',
    Transaction.transaction_date <= '2026-02-28',
).all()

# Example February transactions:
Feb 1:  +₹50,000 (salary to Checking)
Feb 8:  -₹2,500 (groceries from Checking)
Feb 12: -₹1,200 (utilities from Checking)
Feb 15: Transfer ₹5,000 from Checking to Savings
         → -₹5,000 (Checking)
         → +₹5,000 (Savings)
Feb 20: -₹800 (dining from Checking)
```

---

### Step 3: Aggregate by Type and Tag

**Categorize transactions:**

```python
total_income_minor = 0
total_expenses_minor = 0
transfer_count = 0

tag_aggregates = {
    # tag → {amount_minor, count, currency}
}

for txn in transactions:
    if txn.transaction_type == TRANSFER:
        transfer_count += 1
        continue  # Skip for income/expense totals

    if txn.transaction_type == INCOME or txn.amount_minor > 0:
        total_income_minor += txn.amount_minor
        tag_aggregates[txn.tag]["amount_minor"] += txn.amount_minor
        tag_aggregates[txn.tag]["count"] += 1

    elif txn.transaction_type == EXPENSE or txn.amount_minor < 0:
        total_expenses_minor += abs(txn.amount_minor)
        tag_aggregates[txn.tag]["amount_minor"] += abs(txn.amount_minor)
        tag_aggregates[txn.tag]["count"] += 1
```

**Results:**

```python
Income:
- salary: +₹50,000 (1 transaction)

Expenses:
- groceries: -₹2,500 (1 transaction)
- utilities: -₹1,200 (1 transaction)
- dining: -₹800 (1 transaction)

Transfers:
- 2 transactions (debit + credit for one transfer)

Totals:
total_income_minor = 5000000 paise (₹50,000)
total_expenses_minor = 450000 paise (₹4,500)
transfer_count = 2
```

---

### Step 4: Calculate Closing Balance

**Closing balance = Opening balance + All transactions in month**

```python
# Sum ALL transactions in February (including transfers)
all_transactions_sum = (
    +5000000  # salary
    -250000   # groceries
    -120000   # utilities
    -500000   # transfer debit (Checking)
    +500000   # transfer credit (Savings)
    -80000    # dining
) = 4550000 paise (₹45,500)

# Closing balance
opening_balance_minor = 5150000  # ₹51,500
closing_balance_minor = 5150000 + 4550000 = 9700000 paise (₹97,000)
```

**Verification:**

```python
# Account A (Checking):
Opening: ₹51,500 - ₹10,000 (to Savings) = ₹41,500
  (₹51,500 was total, but ₹10,000 was in Savings already from Jan transfer)

Actually, let's recalculate properly:

# After January:
Account A: ₹5,000 + ₹50,000 - ₹2,000 - ₹1,000 - ₹10,000 - ₹500 - ₹3,000 = ₹38,500
Account B: ₹3,000 + ₹10,000 = ₹13,000
Total: ₹51,500 

# After February:
Account A: ₹38,500 + ₹50,000 - ₹2,500 - ₹1,200 - ₹5,000 - ₹800 = ₹79,000
Account B: ₹13,000 + ₹5,000 = ₹18,000
Total: ₹97,000 
```

---

### Step 5: Build Tag Breakdown

**Group by tag and sort:**

```python
tag_breakdown = [
    {"tag": "salary", "total": "50000.00", "count": 1, "currency": "INR"},
    {"tag": "groceries", "total": "-2500.00", "count": 1, "currency": "INR"},
    {"tag": "utilities", "total": "-1200.00", "count": 1, "currency": "INR"},
    {"tag": "dining", "total": "-800.00", "count": 1, "currency": "INR"},
]

# Sort by absolute amount descending
# Result: salary, groceries, utilities, dining
```

---

### Step 6: Build Account Breakdown

**Per-account opening and closing balances:**

```python
for account in accounts:
    # Opening balance (start of Feb)
    opening_balance_minor = (
        account.opening_balance_minor
        + sum(transactions before Feb)
    )

    # Transactions in Feb for this account
    txn_sum_minor = sum(transactions in Feb for this account)

    # Closing balance
    closing_balance_minor = opening_balance_minor + txn_sum_minor
```

**Results:**

```python
Account A (Checking):
  opening_balance: "38500.00"
  closing_balance: "79000.00"
  net_change: "+40500.00"
  transaction_count: 5  # salary, groceries, utilities, transfer out, dining

Account B (Savings):
  opening_balance: "13000.00"
  closing_balance: "18000.00"
  net_change: "+5000.00"
  transaction_count: 1  # transfer in
```

---

### Step 7: Find Top Expenses

**Sort expenses by amount (most negative first):**

```python
# All expense transactions in Feb
expense_transactions = [
    {"amount_minor": -250000, "tag": "groceries", ...},
    {"amount_minor": -120000, "tag": "utilities", ...},
    {"amount_minor": -80000, "tag": "dining", ...},
]

# Sort by amount (most negative = biggest expense)
expense_transactions.sort(key=lambda t: t.amount_minor)

# Take top 5
top_expenses = [
    {
        "id": "txn-uuid",
        "account_name": "Checking",
        "amount": "-2500.00",
        "currency": "INR",
        "tag": "groceries",
        "description": "Weekly shopping",
        "transaction_date": "2026-02-08"
    },
    {
        "id": "txn-uuid",
        "account_name": "Checking",
        "amount": "-1200.00",
        "currency": "INR",
        "tag": "utilities",
        "description": "Electricity bill",
        "transaction_date": "2026-02-12"
    },
    {
        "id": "txn-uuid",
        "account_name": "Checking",
        "amount": "-800.00",
        "currency": "INR",
        "tag": "dining",
        "description": "Restaurant dinner",
        "transaction_date": "2026-02-20"
    }
]
```

---

### Step 8: Build Summary Totals

```python
summary = {
    "total_income": "50000.00",
    "total_expenses": "4500.00",
    "net_savings": "45500.00",  # 50000 - 4500
    "currency": "INR"
}
```

---

### Step 9: Build Period Info

```python
period = {
    "year": 2026,
    "month": 2,
    "month_name": "February",
    "start_date": "2026-02-01",
    "end_date": "2026-02-28"
}
```

---

### Step 10: Return Complete Response

```json
{
  "period": {
    "year": 2026,
    "month": 2,
    "month_name": "February",
    "start_date": "2026-02-01",
    "end_date": "2026-02-28"
  },
  "summary": {
    "total_income": "50000.00",
    "total_expenses": "4500.00",
    "net_savings": "45500.00",
    "currency": "INR"
  },
  "by_tag": [
    {"tag": "salary", "total": "50000.00", "count": 1, "currency": "INR"},
    {"tag": "groceries", "total": "-2500.00", "count": 1, "currency": "INR"},
    {"tag": "utilities", "total": "-1200.00", "count": 1, "currency": "INR"},
    {"tag": "dining", "total": "-800.00", "count": 1, "currency": "INR"}
  ],
  "by_account": [
    {
      "account_id": "account-a-uuid",
      "account_name": "Checking",
      "opening_balance": "38500.00",
      "closing_balance": "79000.00",
      "net_change": "40500.00",
      "currency": "INR",
      "transaction_count": 5
    },
    {
      "account_id": "account-b-uuid",
      "account_name": "Savings",
      "opening_balance": "13000.00",
      "closing_balance": "18000.00",
      "net_change": "5000.00",
      "currency": "INR",
      "transaction_count": 1
    }
  ],
  "top_expenses": [
    {
      "id": "txn-uuid-1",
      "account_name": "Checking",
      "amount": "-2500.00",
      "currency": "INR",
      "tag": "groceries",
      "description": "Weekly shopping",
      "transaction_date": "2026-02-08"
    },
    {
      "id": "txn-uuid-2",
      "account_name": "Checking",
      "amount": "-1200.00",
      "currency": "INR",
      "tag": "utilities",
      "description": "Electricity bill",
      "transaction_date": "2026-02-12"
    },
    {
      "id": "txn-uuid-3",
      "account_name": "Checking",
      "amount": "-800.00",
      "currency": "INR",
      "tag": "dining",
      "description": "Restaurant dinner",
      "transaction_date": "2026-02-20"
    }
  ]
}
```

---

## Data Structures

### Internal Aggregation

**During processing, we use these dictionaries:**

```python
# Map: account_id → opening_balance_minor (for this period)
account_opening_balances: dict[UUID, int] = {
    UUID("account-a"): 3850000,  # ₹38,500
    UUID("account-b"): 1300000,  # ₹13,000
}

# Map: tag → {amount_minor, count, currency}
tag_aggregates: dict[str, dict] = {
    "salary": {"amount_minor": 5000000, "count": 1, "currency": {"INR"}},
    "groceries": {"amount_minor": -250000, "count": 1, "currency": {"INR"}},
    "utilities": {"amount_minor": -120000, "count": 1, "currency": {"INR"}},
    "dining": {"amount_minor": -80000, "count": 1, "currency": {"INR"}},
}

# Map: account_id → {transaction_sum_minor, count}
account_txn_aggregates: dict[UUID, dict] = {
    UUID("account-a"): {"sum_minor": 4050000, "count": 5},
    UUID("account-b"): {"sum_minor": 500000, "count": 1},
}

# List of expense transactions (for top expenses)
expense_transactions: list[Transaction] = [
    Transaction(amount_minor=-250000, tag="groceries", ...),
    Transaction(amount_minor=-120000, "utilities", ...),
    Transaction(amount_minor=-80000, tag="dining", ...),
]
```

---

## Query Performance

### Current Implementation

**Query count:**
```
1. Get all accounts: 1 query
2. Calculate opening balances: N queries (one per account)
3. Get all transactions for month: 1 query
4. Aggregate in-memory: 0 queries
Total: 2 + N queries
```

**For user with 5 accounts:**
```
2 + 5 = 7 queries
```

**Time complexity:**
```
O(N + M) where:
  N = number of accounts
  M = number of transactions in month
```

---

### Optimization Opportunities

#### 1. Batch Opening Balance Calculation

**Current:**
```python
for account in accounts:
    transactions_before = db.query(func.sum(Transaction.amount_minor)).filter(
        Transaction.account_id == account.id,
        Transaction.transaction_date < start_date,
    ).scalar()
    # N queries!
```

**Optimized:**
```python
# Single query with GROUP BY
opening_balances = (
    db.query(
        Transaction.account_id,
        func.sum(Transaction.amount_minor).label('sum')
    )
    .filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_date < start_date,
    )
    .group_by(Transaction.account_id)
    .all()
)
# 1 query for all accounts!
```

**Improvement:** N queries → 1 query

#### 2. Add Database Indexes

```sql
-- For opening balance calculation
CREATE INDEX idx_transactions_account_date
ON transactions (account_id, transaction_date);

-- For monthly transaction retrieval
CREATE INDEX idx_transactions_user_date
ON transactions (user_id, transaction_date);

-- For tag aggregation
CREATE INDEX idx_transactions_tag
ON transactions (tag);
```

#### 3. Cached Summaries (Future)

**ADR-004 decision:** No cached summaries in MVP

**Future optimization:**
```python
class MonthlySummaryCache(Base):
    user_id: UUID
    year: int
    month: int
    summary_json: str  # Cached JSON blob
    last_updated: datetime

# Invalidate on transaction create/update/delete
# Regenerate on first access
```

**Benefits:**
- O(1) query for cached summaries
- Instant response for historical months

**Drawbacks:**
- Cache invalidation complexity
- Stale data risk
- More storage needed

---

## Examples

### Example 1: Multi-Currency User

**User has:**
- Account A (INR)
- Account B (USD)

**February transactions:**
```
Feb 1: +₹50,000 salary (INR, Account A)
Feb 5: -₹2,000 groceries (INR, Account A)
Feb 10: +$500 income (USD, Account B)
Feb 15: -$100 expense (USD, Account B)
```

**Summary response:**
```json
{
  "summary": {
    "total_income": "...",
    "total_expenses": "...",
    "net_savings": "...",
    "currency": "MIXED"  // Multiple currencies!
  },
  "by_tag": [
    {"tag": "salary", "total": "50000.00", "count": 1, "currency": "INR"},
    {"tag": "income", "total": "500.00", "count": 1, "currency": "USD"},
    {"tag": "groceries", "total": "-2000.00", "count": 1, "currency": "INR"},
    {"tag": "expense", "total": "-100.00", "count": 1, "currency": "USD"}
  ]
}
```

**With currency filter:**
```
GET /summary/monthly?year=2026&month=2&currency=INR
```

**Response:**
```json
{
  "summary": {
    "total_income": "50000.00",
    "total_expenses": "2000.00",
    "net_savings": "48000.00",
    "currency": "INR"  // Single currency
  },
  "by_tag": [
    {"tag": "salary", "total": "50000.00", "count": 1, "currency": "INR"},
    {"tag": "groceries", "total": "-2000.00", "count": 1, "currency": "INR"}
  ]
}
```

---

### Example 2: No Transactions

**User has accounts but no transactions in month:**

**Response:**
```json
{
  "period": {
    "year": 2026,
    "month": 3,
    "month_name": "March",
    "start_date": "2026-03-01",
    "end_date": "2026-03-31"
  },
  "summary": {
    "total_income": "0.00",
    "total_expenses": "0.00",
    "net_savings": "0.00",
    "currency": "INR"
  },
  "by_tag": [],
  "by_account": [
    {
      "account_id": "...",
      "account_name": "Checking",
      "opening_balance": "79000.00",
      "closing_balance": "79000.00",
      "net_change": "0.00",
      "currency": "INR",
      "transaction_count": 0
    }
  ],
  "top_expenses": []
}
```

---

### Example 3: Only Transfers

**User only transferred money between accounts:**

**February transactions:**
```
Feb 5: Transfer ₹10,000 from Checking to Savings
Feb 15: Transfer ₹5,000 from Savings to Checking
```

**Response:**
```json
{
  "summary": {
    "total_income": "0.00",
    "total_expenses": "0.00",
    "net_savings": "0.00",
    "currency": "INR"
  },
  "by_tag": [],
  "by_account": [
    {
      "account_name": "Checking",
      "opening_balance": "38500.00",
      "closing_balance": "33500.00",  // -10k +5k
      "net_change": "-5000.00",
      "transaction_count": 2
    },
    {
      "account_name": "Savings",
      "opening_balance": "13000.00",
      "closing_balance": "18000.00",  // +10k -5k
      "net_change": "5000.00",
      "transaction_count": 2
    }
  ],
  "top_expenses": []
}
```

**Note:** Total balance unchanged (₹51,500), just redistributed.

---

## Summary

### Key Principles

1. **No cached data:** All summaries derived from transactions
2. **Transfers excluded:** From income/expense totals
3. **Opening balance:** Calculated from account openings + prior transactions
4. **Closing balance:** Opening + all transactions in month (including transfers)
5. **Multi-currency:** Handled with "MIXED" or filter by currency

### Performance Characteristics

- **Query count:** O(2 + N) where N = number of accounts
- **Time complexity:** O(N + M) where M = transactions in month
- **Optimization:** Can reduce to O(3) queries with batching

### Future Enhancements

- Cached summaries for historical months
- Database-level aggregation (GROUP BY)
- Year-to-date summaries
- Trend analysis across months

---

## Implementation Location

**Endpoint:** [routers/summary.py:33-369](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/summary.py#L33-L369)

**Schemas:** [schemas/summary.py](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/schemas/summary.py)

**API Contract:** [api-contracts.md#5-get-summarymonthly](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/docs/backend/api-contracts.md#5-get-summarymonthly)
