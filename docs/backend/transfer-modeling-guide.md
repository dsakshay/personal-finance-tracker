# Transfer Modeling Guide

## Overview

This document explains why transfers are modeled as **two separate transactions** instead of a single transaction, and how **atomicity** prevents money loss or duplication.

---

## The Transfer Problem

### What is a Transfer?

A transfer moves money from one account to another:

```
Account A (Checking):     ₹10,000
                           ↓ Transfer ₹1,000
Account B (Savings):      ₹5,000

After transfer:
Account A (Checking):     ₹9,000  (decreased by ₹1,000)
Account B (Savings):      ₹6,000  (increased by ₹1,000)
```

### Design Question: How to Model This?

**Option 1: Single Transaction** ❌
```
Transaction:
  amount: ₹1,000
  from_account: A
  to_account: B
```

**Problems:**
- How does this affect account balances?
- `SELECT SUM(amount) FROM transactions WHERE account_id = A` doesn't work
- Need special logic to handle transfers differently
- Balance calculation becomes complex

**Option 2: Two Linked Transactions** ✅
```
Transaction 1 (Debit):
  account_id: A
  amount: -₹1,000
  related_account_id: B

Transaction 2 (Credit):
  account_id: B
  amount: +₹1,000
  related_account_id: A
```

**Benefits:**
- Each account has its own transaction record
- Balance calculation is always: `opening_balance + SUM(amounts)`
- No special cases for transfers
- Double-entry bookkeeping principles

---

## Why Two Transactions?

### 1. Consistent Balance Calculation

**With two transactions:**

```python
# Account A balance:
opening_balance_A = 10000  # ₹10,000
transactions_A = [-1000]    # Transfer out
current_balance_A = 10000 + (-1000) = 9000  # ✅ Correct

# Account B balance:
opening_balance_B = 5000   # ₹5,000
transactions_B = [+1000]   # Transfer in
current_balance_B = 5000 + 1000 = 6000  # ✅ Correct
```

**SQL is simple:**
```sql
-- Balance for any account (income, expense, transfer - all the same)
SELECT opening_balance_minor + COALESCE(SUM(amount_minor), 0)
FROM accounts a
LEFT JOIN transactions t ON t.account_id = a.id
WHERE a.id = ?
GROUP BY a.id;
```

**With single transaction:**
```python
# Would need complex logic:
if transaction.type == TRANSFER:
    if transaction.from_account == account_id:
        balance -= transaction.amount  # Subtract
    elif transaction.to_account == account_id:
        balance += transaction.amount  # Add
else:
    balance += transaction.amount  # Regular logic
```

### 2. Transaction History Per Account

**Each account has complete history:**

```python
# Account A transactions:
GET /transactions?account_id=A

[
  {"date": "2026-01-12", "amount": "-1000.00", "type": "transfer", "related": "B"},
  {"date": "2026-01-10", "amount": "-500.00", "type": "expense", "tag": "groceries"},
  {"date": "2026-01-01", "amount": "50000.00", "type": "income", "tag": "salary"},
]

# All transactions affecting Account A are visible
# No need to query "other accounts" to see impact
```

### 3. Audit Trail and Transparency

**Users see money leaving AND arriving:**

```
User's account list:
- Checking (A):  Shows -₹1,000 (outgoing transfer to Savings)
- Savings (B):   Shows +₹1,000 (incoming transfer from Checking)

vs. single transaction:
- Where does it show up? In Checking? Savings? Both?
- How do you display it differently in each account's view?
```

### 4. Double-Entry Bookkeeping

**Accounting principle:** Every transaction has equal and opposite effects

```
Traditional accounting:
  Debit: Checking Account    ₹1,000 (decrease asset)
  Credit: Savings Account    ₹1,000 (increase asset)

Our implementation:
  Transaction 1: Checking    -₹1,000 (debit)
  Transaction 2: Savings     +₹1,000 (credit)
```

