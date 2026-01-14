 Transfer Modeling Guide

 Overview

This document explains why transfers are modeled as two separate transactions instead of a single transaction, and how atomicity prevents money loss or duplication.

---

 The Transfer Problem

 What is a Transfer?

A transfer moves money from one account to another:

```
Account A (Checking):     ₹,
                           ↓ Transfer ₹,
Account B (Savings):      ₹,

After transfer:
Account A (Checking):     ₹,  (decreased by ₹,)
Account B (Savings):      ₹,  (increased by ₹,)
```

 Design Question: How to Model This?

Option : Single Transaction 
```
Transaction:
  amount: ₹,
  from_account: A
  to_account: B
```

Problems:
- How does this affect account balances?
- `SELECT SUM(amount) FROM transactions WHERE account_id = A` doesn't work
- Need special logic to handle transfers differently
- Balance calculation becomes complex

Option : Two Linked Transactions 
```
Transaction  (Debit):
  account_id: A
  amount: -₹,
  related_account_id: B

Transaction  (Credit):
  account_id: B
  amount: +₹,
  related_account_id: A
```

Benefits:
- Each account has its own transaction record
- Balance calculation is always: `opening_balance + SUM(amounts)`
- No special cases for transfers
- Double-entry bookkeeping principles

---

 Why Two Transactions?

 . Consistent Balance Calculation

With two transactions:

```python
 Account A balance:
opening_balance_A =    ₹,
transactions_A = [-]     Transfer out
current_balance_A =  + (-) =     Correct

 Account B balance:
opening_balance_B =     ₹,
transactions_B = [+]    Transfer in
current_balance_B =  +  =     Correct
```

SQL is simple:
```sql
-- Balance for any account (income, expense, transfer - all the same)
SELECT opening_balance_minor + COALESCE(SUM(amount_minor), )
FROM accounts a
LEFT JOIN transactions t ON t.account_id = a.id
WHERE a.id = ?
GROUP BY a.id;
```

With single transaction:
```python
 Would need complex logic:
if transaction.type == TRANSFER:
    if transaction.from_account == account_id:
        balance -= transaction.amount   Subtract
    elif transaction.to_account == account_id:
        balance += transaction.amount   Add
else:
    balance += transaction.amount   Regular logic
```

 . Transaction History Per Account

Each account has complete history:

```python
 Account A transactions:
GET /transactions?account_id=A

[
  {"date": "--", "amount": "-.", "type": "transfer", "related": "B"},
  {"date": "--", "amount": "-.", "type": "expense", "tag": "groceries"},
  {"date": "--", "amount": ".", "type": "income", "tag": "salary"},
]

 All transactions affecting Account A are visible
 No need to query "other accounts" to see impact
```

 . Audit Trail and Transparency

Users see money leaving AND arriving:

```
User's account list:
- Checking (A):  Shows -₹, (outgoing transfer to Savings)
- Savings (B):   Shows +₹, (incoming transfer from Checking)

vs. single transaction:
- Where does it show up? In Checking? Savings? Both?
- How do you display it differently in each account's view?
```

 . Double-Entry Bookkeeping

Accounting principle: Every transaction has equal and opposite effects

```
Traditional accounting:
  Debit: Checking Account    ₹, (decrease asset)
  Credit: Savings Account    ₹, (increase asset)

Our implementation:
  Transaction : Checking    -₹, (debit)
  Transaction : Savings     +₹, (credit)
```

Verification:
```python
 For any transfer, verify:
debit_transaction.amount + credit_transaction.amount == 

 Example:
- +  =    Balanced
```

 . Related Account Tracking

linked via `related_account_id`:

```python
 From transaction, navigate to the other side:
transfer_out = Transaction(
    account_id="A",
    amount=-,
    related_account_id="B",   Points to destination
)

transfer_in = Transaction(
    account_id="B",
    amount=,
    related_account_id="A",   Points to source
)

 Frontend can display:
"Transfer to Savings (B)"   From transfer_out.related_account
"Transfer from Checking (A)"   From transfer_in.related_account
```

---

 Atomicity: Preventing Money Loss

 The Problem

What if we create two transactions separately?

```python
  DANGEROUS: Non-atomic approach
debit = Transaction(account_id=A, amount=-)
db.add(debit)
db.commit()   ️ Committed!

  Server crashes here!

credit = Transaction(account_id=B, amount=)
db.add(credit)
db.commit()   Never reached!
```

