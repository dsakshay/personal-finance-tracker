# API Reference

Complete API documentation for the Personal Finance Tracker backend.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All endpoints (except auth) require a JWT token in the Authorization header:

```
Authorization: Bearer <token>
```

Get token from: `POST /auth/login`

---

## Authentication Endpoints

### Register User

Create a new user account.

**Endpoint:** `POST /auth/signup`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response:** `201 Created`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Errors:**
- `400` - Invalid email format or weak password
- `409` - Email already registered

---

### Login

Authenticate and receive JWT token.

**Endpoint:** `POST /auth/login`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors:**
- `401` - Incorrect email or password

---

### Get Current User

Get authenticated user's information.

**Endpoint:** `GET /auth/me`

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Errors:**
- `401` - Invalid or expired token

---

## Account Endpoints

### Create Account

Create a new financial account.

**Endpoint:** `POST /accounts`

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "HDFC Savings Account",
  "currency": "INR",
  "opening_balance": 5000.00
}
```

**Response:** `201 Created`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "987fcdeb-51a2-43f1-9876-543210fedcba",
  "name": "HDFC Savings Account",
  "currency": "INR",
  "opening_balance": 5000.00,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Errors:**
- `400` - Invalid currency code or amount format
- `401` - Not authenticated

---

### List Accounts

Get all accounts for authenticated user.

**Endpoint:** `GET /accounts`

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "987fcdeb-51a2-43f1-9876-543210fedcba",
    "name": "HDFC Savings Account",
    "currency": "INR",
    "opening_balance": 5000.00,
    "created_at": "2024-01-15T10:30:00Z"
  },
  {
    "id": "abc12345-6789-def0-1234-56789abcdef0",
    "user_id": "987fcdeb-51a2-43f1-9876-543210fedcba",
    "name": "Cash Wallet",
    "currency": "INR",
    "opening_balance": 1000.00,
    "created_at": "2024-01-16T12:00:00Z"
  }
]
```

---

### List Accounts with Balance

Get accounts with calculated current balances.

**Endpoint:** `GET /accounts/with-balance`

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "987fcdeb-51a2-43f1-9876-543210fedcba",
    "name": "HDFC Savings Account",
    "currency": "INR",
    "opening_balance": 5000.00,
    "current_balance": 4200.50,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

---

### Get Single Account

Get specific account by ID.

**Endpoint:** `GET /accounts/{account_id}`

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "987fcdeb-51a2-43f1-9876-543210fedcba",
  "name": "HDFC Savings Account",
  "currency": "INR",
  "opening_balance": 5000.00,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Errors:**
- `404` - Account not found or not owned by user

---

## Transaction Endpoints

### Create Transaction

Create an income or expense transaction.

**Endpoint:** `POST /transactions`

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "account_id": "123e4567-e89b-12d3-a456-426614174000",
  "amount": -250.50,
  "currency": "INR",
  "transaction_type": "expense",
  "tag": "groceries",
  "payment_method": "card",
  "description": "Weekly shopping",
  "transaction_date": "2024-01-15"
}
```

**Fields:**
- `amount`: Positive for income, negative for expense
- `transaction_type`: `"income"` or `"expense"` (not `"transfer"`)
- `tag`: Category/label (e.g., groceries, salary, rent)
- `payment_method`: Optional (cash, card, upi, etc.)
- `transaction_date`: Date in YYYY-MM-DD format (not future)

**Response:** `201 Created`
```json
{
  "id": "abc12345-6789-def0-1234-56789abcdef0",
  "user_id": "987fcdeb-51a2-43f1-9876-543210fedcba",
  "account_id": "123e4567-e89b-12d3-a456-426614174000",
  "amount": -250.50,
  "currency": "INR",
  "transaction_type": "expense",
  "tag": "groceries",
  "payment_method": "card",
  "related_account_id": null,
  "description": "Weekly shopping",
  "transaction_date": "2024-01-15",
  "created_at": "2024-01-15T18:30:00Z"
}
```

**Errors:**
- `400` - Invalid amount, currency mismatch, future date
- `404` - Account not found

---

### Create Transfer

Transfer money between two accounts (atomic operation).

**Endpoint:** `POST /transactions/transfer`

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "from_account_id": "123e4567-e89b-12d3-a456-426614174000",
  "to_account_id": "987fcdeb-51a2-43f1-9876-543210fedcba",
  "amount": 1000.00,
  "currency": "INR",
  "tag": "transfer",
  "description": "Moving to savings",
  "transaction_date": "2024-01-15"
}
```

**Fields:**
- `amount`: Must be positive (direction is determined by from/to)
- Both accounts must belong to same user
- Both accounts must use same currency