**Verification:**
```python
# For any transfer, verify:
debit_transaction.amount + credit_transaction.amount == 0

# Example:
-1000 + 1000 = 0  ✅ Balanced
```

### 5. Related Account Tracking

**linked via `related_account_id`:**

```python
# From transaction, navigate to the other side:
transfer_out = Transaction(
    account_id="A",
    amount=-1000,
    related_account_id="B",  # Points to destination
)

transfer_in = Transaction(
    account_id="B",
    amount=1000,
    related_account_id="A",  # Points to source
)

# Frontend can display:
"Transfer to Savings (B)"  # From transfer_out.related_account
"Transfer from Checking (A)"  # From transfer_in.related_account
```

---

## Atomicity: Preventing Money Loss

### The Problem

**What if we create two transactions separately?**

```python
# ❌ DANGEROUS: Non-atomic approach
debit = Transaction(account_id=A, amount=-1000)
db.add(debit)
db.commit()  # ⚠️ Committed!

# 💥 Server crashes here!

credit = Transaction(account_id=B, amount=1000)
db.add(credit)
db.commit()  # Never reached!
```

**Result:**
- Debit transaction saved: Account A lost ₹1,000 ❌
- Credit transaction NOT saved: Account B never received ₹1,000 ❌
- **Money disappeared!** 💸

### The Solution: Atomic Transactions

**Database Transaction:** All-or-nothing operation

```python
# ✅ SAFE: Atomic approach
try:
    # Start transaction (implicit with SQLAlchemy session)
    debit = Transaction(account_id=A, amount=-1000)
    credit = Transaction(account_id=B, amount=1000)

    db.add(debit)
    db.add(credit)

    # Single commit: Both or neither
    db.commit()  # ✅ Both saved together

except Exception as e:
    db.rollback()  # ❌ Neither saved
    raise
```

**Result:**
- If commit succeeds: Both transactions saved ✅
- If any error occurs: Both transactions rolled back ✅
- **Money never lost or duplicated!** 💰

### Database Transaction Guarantees (ACID)

#### A - Atomicity
**All or nothing:** Both transactions are saved together, or both are discarded.

```python
# Case 1: Success
db.commit()
# → Both debit and credit saved ✅

# Case 2: Failure (constraint violation, network error, etc.)
db.commit()  # Raises exception
# → Automatic rollback, both discarded ✅

# Case 3: Explicit rollback
db.rollback()
# → Both discarded ✅
```

#### C - Consistency
**Database remains valid:** No broken constraints.

```python
# Foreign key constraints enforced:
debit = Transaction(account_id="INVALID_UUID", ...)
credit = Transaction(account_id=B, ...)

db.commit()
# → IntegrityError: Foreign key violation
# → Automatic rollback, BOTH discarded ✅
```

#### I - Isolation
**Concurrent transfers don't interfere:**

```
User A transfers ₹1,000: A → B
User B transfers ₹500:  A → C

Both happen at same time (concurrently)

Database ensures:
- User A sees consistent state (A, B balances)
- User B sees consistent state (A, C balances)
- No partial states visible
```

#### D - Durability
**Once committed, data persists:**

```python
db.commit()
# → Data written to disk
# → Even if server crashes immediately after, data is safe ✅
```

---

## Implementation Details

### Code Location