Result:
- Debit transaction saved: Account A lost ₹, 
- Credit transaction NOT saved: Account B never received ₹, 
- Money disappeared! 

 The Solution: Atomic Transactions

Database Transaction: All-or-nothing operation

```python
  SAFE: Atomic approach
try:
     Start transaction (implicit with SQLAlchemy session)
    debit = Transaction(account_id=A, amount=-)
    credit = Transaction(account_id=B, amount=)

    db.add(debit)
    db.add(credit)

     Single commit: Both or neither
    db.commit()    Both saved together

except Exception as e:
    db.rollback()    Neither saved
    raise
```

Result:
- If commit succeeds: Both transactions saved 
- If any error occurs: Both transactions rolled back 
- Money never lost or duplicated! 

 Database Transaction Guarantees (ACID)

 A - Atomicity
All or nothing: Both transactions are saved together, or both are discarded.

```python
 Case : Success
db.commit()
 → Both debit and credit saved 

 Case : Failure (constraint violation, network error, etc.)
db.commit()   Raises exception
 → Automatic rollback, both discarded 

 Case : Explicit rollback
db.rollback()
 → Both discarded 
```

 C - Consistency
Database remains valid: No broken constraints.

```python
 Foreign key constraints enforced:
debit = Transaction(account_id="INVALID_UUID", ...)
credit = Transaction(account_id=B, ...)

db.commit()
 → IntegrityError: Foreign key violation
 → Automatic rollback, BOTH discarded 
```

 I - Isolation
Concurrent transfers don't interfere:

```
User A transfers ₹,: A → B
User B transfers ₹:  A → C

Both happen at same time (concurrently)

Database ensures:
- User A sees consistent state (A, B balances)
- User B sees consistent state (A, C balances)
- No partial states visible
```

 D - Durability
Once committed, data persists:

```python
db.commit()
 → Data written to disk
 → Even if server crashes immediately after, data is safe 
```

---

 Implementation Details

 Code Location

[routers/transactions.py:-](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/transactions.pyL-L)

 Step-by-Step Flow

 Step : Validation

```python
 Prevent future transfers
if transfer_data.transaction_date > today:
    raise HTTPException(, "Cannot transfer in the future")

 Prevent same-account transfers
if from_account_id == to_account_id:
    raise HTTPException(, "Cannot transfer to same account")
```

 Step : Authorization

```python
 Both accounts must belong to current user
from_account = db.query(Account).filter(
    Account.id == from_account_id,
    Account.user_id == current_user.id,    Security!
).first()

to_account = db.query(Account).filter(
    Account.id == to_account_id,
    Account.user_id == current_user.id,    Security!
).first()

if not from_account or not to_account:
    raise HTTPException(, "Account(s) not found")
```

Why both must belong to same user:
- Prevent stealing money from other users!
- User A cannot transfer from User B's account to User A's account
- Authorization check happens BEFORE any database changes

 Step : Currency Validation

```python
 Currencies must match
if from_account.currency != to_account.currency:
    raise HTTPException(, f"Currency mismatch: {from_account.currency} ≠ {to_account.currency}")

if transfer_currency != from_account.currency:
    raise HTTPException(, f"Transfer currency must match accounts")
```

Why:
- Cannot transfer ₹, from INR account to USD account
- Prevents currency conversion issues (out of scope for MVP)
- Future enhancement: Support multi-currency transfers with exchange rates

 Step : Create Both Transactions

```python
 Transaction : Debit (money leaving source account)
debit = Transaction(
    user_id=current_user.id,
    account_id=from_account_id,
    amount_minor=-amount_minor,   Negative!
    currency=currency,
    transaction_type=TransactionType.TRANSFER,
    related_account_id=to_account_id,   Link to destination
    ...
)

 Transaction : Credit (money arriving at destination account)
credit = Transaction(
    user_id=current_user.id,
    account_id=to_account_id,
    amount_minor=amount_minor,   Positive!
    currency=currency,
    transaction_type=TransactionType.TRANSFER,
    related_account_id=from_account_id,   Link to source
    ...
)
```

Key points:
- `amount_minor` is negative for debit, positive for credit
- `related_account_id` creates bidirectional link
- Both have same `user_id`, `currency`, `transaction_date`, `description`

 Step : Atomic Commit

