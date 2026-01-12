# Error Handling & Financial Correctness

This document explains how the Personal Finance Tracker backend handles errors and ensures financial data integrity.

## Table of Contents
1. [Error Response Format](#error-response-format)
2. [HTTP Status Codes](#http-status-codes)
3. [Common Failure Scenarios](#common-failure-scenarios)
4. [Financial Correctness Protections](#financial-correctness-protections)
5. [Security Protections](#security-protections)

---

## Error Response Format

All errors return a consistent JSON structure:

```json
{
  "error": "ExceptionClassName",
  "message": "Human-readable error message",
  "details": {
    "field": "optional_field_name",
    "additional_context": "..."
  }
}
```

**Example:**
```json
{
  "error": "CurrencyMismatchException",
  "message": "Currency mismatch in transfer. Expected INR, but received USD",
  "details": {
    "expected_currency": "INR",
    "received_currency": "USD",
    "context": "transfer"
  }
}
```

---

## HTTP Status Codes

| Code | Meaning | Use Case |
|------|---------|----------|
| **200** | OK | Successful GET request |
| **201** | Created | Successful POST (resource created) |
| **400** | Bad Request | Invalid input, business rule violation |
| **401** | Unauthorized | Missing or invalid authentication token |
| **403** | Forbidden | User doesn't have permission |
| **404** | Not Found | Resource doesn't exist or user lacks access |
| **409** | Conflict | Resource already exists (e.g., duplicate email) |
| **422** | Unprocessable Entity | Schema validation failed |
| **500** | Internal Server Error | Unexpected server error |
| **503** | Service Unavailable | Database or external service down |

---

## Common Failure Scenarios

### 1. Authentication Failures

#### **Missing Token**
```bash
GET /api/v1/accounts
# No Authorization header

Response: 401 Unauthorized
{
  "error": "AuthenticationError",
  "message": "Not authenticated"
}
```

#### **Invalid Token**
```bash
GET /api/v1/accounts
Authorization: Bearer invalid-token-here

Response: 401 Unauthorized
{
  "error": "AuthenticationError",
  "message": "Invalid or expired authentication token"
}
```

#### **Expired Token**
```bash
GET /api/v1/accounts
Authorization: Bearer eyJhbGci...  # Expired token

Response: 401 Unauthorized
{
  "error": "AuthenticationError",
  "message": "Invalid or expired authentication token"
}
```

**Protection:** All protected endpoints require valid JWT. No financial data is accessible without authentication.

---

### 2. Authorization Failures

#### **Accessing Another User's Account**
```bash
GET /api/v1/accounts/other-user-account-uuid
Authorization: Bearer <your-token>

Response: 404 Not Found
{
  "error": "NotFoundException",
  "message": "Account not found"
}
```

**Protection:** Returns 404 (not 403) to prevent user enumeration. Attacker can't tell if account exists.

#### **Transfer Between Different Users**
```bash
POST /api/v1/transactions/transfer
Authorization: Bearer <user-a-token>
{
  "from_account_id": "user-a-account",
  "to_account_id": "user-b-account",  # Different user!
  "amount": 1000.00
}

Response: 404 Not Found
{
  "error": "NotFoundException",
  "message": "Account not found"
}
```

**Protection:** Both accounts must belong to the same user. Prevents unauthorized transfers.

---

### 3. Input Validation Failures

#### **Invalid Email Format**
```bash
POST /api/v1/auth/signup
{
  "email": "not-an-email",
  "password": "SecurePass123"
}

Response: 422 Unprocessable Entity
{
  "error": "ValidationError",
  "message": "Input validation failed",
  "details": {
    "errors": [
      {
        "field": "body -> email",
        "message": "value is not a valid email address",
        "type": "value_error.email"
      }
    ]
  }
}
```

#### **Amount with Too Many Decimal Places**
```bash
POST /api/v1/transactions
{
  "amount": 100.123,  # 3 decimal places
  "currency": "INR",
  ...
}

Response: 400 Bad Request
{
  "error": "ValidationException",
  "message": "Amount must have at most 2 decimal places",
  "details": {
    "field": "amount"
  }
}
```

#### **Zero Amount**
```bash
POST /api/v1/transactions
{
  "amount": 0,  # Invalid
  "currency": "INR",
  ...
}

Response: 400 Bad Request
{
  "error": "InvalidAmountException",
  "message": "Amount cannot be zero",
  "details": {
    "amount": 0.0
  }
}
```

**Protection:** Pydantic schemas validate input before it reaches business logic.

---

### 4. Currency Mismatch Failures

#### **Transaction Currency != Account Currency**
```bash
POST /api/v1/transactions
{
  "account_id": "inr-account-uuid",  # INR account
  "amount": 100.00,
  "currency": "USD",  # Trying to use USD!
  ...
}

Response: 400 Bad Request
{
  "error": "CurrencyMismatchException",
  "message": "Currency mismatch in transaction. Expected INR, but received USD",
  "details": {
    "expected_currency": "INR",
    "received_currency": "USD",
    "context": "transaction"
  }
}
```

#### **Transfer Between Different Currencies**
```bash
POST /api/v1/transactions/transfer
{
  "from_account_id": "inr-account",  # INR
  "to_account_id": "usd-account",    # USD
  "amount": 1000.00,
  "currency": "INR"
}

Response: 400 Bad Request
{
  "error": "CurrencyMismatchException",
  "message": "Currency mismatch in transfer. Expected INR, but received USD",
  "details": {
    "expected_currency": "INR",
    "received_currency": "USD",
    "context": "transfer"
  }
}
```

**Protection:** Prevents mixing currencies, which would lead to incorrect balance calculations.

---

### 5. Invalid Transfer Failures

#### **Same Source and Destination**
```bash
POST /api/v1/transactions/transfer
{
  "from_account_id": "account-uuid",
  "to_account_id": "account-uuid",  # Same account!
  "amount": 1000.00,
  "currency": "INR"
}

Response: 400 Bad Request
{
  "error": "InvalidTransferException",
  "message": "Cannot transfer to the same account",
  "details": {
    "from_account_id": "account-uuid",
    "to_account_id": "account-uuid"
  }
}
```

#### **Negative Transfer Amount**
```bash
POST /api/v1/transactions/transfer
{
  "from_account_id": "account-1",
  "to_account_id": "account-2",
  "amount": -1000.00,  # Negative!
  "currency": "INR"
}

Response: 400 Bad Request
{
  "error": "InvalidAmountException",
  "message": "Transfer amount must be positive. Got: -1000.00",
  "details": {
    "amount": -1000.00
  }
}
```

**Protection:** Transfer validation happens before database transaction, preventing invalid states.

---

### 6. Date Validation Failures

#### **Future Transaction Date**
```bash
POST /api/v1/transactions
{
  "amount": 100.00,
  "transaction_date": "2030-12-31",  # Future date!
  ...
}

Response: 400 Bad Request
{
  "error": "InvalidDateException",
  "message": "Transaction date cannot be in the future. Today is 2024-01-15",
  "details": {
    "date": "2030-12-31"
  }
}
```

**Protection:** This is a record-keeping system, not a scheduling system. Only past/present dates allowed.

---

### 7. Duplicate Resource Failures

#### **Email Already Registered**
```bash
POST /api/v1/auth/signup
{
  "email": "existing@example.com",  # Already exists
  "password": "SecurePass123"
}

Response: 409 Conflict
{
  "error": "DuplicateResourceException",
  "message": "Resource already exists: existing@example.com",
  "details": {
    "resource": "User",
    "identifier": "existing@example.com"
  }
}
```

**Protection:** Prevents duplicate accounts. Uses database unique constraint.

---

### 8. Database Failures

#### **Foreign Key Violation**
```bash
POST /api/v1/transactions
{
  "account_id": "non-existent-uuid",  # Account doesn't exist
  "amount": 100.00,
  ...
}

Response: 400 Bad Request
{
  "error": "IntegrityError",
  "message": "Referenced resource does not exist",
  "details": {
    "db_error": "..."
  }
}
```

#### **Database Connection Lost**
```bash
GET /api/v1/accounts

Response: 503 Service Unavailable
{
  "error": "DatabaseError",
  "message": "Database service unavailable",
  "details": {}
}
```

**Protection:** Graceful degradation. User knows service is temporarily unavailable.

---

## Financial Correctness Protections

### 1. **Integer-Based Money Storage (ADR-002)**

**Problem:** Floating-point arithmetic is imprecise.
```python
# Floating point error
0.1 + 0.2 == 0.30000000000000004  # NOT 0.3!
```

**Solution:** Store amounts as integers (minor units).
```python
# Correct
amount_paise = 10 + 20  # 30 paise = ₹0.30
```

**Protection:**
- All database amounts stored as `BIGINT`
- API converts: human format ↔ minor units
- No precision loss in calculations

---

### 2. **Currency Validation**

**Problem:** Mixing currencies leads to wrong totals.
```python
# WRONG
total = ₹100 + $50  # Can't add different currencies!
```

**Solution:** Enforce currency matching.
```python
# Validators check:
validate_currency_match(account.currency, transaction.currency)
validate_currency_match(from_account.currency, to_account.currency)
```

**Protection:**
- Account currency is immutable after creation
- Transactions must match account currency
- Transfers only between same-currency accounts

---

### 3. **Atomic Transfers**

**Problem:** Transfer could fail halfway, leaving inconsistent state.
```python
# BAD - What if second INSERT fails?
db.add(debit_transaction)
db.commit()  # First committed
db.add(credit_transaction)
db.commit()  # Fails! Money disappeared!
```

**Solution:** Database transaction wraps both operations.
```python
# GOOD - Both or neither
db.add(debit_transaction)
db.add(credit_transaction)
db.commit()  # Both committed atomically
```

**Protection:**
- Single `db.commit()` for both transactions
- If either fails, both are rolled back
- No partial transfers possible

---

### 4. **Transaction Immutability (ADR-005)**

**Problem:** Editing past transactions could hide mistakes or fraud.

**Solution:** Transactions are immutable once created.
```python
# Models don't have update methods
# To correct: Create reversal + new transaction
```

**Protection:**
- Complete audit trail
- Historical data preserved
- Corrections are visible as new entries

---

### 5. **User Data Isolation (ADR-001)**

**Problem:** Users could access or modify others' financial data.

**Solution:** Every query filters by `user_id`.
```python
# ALWAYS include user_id filter
accounts = db.query(Account).filter(
    Account.id == account_id,
    Account.user_id == current_user.id  # 🔒
).first()
```

**Protection:**
- Multi-tenant data isolation
- Cross-user access impossible
- 404 for resources user doesn't own (prevents enumeration)

---

### 6. **Balance Derivation (ADR-004)**

**Problem:** Cached balances can drift from reality.

**Solution:** Calculate balance on-demand.
```python
# Always accurate
current_balance = opening_balance + sum(transactions)
```

**Protection:**
- Single source of truth (transactions)
- No synchronization issues
- Always mathematically correct

---

### 7. **Zero Amount Prevention**

**Problem:** Zero transactions serve no purpose and complicate reporting.

**Solution:** Validate amount != 0.
```python
validate_amount_not_zero(amount, context="Transaction")
```

**Protection:**
- Cleaner data
- Meaningful transaction history
- Prevents accidental null entries

---

## Security Protections

### 1. **User Enumeration Prevention**

**Attack:** Check if account exists by trying different IDs.

**Defense:** Return 404 for both "not found" and "no access".
```python
# Don't reveal if resource exists
if not account:
    raise NotFoundException("Account")
    # Same message for "doesn't exist" and "no permission"
```

---

### 2. **SQL Injection Prevention**

**Attack:** Inject malicious SQL in input.
```
email: '; DROP TABLE users; --
```

**Defense:**
- SQLAlchemy ORM (parameterized queries)
- Pydantic validation (type checking)

---

### 3. **JWT Token Validation**

**Attack:** Modify token payload to impersonate another user.

**Defense:**
- Signature verification (HMAC-SHA256)
- Expiration check
- Invalid tokens rejected before reaching business logic

---

### 4. **Password Security**

**Attack:** Database breach exposes passwords.

**Defense:**
- Bcrypt hashing with salt
- One-way function (cannot reverse)
- Passwords never logged or returned in responses

---

### 5. **Rate Limiting** (Future)

**Attack:** Brute-force password guessing.

**Defense:** (To be implemented)
- Limit login attempts
- Exponential backoff
- Account lockout after N failures

---

## Error Handling Best Practices

### **For Frontend Developers:**

1. **Check Status Codes**
   ```javascript
   if (response.status === 401) {
     // Redirect to login
   } else if (response.status === 400) {
     // Show validation errors
   }
   ```

2. **Display Error Messages**
   ```javascript
   const { message, details } = await response.json();
   showError(message);  // User-friendly message
   ```

3. **Handle Network Errors**
   ```javascript
   try {
     await api.call();
   } catch (error) {
     if (!error.response) {
       // Network error
       showError("Connection lost. Please check your internet.");
     }
   }
   ```

---

## Testing Error Scenarios

See examples in test suite (future implementation):
- `tests/test_validation_errors.py`
- `tests/test_authorization_errors.py`
- `tests/test_currency_mismatches.py`
- `tests/test_transfer_atomicity.py`

---

## Summary

**Error handling ensures:**
- ✅ Clear, actionable error messages
- ✅ Consistent JSON response format
- ✅ Proper HTTP status codes
- ✅ Financial data integrity
- ✅ Cross-user access prevention
- ✅ Currency consistency
- ✅ Atomic operations (transfers)
- ✅ Input validation before database
- ✅ Graceful degradation on failures

**Your money is safe!** 💰🔒