[routers/transactions.py:284-328](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/transactions.py#L284-L328)

### Step-by-Step Flow

#### Step 1: Validation

```python
# Prevent future transfers
if transfer_data.transaction_date > today:
    raise HTTPException(400, "Cannot transfer in the future")

# Prevent same-account transfers
if from_account_id == to_account_id:
    raise HTTPException(400, "Cannot transfer to same account")
```

#### Step 2: Authorization

```python
# Both accounts must belong to current user
from_account = db.query(Account).filter(
    Account.id == from_account_id,
    Account.user_id == current_user.id,  # 🔒 Security!
).first()

to_account = db.query(Account).filter(
    Account.id == to_account_id,
    Account.user_id == current_user.id,  # 🔒 Security!
).first()

if not from_account or not to_account:
    raise HTTPException(404, "Account(s) not found")
```

**Why both must belong to same user:**
- Prevent stealing money from other users!
- User A cannot transfer from User B's account to User A's account
- Authorization check happens BEFORE any database changes

#### Step 3: Currency Validation

```python
# Currencies must match
if from_account.currency != to_account.currency:
    raise HTTPException(400, f"Currency mismatch: {from_account.currency} ≠ {to_account.currency}")

if transfer_currency != from_account.currency:
    raise HTTPException(400, f"Transfer currency must match accounts")
```

**Why:**
- Cannot transfer ₹1,000 from INR account to USD account
- Prevents currency conversion issues (out of scope for MVP)
- Future enhancement: Support multi-currency transfers with exchange rates

#### Step 4: Create Both Transactions

```python
# Transaction 1: Debit (money leaving source account)
debit = Transaction(
    user_id=current_user.id,
    account_id=from_account_id,
    amount_minor=-amount_minor,  # Negative!
    currency=currency,
    transaction_type=TransactionType.TRANSFER,
    related_account_id=to_account_id,  # Link to destination
    ...
)

# Transaction 2: Credit (money arriving at destination account)
credit = Transaction(
    user_id=current_user.id,
    account_id=to_account_id,
    amount_minor=amount_minor,  # Positive!
    currency=currency,
    transaction_type=TransactionType.TRANSFER,
    related_account_id=from_account_id,  # Link to source
    ...
)
```

**Key points:**
- `amount_minor` is negative for debit, positive for credit
- `related_account_id` creates bidirectional link
- Both have same `user_id`, `currency`, `transaction_date`, `description`

#### Step 5: Atomic Commit

```python
try:
    # Add both to session (staged, not yet in database)
    db.add(debit)
    db.add(credit)

    # Commit both together (ATOMIC!)
    db.commit()

    # Refresh to get generated IDs and timestamps
    db.refresh(debit)
    db.refresh(credit)

    return [debit, credit]

except IntegrityError as e:
    # Automatic rollback on error
    db.rollback()
    raise HTTPException(400, f"Database error: {e}")
```

**What happens during commit:**

```sql
-- PostgreSQL executes:
BEGIN;  -- Start transaction

INSERT INTO transactions (id, user_id, account_id, amount_minor, ...)
VALUES (
  'uuid-debit',
  'user-id',
  'account-A',
  -100000,  -- -₹1,000
  ...
);

INSERT INTO transactions (id, user_id, account_id, amount_minor, ...)
VALUES (
  'uuid-credit',
  'user-id',
  'account-B',
  100000,  -- +₹1,000
  ...
);

COMMIT;  -- Both saved together!
-- OR
ROLLBACK;  -- Both discarded together!
```

---

## Failure Scenarios

### Scenario 1: Network Failure During Commit

**What happens:**
```python
db.add(debit)
db.add(credit)
db.commit()  # Network error!
# → PostgreSQL never receives commit
# → Automatic rollback after timeout
# → Both transactions discarded ✅
```

**Result:** No money moved, both accounts unchanged ✅

### Scenario 2: Constraint Violation

**What happens:**
```python
debit = Transaction(account_id="INVALID", ...)  # Invalid foreign key
credit = Transaction(account_id=B, ...)

db.add(debit)
db.add(credit)
db.commit()  # IntegrityError!
# → PostgreSQL rejects invalid debit
# → Automatic rollback
# → Credit is also discarded ✅
```

**Result:** Neither transaction saved, both accounts unchanged ✅

### Scenario 3: Server Crash After Commit

**What happens:**
```python
db.commit()  # ✅ Success!
# Data written to PostgreSQL
# 💥 Server crashes here!

# Later, server restarts:
# → PostgreSQL has both transactions ✅
# → Data is durable (ACID: Durability)
```

**Result:** Both transactions saved, transfer completed ✅

### Scenario 4: Concurrent Transfers

**What happens:**
```
Time  | User A (Transfer A→B ₹1,000)    | User B (Transfer A→C ₹500)
------|----------------------------------|---------------------------
T1    | Read Account A: ₹10,000         |
T2    |                                  | Read Account A: ₹10,000
T3    | Create debit: A -₹1,000          |
T4    | Create credit: B +₹1,000         |
T5    |                                  | Create debit: A -₹500
T6    |                                  | Create credit: C +₹500
T7    | COMMIT (both saved)              |
T8    |                                  | COMMIT (both saved)
```

**Result:**
- Account A: ₹10,000 - ₹1,000 - ₹500 = ₹8,500 ✅
- Account B: +₹1,000 ✅
- Account C: +₹500 ✅
- Total: ₹10,000 = ₹8,500 + ₹1,000 + ₹500 ✅ Balanced!

**Database isolation ensures:**
- No lost updates
- No dirty reads
- Consistent state throughout

---

## Verification and Auditing

### 1. Transfer Pair Verification

**Check that transfers are balanced:**

```sql
-- Find all transfer transactions
SELECT
  t1.id as debit_id,
  t1.account_id as from_account,
  t1.amount_minor as debit_amount,
  t2.id as credit_id,
  t2.account_id as to_account,
  t2.amount_minor as credit_amount,
  (t1.amount_minor + t2.amount_minor) as balance
FROM transactions t1
JOIN transactions t2 ON t1.related_account_id = t2.account_id
  AND t2.related_account_id = t1.account_id
WHERE t1.transaction_type = 'transfer'
  AND t2.transaction_type = 'transfer'
  AND t1.amount_minor < 0  -- Debit only
HAVING (t1.amount_minor + t2.amount_minor) != 0;

-- Should return 0 rows! (all balanced)
```

### 2. Orphaned Transfer Detection

**Find transfers without pairs:**

```sql
-- Transfers without matching pair (should never happen!)
SELECT *
FROM transactions t1
WHERE t1.transaction_type = 'transfer'
  AND t1.related_account_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1
    FROM transactions t2
    WHERE t2.account_id = t1.related_account_id
      AND t2.related_account_id = t1.account_id
      AND t2.transaction_type = 'transfer'
  );

-- Should return 0 rows!
```

### 3. Account Balance Verification

**Verify total money in system:**

```sql
-- Sum of all balances should equal sum of opening balances
SELECT
  SUM(opening_balance_minor) as total_opening,
  SUM(opening_balance_minor + COALESCE(txn_sum, 0)) as total_current
FROM accounts a
LEFT JOIN (
  SELECT account_id, SUM(amount_minor) as txn_sum
  FROM transactions
  GROUP BY account_id
) t ON t.account_id = a.id;

-- total_opening should equal total_current
-- (transfers don't create or destroy money!)
```

---

## Common Pitfalls (Avoided by Our Design)

### ❌ Pitfall 1: Separate API Calls

**Bad approach:**
```javascript
// Frontend makes two calls:
await fetch('/transactions', {
  method: 'POST',
  body: JSON.stringify({ account_id: A, amount: -1000 })
});

// 💥 Network error here!

await fetch('/transactions', {
  method: 'POST',
  body: JSON.stringify({ account_id: B, amount: 1000 })
});
```

**Problem:** First call succeeds, second fails → Money lost!

**Our solution:** Single API call `/transactions/transfer` creates both atomically

### ❌ Pitfall 2: Separate Commits

**Bad approach:**
```python
# Create debit
db.add(debit)
db.commit()  # ⚠️ First commit

# Create credit
db.add(credit)
db.commit()  # ⚠️ Second commit
```

**Problem:** First commit succeeds, second fails → Money lost!

**Our solution:** Single `db.commit()` for both transactions

### ❌ Pitfall 3: No Validation

**Bad approach:**
```python
# Skip currency check
debit = Transaction(account_id=A, currency="INR", amount=-1000)
credit = Transaction(account_id=B, currency="USD", amount=1000)
db.commit()
```

**Problem:** Transfer between incompatible currencies!

**Our solution:** Validate currencies match BEFORE creating transactions

### ❌ Pitfall 4: No Authorization Check

**Bad approach:**
```python
# Skip ownership check
from_account = db.get(Account, from_account_id)  # Any user's account!
to_account = db.get(Account, to_account_id)      # Any user's account!
```

**Problem:** User A can transfer money out of User B's account!

**Our solution:** Verify BOTH accounts belong to current user

---

## Benefits Summary

### For Users

✅ **Accurate balances:** Each account shows correct balance
✅ **Complete history:** See all money in/out of each account
✅ **Clear audit trail:** "Transfer to Savings" vs "Transfer from Checking"
✅ **No money loss:** Atomicity prevents partial transfers

### For Developers

✅ **Simple queries:** Balance = `SUM(amounts)` always works
✅ **No special cases:** Transfers handled like any transaction
✅ **Type safety:** Enum prevents invalid transfer types
✅ **Easy debugging:** Two separate records to inspect

### For Business

✅ **Compliance:** Double-entry bookkeeping standard
✅ **Auditability:** Clear money trail
✅ **Reliability:** ACID guarantees prevent errors
✅ **Scalability:** No complex locking needed

---

## Future Enhancements

### 1. Multi-Currency Transfers

```python
# Transfer with exchange rate
transfer = Transfer(
    from_account_id=A,  # INR account
    to_account_id=B,    # USD account
    from_amount=8300,   # ₹8,300
    to_amount=100,      # $100
    exchange_rate=83.0, # 1 USD = 83 INR
)

# Creates:
# - Debit:  A, -8300 INR
# - Credit: B, +100 USD
```

### 2. Transfer Reversal

```python
# Create reverse transactions
def reverse_transfer(original_transfer_id):
    # Find original pair
    original_debit, original_credit = get_transfer_pair(original_transfer_id)

    # Create opposite transactions
    reversal_debit = create_opposite(original_credit)
    reversal_credit = create_opposite(original_debit)

    # Link to originals
    reversal_debit.reversal_of = original_debit.id
    reversal_credit.reversal_of = original_credit.id

    # Commit atomically
    db.commit()
```

### 3. Transfer Scheduling

```python
# Schedule future transfer
scheduled_transfer = ScheduledTransfer(
    from_account=A,
    to_account=B,
    amount=1000,
    execute_date="2026-02-01",  # Future date
    recurrence="monthly",
)

# Cron job executes on date:
if scheduled_transfer.execute_date == today:
    create_transfer(...)  # Atomic execution
```

---

## Conclusion

**Why two transactions:**
1. Consistent balance calculation
2. Complete per-account history
3. Follows accounting principles
4. Simpler implementation

**How atomicity prevents money loss:**
1. Both transactions created in single database transaction
2. Either both save (success) or both rollback (failure)
3. No partial states possible
4. ACID guarantees by PostgreSQL

**Key takeaway:**
> Transfers are not a special case—they're just two regular transactions that happen to be linked and created atomically.

This design is:
- ✅ Simple to implement
- ✅ Easy to reason about
- ✅ Impossible to lose money
- ✅ Follows industry standards

---

## Further Reading

- [Double-Entry Bookkeeping](https://en.wikipedia.org/wiki/Double-entry_bookkeeping)
- [ACID Properties](https://en.wikipedia.org/wiki/ACID)
- [Database Transactions](https://www.postgresql.org/docs/current/tutorial-transactions.html)
- [ADR-006: Transfer Representation](../adrs/006-transfer-representation.md) (if exists)
