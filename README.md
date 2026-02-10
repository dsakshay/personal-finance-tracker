#  Personal Finance Tracker (MVP)

A transparent, event-driven personal finance tracker designed to accurately track income, expenses, transfers, and balances across multiple accounts, with a clean upgrade path to a production-grade financial ledger.

---

##  Motivation

Most personal finance tools either:
- Hide how balances are computed
- Are difficult to customize
- Become untrustworthy over time

This project prioritizes:
- **Correctness**
- **Auditability**
- **Simplicity first, extensibility later**

The MVP focuses on *manual transaction entry* and *derived insights*, while laying the foundation for a robust accounting system.

---

##  MVP Goals

### Functional Goals
- Support **multiple users** on the platform (strict data isolation)
- Allow **multiple accounts per user**
- Track:
  - Income
  - Expenses
  - Transfers between own accounts
- Categorize transactions via **tags**
- Generate **monthly and yearly summaries**
- Visualize data via charts:
  - Income vs expense
  - Expense by category
  - Account-wise breakdown
  - Balance over time

### Non-Goals (MVP)
- Bank API integrations
- Automatic transaction imports
- Shared / family accounts
- Budget forecasting
- Machine learning insights

---

##  Core Design Principles

1. **Event-first thinking**
   - Transactions are append-only
   - Corrections are modeled as compensating entries

2. **Account-centric money flow**
   - All money belongs to an account
   - No global balances

3. **Integer-based money**
   - Monetary values stored in smallest units (cents / paise)
   - No floating-point arithmetic

4. **Derived aggregates**
   - Monthly and yearly summaries are computed from transactions
   - Cached later only if performance demands it

5. **Explicit ownership**
   - Every financial entity belongs to a user

---

##  High-Level Architecture (MVP)

Frontend → Backend API → Database

- **Frontend**
  - Web UI for data entry, summaries, and visualizations
- **Backend**
  - Python API handling business logic, validation, and aggregation
- **Database**
  - Relational database ensuring consistency and auditability

---

##  User Model (Platform Multi-User)

- Multiple independent users can use the platform
- Each user:
  - Has their own login
  - Owns their accounts and transactions
- No shared financial data between users in MVP

> Platform multi-user ≠ shared or family accounts  
> Shared accounts are explicitly out of scope for MVP.

---

## Data Model (MVP)

### User
Represents a platform user.

**Attributes**
- `id`
- `email`
- `password_hash`
- `created_at`

---

### Account
Represents a financial account owned by a user.

**Attributes**
- `id`
- `user_id`
- `name`
- `currency`
- `opening_balance_cents`
- `created_at`

A user can own multiple accounts.

---

### Transaction
Represents a financial event.

**Attributes**
- `id`
- `user_id`
- `account_id`
- `amount_cents`
  - Positive → income
  - Negative → expense
- `transaction_type` (`income | expense | transfer`)
- `tag` (e.g., food, salary, investment)
- `payment_method` (card, cash, upi, netbanking)
- `related_account_id` (nullable, used for transfers)
- `description`
- `transaction_date`
- `created_at`

---

### Transfers (MVP Representation)

Transfers are represented as **two linked transactions**:
- Debit from source account
- Credit to destination account

Both transactions:
- Belong to the same user
- Are created atomically by the backend

> Future versions will formalize this using a ledger + journal entry model.

---

##  Financial Computation Model

### Monthly Summary (Derived)

For a given user and month:
- **Opening balance**: previous month’s closing balance
- **Total income**: sum of all positive transactions
- **Total expenses**: absolute sum of all negative transactions
- **Closing balance**: opening_balance + total_income - total_expenses


Monthly summaries are **derived**, not stored, in MVP.

---

### Yearly Summary

- Aggregation of monthly summaries
- Used for long-term trends and reporting

---

##  Visualizations (MVP)

- Monthly income vs expense (bar chart)
- Expense distribution by category (pie chart)
- Account-wise spending (stacked bar)
- Balance over time (line chart)

All visualizations are derived from transaction data.

---

##  Security & Data Integrity (MVP)

- All queries scoped to authenticated user
- Monetary values stored as integers
- Transactions are immutable once created
- Corrections handled via reversal entries
- Soft deletes reserved for future versions

---

##  Extensibility Roadmap

### Phase 2
- Cached monthly summaries
- Stored account balances with reconciliation
- Idempotency keys
- Transaction lifecycle states

### Phase 3
- Double-entry bookkeeping (journal entries)
- Shared / family accounts
- CSV imports
- Multi-currency transfers

### Phase 4
- Mobile apps (same backend APIs)
- Public SaaS deployment

---

##  Success Criteria (MVP)

The MVP is successful if:
- Financial summaries are mathematically correct
- All balances are traceable to transactions
- A second user can sign up without data leakage
- Future ledger upgrades do not require schema rewrites

---

##  Open Design Questions

- When should summaries be cached vs computed?
- Should transactions ever be editable?
- How should corrections be surfaced in the UI?
- Should tags be user-defined or system-defined?

---

## Initial Tech Stack

- **Backend**: Python (FastAPI)
- **Database**: PostgreSQL
- **Frontend**: Web-based UI
- **Authentication**: Token-based authentication

---

##  License

MIT (tentative)

---

###  End of MVP Design