```python
try:
     Add both to session (staged, not yet in database)
    db.add(debit)
    db.add(credit)

     Commit both together (ATOMIC!)
    db.commit()

     Refresh to get generated IDs and timestamps
    db.refresh(debit)
    db.refresh(credit)

    return [debit, credit]

except IntegrityError as e:
     Automatic rollback on error
    db.rollback()
    raise HTTPException(, f"Database error: {e}")
```

What happens during commit:

```sql
-- PostgreSQL executes:
BEGIN;  -- Start transaction

INSERT INTO transactions (id, user_id, account_id, amount_minor, ...)
VALUES (
  'uuid-debit',
  'user-id',
  'account-A',
  -,  -- -₹,
  ...
);

INSERT INTO transactions (id, user_id, account_id, amount_minor, ...)
VALUES (
  'uuid-credit',
  'user-id',
  'account-B',
  ,  -- +₹,
  ...
);

COMMIT;  -- Both saved together!
-- OR
ROLLBACK;  -- Both discarded together!
```

---

 Failure Scenarios

 Scenario : Network Failure During Commit

What happens:
```python
db.add(debit)
db.add(credit)
db.commit()   Network error!
 → PostgreSQL never receives commit
 → Automatic rollback after timeout
 → Both transactions discarded 
```

Result: No money moved, both accounts unchanged 

 Scenario : Constraint Violation

What happens:
```python
debit = Transaction(account_id="INVALID", ...)   Invalid foreign key
credit = Transaction(account_id=B, ...)

db.add(debit)
db.add(credit)
db.commit()   IntegrityError!
 → PostgreSQL rejects invalid debit
 → Automatic rollback
 → Credit is also discarded 
```

Result: Neither transaction saved, both accounts unchanged 

 Scenario : Server Crash After Commit

What happens:
```python
db.commit()    Success!
 Data written to PostgreSQL
  Server crashes here!

 Later, server restarts:
 → PostgreSQL has both transactions 
 → Data is durable (ACID: Durability)
```

Result: Both transactions saved, transfer completed 

 Scenario : Concurrent Transfers

What happens:
```
Time  | User A (Transfer A→B ₹,)    | User B (Transfer A→C ₹)
------|----------------------------------|---------------------------
T    | Read Account A: ₹,         |
T    |                                  | Read Account A: ₹,
T    | Create debit: A -₹,          |
T    | Create credit: B +₹,         |
T    |                                  | Create debit: A -₹
T    |                                  | Create credit: C +₹
T    | COMMIT (both saved)              |
T    |                                  | COMMIT (both saved)
```

Result:
- Account A: ₹, - ₹, - ₹ = ₹, 
- Account B: +₹, 
- Account C: +₹ 
- Total: ₹, = ₹, + ₹, + ₹  Balanced!

Database isolation ensures:
- No lost updates
- No dirty reads
- Consistent state throughout

---

 Verification and Auditing

 . Transfer Pair Verification

Check that transfers are balanced:

```sql
-- Find all transfer transactions
SELECT
  t.id as debit_id,
  t.account_id as from_account,
  t.amount_minor as debit_amount,
  t.id as credit_id,
  t.account_id as to_account,
  t.amount_minor as credit_amount,
  (t.amount_minor + t.amount_minor) as balance
FROM transactions t
JOIN transactions t ON t.related_account_id = t.account_id
  AND t.related_account_id = t.account_id
WHERE t.transaction_type = 'transfer'
  AND t.transaction_type = 'transfer'
  AND t.amount_minor <   -- Debit only
HAVING (t.amount_minor + t.amount_minor) != ;

-- Should return  rows! (all balanced)
```

 . Orphaned Transfer Detection

Find transfers without pairs:

```sql
-- Transfers without matching pair (should never happen!)
SELECT 
FROM transactions t
WHERE t.transaction_type = 'transfer'
  AND t.related_account_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 
    FROM transactions t
    WHERE t.account_id = t.related_account_id
      AND t.related_account_id = t.account_id
      AND t.transaction_type = 'transfer'
  );

-- Should return  rows!
```

 . Account Balance Verification

Verify total money in system:

```sql
-- Sum of all balances should equal sum of opening balances
SELECT
  SUM(opening_balance_minor) as total_opening,
  SUM(opening_balance_minor + COALESCE(txn_sum, )) as total_current
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

 Common Pitfalls (Avoided by Our Design)

  Pitfall : Separate API Calls

Bad approach:
```javascript
// Frontend makes two calls:
await fetch('/transactions', {
  method: 'POST',
  body: JSON.stringify({ account_id: A, amount: - })
});

//  Network error here!

await fetch('/transactions', {
  method: 'POST',
  body: JSON.stringify({ account_id: B, amount:  })
});
```

Problem: First call succeeds, second fails → Money lost!

Our solution: Single API call `/transactions/transfer` creates both atomically

  Pitfall : Separate Commits

Bad approach:
```python
 Create debit
db.add(debit)
db.commit()   ️ First commit

 Create credit
db.add(credit)
db.commit()   ️ Second commit
```

Problem: First commit succeeds, second fails → Money lost!

Our solution: Single `db.commit()` for both transactions

  Pitfall : No Validation

Bad approach:
```python
 Skip currency check
debit = Transaction(account_id=A, currency="INR", amount=-)
credit = Transaction(account_id=B, currency="USD", amount=)
db.commit()
```

Problem: Transfer between incompatible currencies!

Our solution: Validate currencies match BEFORE creating transactions

  Pitfall : No Authorization Check

Bad approach:
```python
 Skip ownership check
from_account = db.get(Account, from_account_id)   Any user's account!
to_account = db.get(Account, to_account_id)       Any user's account!
```

Problem: User A can transfer money out of User B's account!

Our solution: Verify BOTH accounts belong to current user

---

 Benefits Summary

 For Users

 Accurate balances: Each account shows correct balance
 Complete history: See all money in/out of each account
 Clear audit trail: "Transfer to Savings" vs "Transfer from Checking"
 No money loss: Atomicity prevents partial transfers

 For Developers

 Simple queries: Balance = `SUM(amounts)` always works
 No special cases: Transfers handled like any transaction
 Type safety: Enum prevents invalid transfer types
 Easy debugging: Two separate records to inspect

 For Business

 Compliance: Double-entry bookkeeping standard
 Auditability: Clear money trail
 Reliability: ACID guarantees prevent errors
 Scalability: No complex locking needed

---

 Future Enhancements

 . Multi-Currency Transfers

```python
 Transfer with exchange rate
transfer = Transfer(
    from_account_id=A,   INR account
    to_account_id=B,     USD account
    from_amount=,    ₹,
    to_amount=,       $
    exchange_rate=.,   USD =  INR
)

 Creates:
 - Debit:  A, - INR
 - Credit: B, + USD
```

 . Transfer Reversal

```python
 Create reverse transactions
def reverse_transfer(original_transfer_id):
     Find original pair
    original_debit, original_credit = get_transfer_pair(original_transfer_id)

     Create opposite transactions
    reversal_debit = create_opposite(original_credit)
    reversal_credit = create_opposite(original_debit)

     Link to originals
    reversal_debit.reversal_of = original_debit.id
    reversal_credit.reversal_of = original_credit.id

     Commit atomically
    db.commit()
```

 . Transfer Scheduling

```python
 Schedule future transfer
scheduled_transfer = ScheduledTransfer(
    from_account=A,
    to_account=B,
    amount=,
    execute_date="--",   Future date
    recurrence="monthly",
)

 Cron job executes on date:
if scheduled_transfer.execute_date == today:
    create_transfer(...)   Atomic execution
```

---

 Conclusion

Why two transactions:
. Consistent balance calculation
. Complete per-account history
. Follows accounting principles
. Simpler implementation

How atomicity prevents money loss:
. Both transactions created in single database transaction
. Either both save (success) or both rollback (failure)
. No partial states possible
. ACID guarantees by PostgreSQL

Key takeaway:
> Transfers are not a special case—they're just two regular transactions that happen to be linked and created atomically.

This design is:
-  Simple to implement
-  Easy to reason about
-  Impossible to lose money
-  Follows industry standards

---

 Further Reading

- [Double-Entry Bookkeeping](https://en.wikipedia.org/wiki/Double-entry_bookkeeping)
- [ACID Properties](https://en.wikipedia.org/wiki/ACID)
- [Database Transactions](https://www.postgresql.org/docs/current/tutorial-transactions.html)
- [ADR-: Transfer Representation](../adrs/-transfer-representation.md) (if exists)