**Response:** `201 Created`
```json
[
  {
    "id": "txn-debit-uuid",
    "account_id": "123e4567-e89b-12d3-a456-426614174000",
    "amount": -1000.00,
    "transaction_type": "transfer",
    "related_account_id": "987fcdeb-51a2-43f1-9876-543210fedcba",
    ...
  },
  {
    "id": "txn-credit-uuid",
    "account_id": "987fcdeb-51a2-43f1-9876-543210fedcba",
    "amount": 1000.00,
    "transaction_type": "transfer",
    "related_account_id": "123e4567-e89b-12d3-a456-426614174000",
    ...
  }
]
```

**Errors:**
- `400` - Same source/destination, currency mismatch, invalid amount
- `404` - Account(s) not found

---

### List Transactions

Get transactions with optional filters.

**Endpoint:** `GET /transactions`

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `account_id` (optional): Filter by account
- `transaction_type` (optional): Filter by type (income/expense/transfer)
- `tag` (optional): Filter by tag
- `limit` (optional): Max results (default 100, max 500)
- `offset` (optional): Skip N results for pagination (default 0)

**Example:**
```
GET /transactions?account_id=123e4567&transaction_type=expense&limit=50
```

**Response:** `200 OK`
```json
[
  {
    "id": "abc12345-6789-def0-1234-56789abcdef0",
    "user_id": "987fcdeb-51a2-43f1-9876-543210fedcba",
    "account_id": "123e4567-e89b-12d3-a456-426614174000",
    "amount": -250.50,
    "currency": "INR",
    "transaction_type": "expense",
    "tag": "groceries",
    "payment_method": "card",
    "description": "Weekly shopping",
    "transaction_date": "2024-01-15",
    "created_at": "2024-01-15T18:30:00Z"
  }
]
```

---

### Get Single Transaction

Get specific transaction by ID.

**Endpoint:** `GET /transactions/{transaction_id}`

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": "abc12345-6789-def0-1234-56789abcdef0",
  "user_id": "987fcdeb-51a2-43f1-9876-543210fedcba",
  "account_id": "123e4567-e89b-12d3-a456-426614174000",
  "amount": -250.50,
  "currency": "INR",
  "transaction_type": "expense",
  "tag": "groceries",
  "payment_method": "card",
  "description": "Weekly shopping",
  "transaction_date": "2024-01-15",
  "created_at": "2024-01-15T18:30:00Z"
}
```

**Errors:**
- `404` - Transaction not found or not owned by user

---

## Summary Endpoints

### Monthly Summary

Get financial summary for a specific month.

**Endpoint:** `GET /summary/monthly`

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `year` (optional): Year (default: current year)
- `month` (optional): Month 1-12 (default: current month)

**Example:**
```
GET /summary/monthly?year=2024&month=1
```

**Response:** `200 OK`
```json
{
  "year": 2024,
  "month": 1,
  "opening_balance": 10000.00,
  "total_income": 50000.00,
  "total_expenses": 35000.00,
  "closing_balance": 25000.00,
  "net_change": 15000.00,
  "income_by_tag": [
    {
      "tag": "salary",
      "amount": 50000.00,
      "count": 1
    }
  ],
  "expense_by_tag": [
    {
      "tag": "rent",
      "amount": 20000.00,
      "count": 1
    },
    {
      "tag": "groceries",
      "amount": 5000.00,
      "count": 8
    },
    {
      "tag": "utilities",
      "amount": 10000.00,
      "count": 5
    }
  ],
  "income_count": 1,
  "expense_count": 14,
  "transfer_count": 2
}
```

**Calculation:**
- `opening_balance`: Sum of account balances at start of month
- `total_income`: Sum of positive transactions (excluding transfers)
- `total_expenses`: Sum of negative transactions (excluding transfers)
- `closing_balance`: `opening_balance + total_income - total_expenses`
- `net_change`: `total_income - total_expenses`

**Errors:**
- `400` - Future month/year requested

---

## Common Response Codes

| Code | Meaning |
|------|---------|
| `200` | OK - Request succeeded |
| `201` | Created - Resource created successfully |
| `400` | Bad Request - Invalid input or business rule violation |
| `401` | Unauthorized - Missing or invalid token |
| `404` | Not Found - Resource doesn't exist or no access |
| `409` | Conflict - Resource already exists |
| `422` | Unprocessable Entity - Schema validation failed |
| `500` | Internal Server Error - Unexpected error |
| `503` | Service Unavailable - Database or service down |

---

## Error Response Format

All errors return JSON in this format:

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

See [Error Handling](./error-handling.md) for complete documentation.

---

## Interactive API Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- Browse all endpoints
- Try API calls directly
- See request/response schemas
- Test authentication
