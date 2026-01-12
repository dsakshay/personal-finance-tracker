# Personal Finance Tracker - Test Suite

This test suite validates the correctness and security of the Personal Finance Tracker backend API.

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_transfers.py

# Run specific test
pytest tests/test_transfers.py::test_transfer_creates_two_linked_transactions

# Run with coverage report
pytest --cov=app --cov-report=html
```

## Test Infrastructure

### Test Database
- **Engine**: SQLite in-memory database
- **Isolation**: Each test gets a fresh database
- **Speed**: Fast (no disk I/O, no external dependencies)
- **No setup required**: Does NOT need PostgreSQL or uvicorn running

### Fixtures (conftest.py)
- `db_session`: Fresh database session for each test
- `client`: FastAPI TestClient with dependency overrides
- `test_user`: Pre-created user with known credentials
- `auth_token`: Valid JWT token for test user
- `auth_headers`: HTTP headers with Bearer token
- `authenticated_client`: TestClient with authentication pre-configured

## Test Categories

### 1. Authentication Tests (`test_auth.py`)

**What they validate:**
- User signup creates account with hashed password
- Duplicate email registration is prevented
- Weak passwords are rejected
- Valid credentials return JWT token
- Invalid credentials are rejected
- Protected endpoints require valid tokens

**Why critical:**
- **Security**: Prevents unauthorized access to financial data
- **Data isolation**: Each user only sees their own data
- **Password security**: Ensures passwords are hashed, never stored in plain text
- **Token validation**: Prevents token forgery and replay attacks

**Key tests:**
- `test_signup_creates_user`: Validates registration flow
- `test_login_with_valid_credentials`: Ensures JWT token generation works
- `test_protected_endpoint_without_token_fails`: Verifies authorization enforcement

---

### 2. Account Tests (`test_accounts.py`)

**What they validate:**
- Accounts created with correct opening balance
- Currency codes validated (ISO 4217 format)
- Amount format validation (exactly 2 decimal places)
- Users can only see their own accounts
- Current balance = opening balance + sum of transactions

**Why critical:**
- **Currency consistency**: Prevents mixing currencies in one account
- **Decimal precision**: Ensures amounts stored with exact 2 decimal places
- **Multi-user isolation**: User A cannot see or modify User B's accounts
- **Balance calculation**: Core finance logic must be correct

**Key tests:**
- `test_create_account_success`: Validates decimal string amount handling
- `test_list_accounts_returns_only_user_accounts`: Security isolation test
- `test_account_current_balance_reflects_transactions`: Balance calculation correctness

---

### 3. Transaction Tests (`test_transactions.py`)

**What they validate:**
- Income transactions stored as positive amounts
- Expense transactions stored as negative amounts
- Currency must match account currency
- Future transaction dates are rejected
- Cannot create transactions in other user's accounts
- Filter transactions by account, type, tag

**Why critical:**
- **Sign handling**: Income positive, expense negative (affects balance)
- **Currency validation**: Prevents invalid multi-currency transactions
- **Temporal integrity**: No future-dated transactions
- **Authorization**: Prevents cross-user transaction creation

**Key tests:**
- `test_create_income_transaction`: Validates positive amount storage
- `test_create_expense_transaction`: Validates negative amount storage
- `test_create_transaction_with_currency_mismatch_fails`: Currency enforcement
- `test_create_transaction_for_other_user_account_fails`: Authorization check

---

### 4. Transfer Tests (`test_transfers.py`)

**What they validate:**
- Transfer creates **exactly TWO** linked transactions atomically
- One debit (negative) and one credit (positive)
- Total money conserved (sum = zero)
- Both transactions reference each other via `related_account_id`
- Cannot transfer between different currencies
- Cannot transfer to same account
- Cannot transfer to other user's accounts

**Why critical:**
- **Double-entry bookkeeping**: Foundation of accounting accuracy
- **Money conservation**: Transfers don't create or destroy money
- **Atomicity**: Both transactions succeed or both fail (prevents partial transfers)
- **Data integrity**: Related account links ensure transfer traceability
- **Security**: Prevents unauthorized money movement between users

**Key tests:**
- `test_transfer_creates_two_linked_transactions`: **Most critical test** - validates double-entry
- `test_transfer_money_is_conserved`: Ensures total balance unchanged
- `test_transfer_between_different_currencies_fails`: Currency validation
- `test_transfer_atomicity_simulation`: Verifies both transactions committed together

---

### 5. Monthly Summary Tests (`test_monthly_summary.py`)

**What they validate:**
- Opening balance = account openings + all prior transactions
- Income/expense totals calculated correctly
- **Transfers do NOT count as income or expense**
- Closing balance = opening + income - expenses
- Tag breakdown sorted by amount
- Top expenses shows largest 5 expenses
- Account breakdown shows per-account balances

**Why critical:**
- **Opening balance accuracy**: Must include all historical data
- **Transfer exclusion**: Including transfers would double-count money
- **Closing balance**: Must match actual end-of-month account balances
- **Budgeting**: Tag breakdown essential for spending analysis
- **Multi-account tracking**: Account breakdown shows complete financial picture

**Key tests:**
- `test_monthly_summary_opening_balance_calculation`: Historical data inclusion
- `test_monthly_summary_transfers_not_counted_as_income_or_expense`: **Critical** - prevents double-counting
- `test_monthly_summary_closing_balance_calculation`: End-to-end calculation validation
- `test_monthly_summary_tag_breakdown`: Spending categorization

---

## Why These Tests Are Critical for Finance Correctness

### 1. Money Conservation
Transfers must not create or destroy money. The sum of all account balances must remain constant unless income/expense occurs.

**Tests validating this:**
- `test_transfer_money_is_conserved`
- `test_monthly_summary_transfers_not_counted_as_income_or_expense`

### 2. Double-Entry Bookkeeping
Every transfer creates two equal and opposite transactions. This is the foundation of accounting accuracy.

**Tests validating this:**
- `test_transfer_creates_two_linked_transactions`
- `test_transfer_atomicity_simulation`

### 3. Precision and Sign Handling
Amounts must be stored with exact precision (2 decimal places). Income positive, expense negative.

**Tests validating this:**
- `test_create_account_invalid_amount_format`
- `test_create_income_transaction` (positive)
- `test_create_expense_transaction` (negative)

### 4. Currency Consistency
Mixing currencies in the same account or transfer leads to invalid calculations.

**Tests validating this:**
- `test_create_account_invalid_currency_format`
- `test_create_transaction_with_currency_mismatch_fails`
- `test_transfer_between_different_currencies_fails`

### 5. Temporal Integrity
Financial data must be historical. Future transactions would corrupt current balance calculations.

**Tests validating this:**
- `test_create_transaction_with_future_date_fails`
- `test_transfer_with_future_date_fails`

### 6. Authorization and Security
Users must only access their own data. Cross-user data leakage would be catastrophic.

**Tests validating this:**
- `test_list_accounts_returns_only_user_accounts`
- `test_create_transaction_for_other_user_account_fails`
- `test_transfer_to_other_user_account_fails`

### 7. Aggregation Correctness
Monthly summaries must accurately reflect opening, income, expenses, and closing balances.

**Tests validating this:**
- `test_monthly_summary_opening_balance_calculation`
- `test_monthly_summary_income_and_expense_totals`
- `test_monthly_summary_closing_balance_calculation`

---

## Test Coverage Goals

**Minimum acceptable coverage:**
- Core logic: 90%+
- API endpoints: 100%
- Database models: 80%+
- Security/auth: 100%

**Coverage command:**
```bash
pytest --cov=app --cov-report=term-missing
```

---

## Adding New Tests

When adding features, ensure tests cover:

1. **Happy path**: Feature works with valid data
2. **Validation**: Invalid data is rejected with proper error
3. **Authorization**: Cannot access other user's data
4. **Edge cases**: Empty data, boundary values, null handling
5. **Finance correctness**: Amounts, signs, balances calculated correctly

**Example pattern:**
```python
def test_new_feature_success(authenticated_client):
    """Test: Feature works with valid data."""
    response = authenticated_client.post("/endpoint", json={...})
    assert response.status_code == 201
    # Validate response data

def test_new_feature_validation_fails(authenticated_client):
    """Test: Invalid data rejected."""
    response = authenticated_client.post("/endpoint", json={"invalid": "data"})
    assert response.status_code == 422

def test_new_feature_authorization(authenticated_client):
    """Test: Cannot access other user's resources."""
    # Create resource for another user
    # Try to access it with authenticated_client
    assert response.status_code == 404
```

---

## Continuous Integration

These tests should run on:
- Every commit (pre-commit hook)
- Every pull request (CI pipeline)
- Before deployment (staging validation)

**Recommended CI workflow:**
```yaml
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=app --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

---

## Debugging Failed Tests

**Common issues:**

1. **Test database state pollution**: Ensure `db_session` fixture used correctly
2. **Authentication token expired**: Use `authenticated_client` fixture
3. **Date-dependent tests**: Use fixed dates, not `date.today()`
4. **Floating point comparison**: Use decimal strings, not floats

**Debug tips:**
```bash
# Run single test with full output
pytest tests/test_transfers.py::test_transfer_money_is_conserved -vv -s

# Drop into debugger on failure
pytest --pdb

# Show print statements
pytest -s
```

---

## Test Maintenance

**When to update tests:**
- API contract changes
- New validation rules added
- Security requirements change
- Database schema modifications

**Never:**
- Remove tests to make CI pass
- Skip tests without documenting why
- Disable authorization tests
