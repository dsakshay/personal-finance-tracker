# API Contracts Specification

## Overview

This document defines the API contracts for the personal finance tracker. These contracts represent the **interface** between frontend and backend, specifying exact request/response formats.

**Important:** This is a **design document only**. Implementation comes later.

---

## Why API Contracts Matter

### 1. Frontend-Backend Coordination

**Without contracts:**
```
Frontend dev: "What fields does the account endpoint return?"
Backend dev: "Let me check the code... I think it's 'balance' or maybe 'current_balance'?"
Frontend dev: "Is it in cents or dollars?"
Backend dev: "Uh... not sure, let me run the server and test..."
```

**With contracts:**
- Frontend knows exact field names, types, and formats
- Backend knows exactly what to implement
- Both teams work in parallel without blocking

### 2. Breaking Change Prevention

```javascript
// Frontend code depends on specific field names
const balance = account.balance;  // Works today

// Backend changes field name without coordination
const balance = account.current_balance;  // Frontend breaks!
```

**Contracts prevent:**
- Silent failures
- Type mismatches
- Missing required fields
- Unexpected null values

### 3. Versioning and Evolution

```
v1 API: amount is a float (bad for money)
v2 API: amount is integer in minor units (good!)
```

- Contracts enable versioned APIs
- Frontend can migrate gradually
- Old apps continue working

### 4. Documentation and Testing

- Contracts serve as executable documentation
- Enable automated contract testing (schema validation)
- API clients (mobile, web) stay in sync

---

## Design Principles

### 1. Human-Readable Amounts

**Database (internal):**
```json
{"amount_minor": 50000, "currency": "INR"}
```

**API (external):**
```json
{"amount": "500.00", "currency": "INR"}
```

**Why:**
- Frontend doesn't deal with minor units (paise/cents)
- Easier to display and format
- Backend handles precision internally

### 2. Explicit Currency

**Never:**
```json
{"amount": "500.00"}  // What currency?!
```

**Always:**
```json
{"amount": "500.00", "currency": "INR"}
```

**Why:**
- Multi-currency support from day one
- No assumptions about user's default currency
- Explicit is better than implicit

### 3. User Context from Auth

**Wrong:**
```json
POST /accounts
{"user_id": "123", "name": "Savings"}  // Security hole!
```

**Right:**
```
POST /accounts
Authorization: Bearer <jwt_token>
{"name": "Savings"}  // user_id extracted from token
```

**Why:**
- Users can't create accounts for other users
- Prevents privilege escalation attacks
- Cleaner API (fewer fields)

### 4. ISO Standards

- **Dates:** ISO 8601 format (`YYYY-MM-DD`)
- **Timestamps:** ISO 8601 with timezone (`2026-01-12T10:30:00Z`)
- **Currency codes:** ISO 4217 (`INR`, `USD`, `EUR`)

---

## Authentication

All endpoints require authentication unless specified.

**Request Header:**
```
Authorization: Bearer <jwt_token>
```

**Extracted from token:**
- `user_id`: UUID of authenticated user
- `email`: User's email address

**Error responses:**

```json
// 401 Unauthorized
{
  "error": "unauthorized",
  "message": "Missing or invalid authentication token"
}

// 403 Forbidden
{
  "error": "forbidden",
  "message": "You do not have access to this resource"
}
```

---

## API Endpoints

### 1. POST /accounts

Create a new account for the authenticated user.

#### Request

**Headers:**
```
Content-Type: application/json
Authorization: Bearer <jwt_token>
```

**Body:**
```json
{
  "name": "Savings Account",
  "currency": "INR",
  "opening_balance": "10000.00"
}
```

**Field Specifications:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `name` | string | Yes | 1-100 chars | Account display name |
| `currency` | string | Yes | ISO 4217 code (3 chars) | Account currency |
| `opening_balance` | string | No | Decimal string, default "0.00" | Initial balance |

**Validation Rules:**

```python
name:
  - Required
  - Min length: 1 character
  - Max length: 100 characters
  - Cannot be only whitespace

currency:
  - Required
  - Must be valid ISO 4217 code (INR, USD, EUR, etc.)
  - Exactly 3 uppercase letters
  - Must be in supported currencies list

opening_balance:
  - Optional (defaults to "0.00")
  - Must be valid decimal string
  - Format: "[-]?[0-9]+\.[0-9]{2}"
  - Examples: "0.00", "1000.50", "-250.00"
  - Max precision: 2 decimal places
  - Must not exceed ±9999999999.99 (10 billion limit)
```

#### Response

**Success: 201 Created**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Savings Account",
  "currency": "INR",
  "opening_balance": "10000.00",
  "current_balance": "10000.00",
  "created_at": "2026-01-12T10:30:00Z"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Unique account identifier |
| `name` | string | Account display name |
| `currency` | string | ISO 4217 currency code |
| `opening_balance` | string | Initial balance (decimal) |
| `current_balance` | string | Current balance including all transactions |
| `created_at` | string (ISO 8601) | Account creation timestamp (UTC) |

**Error Responses:**

```json
// 400 Bad Request - Validation failure
{
  "error": "validation_error",
  "message": "Invalid request data",
  "details": {
    "name": ["Field is required"],
    "currency": ["Must be a valid ISO 4217 currency code"],
    "opening_balance": ["Must be a valid decimal with 2 decimal places"]
  }
}

// 400 Bad Request - Unsupported currency
{
  "error": "unsupported_currency",
  "message": "Currency 'XYZ' is not supported",
  "supported_currencies": ["INR", "USD", "EUR", "GBP"]
}

// 409 Conflict - Duplicate account name
{
  "error": "duplicate_account",
  "message": "An account with this name already exists"
}
```

#### Example

**Request:**
```bash
curl -X POST https://api.example.com/accounts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGc..." \
  -d '{
    "name": "Emergency Fund",
    "currency": "INR",
    "opening_balance": "50000.00"
  }'
```

**Response:**
```json
{
  "id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
  "name": "Emergency Fund",
  "currency": "INR",
  "opening_balance": "50000.00",
  "current_balance": "50000.00",
  "created_at": "2026-01-12T14:23:45Z"
}
```

---

### 2. GET /accounts

Retrieve all accounts for the authenticated user.

#### Request

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `currency` | string | No | Filter accounts by currency (ISO 4217) |

**Example URLs:**
```
GET /accounts
GET /accounts?currency=INR
```

#### Response

**Success: 200 OK**

```json
{
  "accounts": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Savings Account",
      "currency": "INR",
      "opening_balance": "10000.00",
      "current_balance": "12500.50",
      "created_at": "2026-01-01T00:00:00Z"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440111",
      "name": "Credit Card",
      "currency": "INR",
      "opening_balance": "0.00",
      "current_balance": "-3500.00",
      "created_at": "2026-01-05T10:30:00Z"
    }
  ],
  "total_count": 2
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `accounts` | array | List of account objects |
| `total_count` | integer | Total number of accounts returned |

**Account Object:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Unique account identifier |
| `name` | string | Account display name |
| `currency` | string | ISO 4217 currency code |
| `opening_balance` | string | Initial balance (decimal) |
| `current_balance` | string | Balance including all transactions |
| `created_at` | string (ISO 8601) | Account creation timestamp (UTC) |

**Notes:**
- `current_balance` = `opening_balance` + sum of all transaction amounts
- Negative balance indicates debt (e.g., credit cards)
- Accounts are ordered by `created_at` descending (newest first)

**Error Responses:**

```json
// 400 Bad Request - Invalid currency filter
{
  "error": "invalid_currency",
  "message": "Currency 'XYZ' is not a valid ISO 4217 code"
}
```

#### Example

**Request:**
```bash
curl -X GET https://api.example.com/accounts \
  -H "Authorization: Bearer eyJhbGc..."
```

**Response:**
```json
{
  "accounts": [
    {
      "id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
      "name": "Emergency Fund",
      "currency": "INR",
      "opening_balance": "50000.00",
      "current_balance": "48200.50",
      "created_at": "2026-01-10T14:23:45Z"
    },
    {
      "id": "b2c3d4e5-f6a7-5b8c-9d0e-1f2a3b4c5d6e",
      "name": "Checking",
      "currency": "INR",
      "opening_balance": "5000.00",
      "current_balance": "7850.25",
      "created_at": "2026-01-01T08:00:00Z"
    }
  ],
  "total_count": 2
}
```

---

### 3. POST /transactions

Create a new transaction (income, expense, or transfer).

#### Request

**Headers:**
```
Content-Type: application/json
Authorization: Bearer <jwt_token>
```

**Body - Income/Expense:**
```json
{
  "account_id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": "500.00",
  "currency": "INR",
  "transaction_type": "expense",
  "tag": "groceries",
  "payment_method": "card",
  "description": "Weekly grocery shopping",
  "transaction_date": "2026-01-12"
}
```

**Body - Transfer:**
```json
{
  "account_id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": "1000.00",
  "currency": "INR",
  "transaction_type": "transfer",
  "related_account_id": "660e8400-e29b-41d4-a716-446655440111",
  "tag": "transfer",
  "description": "Moving money to savings",
  "transaction_date": "2026-01-12"
}
```

**Field Specifications:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `account_id` | string (UUID) | Yes | Must exist and belong to user | Source account |
| `amount` | string | Yes | Positive decimal string | Transaction amount |
| `currency` | string | Yes | ISO 4217 code | Must match account currency |
| `transaction_type` | string | Yes | `income`, `expense`, or `transfer` | Transaction classification |
| `tag` | string | Yes | 1-50 chars | Category tag |
| `payment_method` | string | No | 1-50 chars | Payment method (optional) |
| `related_account_id` | string (UUID) | Required for `transfer` | Must exist and belong to user | Destination account (transfers only) |
| `description` | string | No | Max 255 chars | Optional notes |
| `transaction_date` | string | Yes | ISO 8601 date (YYYY-MM-DD) | When transaction occurred |

**Validation Rules:**

```python
account_id:
  - Required
  - Must be valid UUID
  - Must exist in database
  - Must belong to authenticated user

amount:
  - Required
  - Must be positive decimal string
  - Format: "[0-9]+\.[0-9]{2}"
  - Examples: "0.01", "500.00", "10000.50"
  - Must be > 0.00
  - Max: 9999999999.99

currency:
  - Required
  - Must match account's currency
  - ISO 4217 code (3 uppercase letters)

transaction_type:
  - Required
  - Must be one of: "income", "expense", "transfer"

tag:
  - Required
  - Min length: 1 character
  - Max length: 50 characters
  - Examples: "groceries", "salary", "rent", "transfer"

payment_method:
  - Optional
  - Max length: 50 characters
  - Examples: "cash", "card", "upi", "bank_transfer"

related_account_id:
  - Required if transaction_type = "transfer"
  - Must be valid UUID
  - Must exist in database
  - Must belong to authenticated user
  - Cannot be same as account_id

description:
  - Optional
  - Max length: 255 characters

transaction_date:
  - Required
  - Must be valid ISO 8601 date (YYYY-MM-DD)
  - Cannot be in the future
  - Cannot be more than 10 years in the past
```

**Amount Sign Convention:**
- Client always sends **positive** amounts
- Backend determines sign based on transaction type:
  - `income`: stored as positive
  - `expense`: stored as negative
  - `transfer`: creates two transactions (negative for source, positive for destination)

#### Response

**Success: 201 Created (Income/Expense)**

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440222",
  "account_id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": "-500.00",
  "currency": "INR",
  "transaction_type": "expense",
  "tag": "groceries",
  "payment_method": "card",
  "description": "Weekly grocery shopping",
  "transaction_date": "2026-01-12",
  "created_at": "2026-01-12T10:30:00Z"
}
```

**Success: 201 Created (Transfer)**

```json
{
  "transfer_id": "880e8400-e29b-41d4-a716-446655440333",
  "transactions": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440444",
      "account_id": "550e8400-e29b-41d4-a716-446655440000",
      "amount": "-1000.00",
      "currency": "INR",
      "transaction_type": "transfer",
      "tag": "transfer",
      "related_account_id": "660e8400-e29b-41d4-a716-446655440111",
      "description": "Moving money to savings",
      "transaction_date": "2026-01-12",
      "created_at": "2026-01-12T10:30:00Z"
    },
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440555",
      "account_id": "660e8400-e29b-41d4-a716-446655440111",
      "amount": "1000.00",
      "currency": "INR",
      "transaction_type": "transfer",
      "tag": "transfer",
      "related_account_id": "550e8400-e29b-41d4-a716-446655440000",
      "description": "Moving money to savings",
      "transaction_date": "2026-01-12",
      "created_at": "2026-01-12T10:30:00Z"
    }
  ]
}
```

**Response Fields (Income/Expense):**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Unique transaction identifier |
| `account_id` | string (UUID) | Account this transaction belongs to |
| `amount` | string | Signed amount (negative for expense, positive for income) |
| `currency` | string | ISO 4217 currency code |
| `transaction_type` | string | Transaction type |
| `tag` | string | Category tag |
| `payment_method` | string \| null | Payment method if provided |
| `related_account_id` | string (UUID) \| null | Always null for income/expense |
| `description` | string \| null | Description if provided |
| `transaction_date` | string (ISO 8601 date) | Transaction date |
| `created_at` | string (ISO 8601) | Creation timestamp (UTC) |

**Response Fields (Transfer):**

| Field | Type | Description |
|-------|------|-------------|
| `transfer_id` | string (UUID) | Logical transfer identifier |
| `transactions` | array | Two transaction objects (debit and credit) |

**Notes:**
- Response `amount` includes sign (negative for outflow, positive for inflow)
- Transfers create two linked transactions atomically
- `payment_method` and `related_account_id` can be null

**Error Responses:**

```json
// 400 Bad Request - Validation error
{
  "error": "validation_error",
  "message": "Invalid request data",
  "details": {
    "amount": ["Must be a positive decimal with 2 decimal places"],
    "transaction_type": ["Must be one of: income, expense, transfer"]
  }
}

// 400 Bad Request - Currency mismatch
{
  "error": "currency_mismatch",
  "message": "Transaction currency 'USD' does not match account currency 'INR'"
}

// 400 Bad Request - Transfer to same account
{
  "error": "invalid_transfer",
  "message": "Cannot transfer to the same account"
}

// 400 Bad Request - Future date
{
  "error": "invalid_date",
  "message": "Transaction date cannot be in the future"
}

// 404 Not Found - Account doesn't exist
{
  "error": "account_not_found",
  "message": "Account with id '...' not found"
}

// 403 Forbidden - Account belongs to another user
{
  "error": "forbidden",
  "message": "You do not have access to this account"
}
```

#### Examples

**Example 1: Expense**

**Request:**
```bash
curl -X POST https://api.example.com/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGc..." \
  -d '{
    "account_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
    "amount": "75.50",
    "currency": "INR",
    "transaction_type": "expense",
    "tag": "dining",
    "payment_method": "card",
    "description": "Dinner at restaurant",
    "transaction_date": "2026-01-11"
  }'
```

**Response:**
```json
{
  "id": "c3d4e5f6-a7b8-5c9d-0e1f-2a3b4c5d6e7f",
  "account_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
  "amount": "-75.50",
  "currency": "INR",
  "transaction_type": "expense",
  "tag": "dining",
  "payment_method": "card",
  "description": "Dinner at restaurant",
  "transaction_date": "2026-01-11",
  "created_at": "2026-01-12T10:30:00Z"
}
```

**Example 2: Income**

**Request:**
```bash
curl -X POST https://api.example.com/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGc..." \
  -d '{
    "account_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
    "amount": "50000.00",
    "currency": "INR",
    "transaction_type": "income",
    "tag": "salary",
    "payment_method": "bank_transfer",
    "description": "January salary",
    "transaction_date": "2026-01-01"
  }'
```

**Response:**
```json
{
  "id": "d4e5f6a7-b8c9-6d0e-1f2a-3b4c5d6e7f8a",
  "account_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
  "amount": "50000.00",
  "currency": "INR",
  "transaction_type": "income",
  "tag": "salary",
  "payment_method": "bank_transfer",
  "description": "January salary",
  "transaction_date": "2026-01-01",
  "created_at": "2026-01-12T10:35:00Z"
}
```

**Example 3: Transfer**

**Request:**
```bash
curl -X POST https://api.example.com/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGc..." \
  -d '{
    "account_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
    "amount": "5000.00",
    "currency": "INR",
    "transaction_type": "transfer",
    "related_account_id": "b2c3d4e5-f6a7-5b8c-9d0e-1f2a3b4c5d6e",
    "tag": "transfer",
    "description": "Emergency fund contribution",
    "transaction_date": "2026-01-12"
  }'
```

**Response:**
```json
{
  "transfer_id": "e5f6a7b8-c9d0-7e1f-2a3b-4c5d6e7f8a9b",
  "transactions": [
    {
      "id": "f6a7b8c9-d0e1-8f2a-3b4c-5d6e7f8a9b0c",
      "account_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
      "amount": "-5000.00",
      "currency": "INR",
      "transaction_type": "transfer",
      "tag": "transfer",
      "related_account_id": "b2c3d4e5-f6a7-5b8c-9d0e-1f2a3b4c5d6e",
      "description": "Emergency fund contribution",
      "transaction_date": "2026-01-12",
      "created_at": "2026-01-12T10:40:00Z"
    },
    {
      "id": "a7b8c9d0-e1f2-9a3b-4c5d-6e7f8a9b0c1d",
      "account_id": "b2c3d4e5-f6a7-5b8c-9d0e-1f2a3b4c5d6e",
      "amount": "5000.00",
      "currency": "INR",
      "transaction_type": "transfer",
      "tag": "transfer",
      "related_account_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
      "description": "Emergency fund contribution",
      "transaction_date": "2026-01-12",
      "created_at": "2026-01-12T10:40:00Z"
    }
  ]
}
```

---

### 4. GET /transactions

Retrieve transactions for the authenticated user.

#### Request

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `account_id` | string (UUID) | No | Filter by account |
| `transaction_type` | string | No | Filter by type: `income`, `expense`, or `transfer` |
| `tag` | string | No | Filter by tag (exact match) |
| `from_date` | string | No | Start date (ISO 8601: YYYY-MM-DD), inclusive |
| `to_date` | string | No | End date (ISO 8601: YYYY-MM-DD), inclusive |
| `limit` | integer | No | Max results per page (default: 50, max: 200) |
| `offset` | integer | No | Skip N results (default: 0) |

**Example URLs:**
```
GET /transactions
GET /transactions?account_id=550e8400-e29b-41d4-a716-446655440000
GET /transactions?transaction_type=expense&tag=groceries
GET /transactions?from_date=2026-01-01&to_date=2026-01-31
GET /transactions?limit=20&offset=40
```

**Notes:**
- Multiple filters can be combined
- Results ordered by `transaction_date` descending, then `created_at` descending
- Pagination using `limit` and `offset`

#### Response

**Success: 200 OK**

```json
{
  "transactions": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440222",
      "account_id": "550e8400-e29b-41d4-a716-446655440000",
      "account_name": "Savings Account",
      "amount": "-500.00",
      "currency": "INR",
      "transaction_type": "expense",
      "tag": "groceries",
      "payment_method": "card",
      "related_account_id": null,
      "related_account_name": null,
      "description": "Weekly grocery shopping",
      "transaction_date": "2026-01-12",
      "created_at": "2026-01-12T10:30:00Z"
    },
    {
      "id": "880e8400-e29b-41d4-a716-446655440333",
      "account_id": "550e8400-e29b-41d4-a716-446655440000",
      "account_name": "Savings Account",
      "amount": "-1000.00",
      "currency": "INR",
      "transaction_type": "transfer",
      "tag": "transfer",
      "payment_method": null,
      "related_account_id": "660e8400-e29b-41d4-a716-446655440111",
      "related_account_name": "Emergency Fund",
      "description": "Moving money to savings",
      "transaction_date": "2026-01-11",
      "created_at": "2026-01-11T15:20:00Z"
    }
  ],
  "total_count": 2,
  "limit": 50,
  "offset": 0
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `transactions` | array | List of transaction objects |
| `total_count` | integer | Total transactions matching filters |
| `limit` | integer | Results per page |
| `offset` | integer | Current offset |

**Transaction Object:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Unique transaction identifier |
| `account_id` | string (UUID) | Account this transaction belongs to |
| `account_name` | string | Account name (for display) |
| `amount` | string | Signed amount (decimal) |
| `currency` | string | ISO 4217 currency code |
| `transaction_type` | string | Transaction type |
| `tag` | string | Category tag |
| `payment_method` | string \| null | Payment method if provided |
| `related_account_id` | string (UUID) \| null | Related account (transfers only) |
| `related_account_name` | string \| null | Related account name (transfers only) |
| `description` | string \| null | Description if provided |
| `transaction_date` | string (ISO 8601 date) | Transaction date |
| `created_at` | string (ISO 8601) | Creation timestamp (UTC) |

**Notes:**
- Includes `account_name` and `related_account_name` for display (denormalized)
- Frontend doesn't need separate account lookup
- `amount` is signed (negative for outflow, positive for inflow)

**Error Responses:**

```json
// 400 Bad Request - Invalid filter
{
  "error": "invalid_filter",
  "message": "Invalid transaction_type. Must be one of: income, expense, transfer"
}

// 400 Bad Request - Invalid date range
{
  "error": "invalid_date_range",
  "message": "from_date must be before or equal to to_date"
}

// 400 Bad Request - Invalid pagination
{
  "error": "invalid_pagination",
  "message": "limit must be between 1 and 200"
}

// 404 Not Found - Account doesn't exist
{
  "error": "account_not_found",
  "message": "Account with id '...' not found"
}
```

#### Example

**Request:**
```bash
curl -X GET "https://api.example.com/transactions?transaction_type=expense&from_date=2026-01-01&to_date=2026-01-31&limit=10" \
  -H "Authorization: Bearer eyJhbGc..."
```

**Response:**
```json
{
  "transactions": [
    {
      "id": "c3d4e5f6-a7b8-5c9d-0e1f-2a3b4c5d6e7f",
      "account_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
      "account_name": "Checking",
      "amount": "-75.50",
      "currency": "INR",
      "transaction_type": "expense",
      "tag": "dining",
      "payment_method": "card",
      "related_account_id": null,
      "related_account_name": null,
      "description": "Dinner at restaurant",
      "transaction_date": "2026-01-11",
      "created_at": "2026-01-12T10:30:00Z"
    },
    {
      "id": "d4e5f6a7-b8c9-6d0e-1f2a-3b4c5d6e7f8a",
      "account_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
      "account_name": "Checking",
      "amount": "-1200.00",
      "currency": "INR",
      "transaction_type": "expense",
      "tag": "rent",
      "payment_method": "bank_transfer",
      "related_account_id": null,
      "related_account_name": null,
      "description": "January rent",
      "transaction_date": "2026-01-05",
      "created_at": "2026-01-05T09:00:00Z"
    }
  ],
  "total_count": 2,
  "limit": 10,
  "offset": 0
}
```

---

### 5. GET /summary/monthly

Get monthly financial summary for the authenticated user.

#### Request

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `year` | integer | Yes | Year (e.g., 2026) |
| `month` | integer | Yes | Month (1-12) |
| `currency` | string | No | Filter by currency (ISO 4217) |

**Example URLs:**
```
GET /summary/monthly?year=2026&month=1
GET /summary/monthly?year=2026&month=1&currency=INR
```

**Validation Rules:**

```python
year:
  - Required
  - Integer between 2000 and 2100

month:
  - Required
  - Integer between 1 and 12

currency:
  - Optional
  - Must be valid ISO 4217 code if provided
  - Filters results to accounts/transactions in this currency only
```

#### Response

**Success: 200 OK**

```json
{
  "period": {
    "year": 2026,
    "month": 1,
    "month_name": "January",
    "start_date": "2026-01-01",
    "end_date": "2026-01-31"
  },
  "summary": {
    "total_income": "50000.00",
    "total_expenses": "18500.50",
    "net_savings": "31499.50",
    "currency": "INR"
  },
  "by_tag": [
    {
      "tag": "groceries",
      "total": "-5500.00",
      "count": 15,
      "currency": "INR"
    },
    {
      "tag": "salary",
      "total": "50000.00",
      "count": 1,
      "currency": "INR"
    },
    {
      "tag": "dining",
      "total": "-3200.50",
      "count": 8,
      "currency": "INR"
    }
  ],
  "by_account": [
    {
      "account_id": "550e8400-e29b-41d4-a716-446655440000",
      "account_name": "Savings Account",
      "opening_balance": "10000.00",
      "closing_balance": "12500.50",
      "net_change": "2500.50",
      "currency": "INR",
      "transaction_count": 23
    },
    {
      "account_id": "660e8400-e29b-41d4-a716-446655440111",
      "account_name": "Credit Card",
      "opening_balance": "0.00",
      "closing_balance": "-3500.00",
      "net_change": "-3500.00",
      "currency": "INR",
      "transaction_count": 12
    }
  ],
  "top_expenses": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440222",
      "account_name": "Credit Card",
      "amount": "-1200.00",
      "currency": "INR",
      "tag": "rent",
      "description": "January rent",
      "transaction_date": "2026-01-05"
    },
    {
      "id": "880e8400-e29b-41d4-a716-446655440333",
      "account_name": "Savings Account",
      "amount": "-500.00",
      "currency": "INR",
      "tag": "groceries",
      "description": "Weekly grocery shopping",
      "transaction_date": "2026-01-12"
    }
  ]
}
```

**Response Fields:**

**`period` object:**

| Field | Type | Description |
|-------|------|-------------|
| `year` | integer | Requested year |
| `month` | integer | Requested month (1-12) |
| `month_name` | string | Month name (e.g., "January") |
| `start_date` | string (ISO 8601 date) | First day of month |
| `end_date` | string (ISO 8601 date) | Last day of month |

**`summary` object:**

| Field | Type | Description |
|-------|------|-------------|
| `total_income` | string | Sum of all income transactions (positive) |
| `total_expenses` | string | Sum of all expense transactions (positive, unsigned) |
| `net_savings` | string | Income minus expenses |
| `currency` | string | Currency code (if filtered), or "MIXED" if multiple |

**`by_tag` array:**

| Field | Type | Description |
|-------|------|-------------|
| `tag` | string | Tag name |
| `total` | string | Sum of amounts (signed) |
| `count` | integer | Number of transactions |
| `currency` | string | Currency code |

**Notes:**
- Sorted by absolute value of `total` descending
- Max 10 tags returned
- Excludes transfers

**`by_account` array:**

| Field | Type | Description |
|-------|------|-------------|
| `account_id` | string (UUID) | Account identifier |
| `account_name` | string | Account name |
| `opening_balance` | string | Balance at start of month |
| `closing_balance` | string | Balance at end of month |
| `net_change` | string | Difference (closing - opening) |
| `currency` | string | Account currency |
| `transaction_count` | integer | Transactions in this month |

**`top_expenses` array:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Transaction ID |
| `account_name` | string | Account name |
| `amount` | string | Amount (negative, signed) |
| `currency` | string | Currency code |
| `tag` | string | Tag name |
| `description` | string \| null | Description if provided |
| `transaction_date` | string (ISO 8601 date) | Transaction date |

**Notes:**
- Top 5 expenses by absolute amount
- Excludes transfers
- Sorted by amount descending (most negative first)

**Error Responses:**

```json
// 400 Bad Request - Invalid year
{
  "error": "invalid_year",
  "message": "Year must be between 2000 and 2100"
}

// 400 Bad Request - Invalid month
{
  "error": "invalid_month",
  "message": "Month must be between 1 and 12"
}

// 400 Bad Request - Invalid currency
{
  "error": "invalid_currency",
  "message": "Currency 'XYZ' is not a valid ISO 4217 code"
}
```

#### Example

**Request:**
```bash
curl -X GET "https://api.example.com/summary/monthly?year=2026&month=1&currency=INR" \
  -H "Authorization: Bearer eyJhbGc..."
```

**Response:**
```json
{
  "period": {
    "year": 2026,
    "month": 1,
    "month_name": "January",
    "start_date": "2026-01-01",
    "end_date": "2026-01-31"
  },
  "summary": {
    "total_income": "50000.00",
    "total_expenses": "18500.50",
    "net_savings": "31499.50",
    "currency": "INR"
  },
  "by_tag": [
    {
      "tag": "salary",
      "total": "50000.00",
      "count": 1,
      "currency": "INR"
    },
    {
      "tag": "groceries",
      "total": "-5500.00",
      "count": 15,
      "currency": "INR"
    },
    {
      "tag": "dining",
      "total": "-3200.50",
      "count": 8,
      "currency": "INR"
    },
    {
      "tag": "utilities",
      "total": "-2500.00",
      "count": 4,
      "currency": "INR"
    },
    {
      "tag": "transport",
      "total": "-1800.00",
      "count": 12,
      "currency": "INR"
    }
  ],
  "by_account": [
    {
      "account_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
      "account_name": "Checking",
      "opening_balance": "5000.00",
      "closing_balance": "36499.50",
      "net_change": "31499.50",
      "currency": "INR",
      "transaction_count": 35
    },
    {
      "account_id": "b2c3d4e5-f6a7-5b8c-9d0e-1f2a3b4c5d6e",
      "account_name": "Credit Card",
      "opening_balance": "0.00",
      "closing_balance": "0.00",
      "net_change": "0.00",
      "currency": "INR",
      "transaction_count": 5
    }
  ],
  "top_expenses": [
    {
      "id": "e5f6a7b8-c9d0-7e1f-2a3b-4c5d6e7f8a9b",
      "account_name": "Checking",
      "amount": "-12000.00",
      "currency": "INR",
      "tag": "rent",
      "description": "January rent payment",
      "transaction_date": "2026-01-05"
    },
    {
      "id": "f6a7b8c9-d0e1-8f2a-3b4c-5d6e7f8a9b0c",
      "account_name": "Credit Card",
      "amount": "-2500.00",
      "currency": "INR",
      "tag": "utilities",
      "description": "Electricity bill",
      "transaction_date": "2026-01-15"
    },
    {
      "id": "a7b8c9d0-e1f2-9a3b-4c5d-6e7f8a9b0c1d",
      "account_name": "Checking",
      "amount": "-800.00",
      "currency": "INR",
      "tag": "groceries",
      "description": "Monthly grocery stock",
      "transaction_date": "2026-01-20"
    }
  ]
}
```

---

## Common Error Responses

All endpoints may return these standard errors:

### 401 Unauthorized

```json
{
  "error": "unauthorized",
  "message": "Missing or invalid authentication token"
}
```

**Cause:** No `Authorization` header or invalid JWT token

### 403 Forbidden

```json
{
  "error": "forbidden",
  "message": "You do not have access to this resource"
}
```

**Cause:** Authenticated, but accessing another user's resource

### 404 Not Found

```json
{
  "error": "not_found",
  "message": "Resource not found"
}
```

**Cause:** Requested resource (account, transaction) doesn't exist

### 422 Unprocessable Entity

```json
{
  "error": "business_logic_error",
  "message": "Insufficient balance for this transaction"
}
```

**Cause:** Request is valid, but business logic prevents operation

### 500 Internal Server Error

```json
{
  "error": "internal_server_error",
  "message": "An unexpected error occurred"
}
```

**Cause:** Server-side error (should be logged and monitored)

---

## Data Type Conventions

### Amount Formatting

**Format:** Decimal string with exactly 2 decimal places

```
Valid:   "0.00", "100.50", "12345.67", "-500.00"
Invalid: "100", "100.5", "100.567", "-100"
```

**Why string, not number?**
- JavaScript `number` loses precision for large amounts
- Example: `0.1 + 0.2 = 0.30000000000000004` in JavaScript
- Strings preserve exact decimal values

**Frontend handling:**
```javascript
// Parsing
const amount = parseFloat("100.50");  // 100.5

// Formatting for display
const formatted = parseFloat("100.50").toFixed(2);  // "100.50"

// Arithmetic (use a library like decimal.js)
import Decimal from 'decimal.js';
const total = new Decimal("100.50").plus("200.75").toString();  // "301.25"
```

### Date Formatting

**ISO 8601 Date (YYYY-MM-DD):**
```
Valid:   "2026-01-12", "2025-12-31"
Invalid: "01-12-2026", "12/01/2026", "2026/01/12"
```

**ISO 8601 Timestamp (YYYY-MM-DDTHH:mm:ssZ):**
```
Valid:   "2026-01-12T10:30:00Z"
Invalid: "2026-01-12 10:30:00", "2026-01-12T10:30:00"
```

**Why UTC (Z suffix)?**
- Consistent across timezones
- Frontend converts to user's local timezone for display

**Frontend handling:**
```javascript
// Parsing
const date = new Date("2026-01-12T10:30:00Z");

// Display in user's timezone
const local = date.toLocaleString();  // "1/12/2026, 4:00:00 PM IST"

// Display as date only
const dateOnly = date.toLocaleDateString();  // "1/12/2026"
```

### UUID Formatting

**Format:** Canonical 8-4-4-4-12 format

```
Valid:   "550e8400-e29b-41d4-a716-446655440000"
Invalid: "550e8400e29b41d4a716446655440000"  // Missing hyphens
```

---

## Frontend Integration Guide

### 1. Type Definitions (TypeScript)

```typescript
// types/api.ts

// Common types
export type UUID = string;
export type ISO8601Date = string;  // YYYY-MM-DD
export type ISO8601Timestamp = string;  // YYYY-MM-DDTHH:mm:ssZ
export type CurrencyCode = string;  // ISO 4217 (e.g., "INR")
export type DecimalString = string;  // e.g., "100.50"

export type TransactionType = "income" | "expense" | "transfer";

// Account
export interface Account {
  id: UUID;
  name: string;
  currency: CurrencyCode;
  opening_balance: DecimalString;
  current_balance: DecimalString;
  created_at: ISO8601Timestamp;
}

export interface CreateAccountRequest {
  name: string;
  currency: CurrencyCode;
  opening_balance?: DecimalString;
}

export interface GetAccountsResponse {
  accounts: Account[];
  total_count: number;
}

// Transaction
export interface Transaction {
  id: UUID;
  account_id: UUID;
  account_name: string;
  amount: DecimalString;
  currency: CurrencyCode;
  transaction_type: TransactionType;
  tag: string;
  payment_method: string | null;
  related_account_id: UUID | null;
  related_account_name: string | null;
  description: string | null;
  transaction_date: ISO8601Date;
  created_at: ISO8601Timestamp;
}

export interface CreateTransactionRequest {
  account_id: UUID;
  amount: DecimalString;
  currency: CurrencyCode;
  transaction_type: TransactionType;
  tag: string;
  payment_method?: string;
  related_account_id?: UUID;
  description?: string;
  transaction_date: ISO8601Date;
}

export interface CreateTransactionResponse {
  id?: UUID;
  transfer_id?: UUID;
  transactions?: Transaction[];
  // ... other fields
}

export interface GetTransactionsResponse {
  transactions: Transaction[];
  total_count: number;
  limit: number;
  offset: number;
}

// Monthly Summary
export interface MonthlySummary {
  period: {
    year: number;
    month: number;
    month_name: string;
    start_date: ISO8601Date;
    end_date: ISO8601Date;
  };
  summary: {
    total_income: DecimalString;
    total_expenses: DecimalString;
    net_savings: DecimalString;
    currency: CurrencyCode;
  };
  by_tag: Array<{
    tag: string;
    total: DecimalString;
    count: number;
    currency: CurrencyCode;
  }>;
  by_account: Array<{
    account_id: UUID;
    account_name: string;
    opening_balance: DecimalString;
    closing_balance: DecimalString;
    net_change: DecimalString;
    currency: CurrencyCode;
    transaction_count: number;
  }>;
  top_expenses: Array<{
    id: UUID;
    account_name: string;
    amount: DecimalString;
    currency: CurrencyCode;
    tag: string;
    description: string | null;
    transaction_date: ISO8601Date;
  }>;
}

// Error response
export interface APIError {
  error: string;
  message: string;
  details?: Record<string, string[]>;
}
```

### 2. API Client (Axios)

```typescript
// services/api.ts
import axios, { AxiosInstance } from 'axios';
import type {
  Account,
  CreateAccountRequest,
  GetAccountsResponse,
  Transaction,
  CreateTransactionRequest,
  CreateTransactionResponse,
  GetTransactionsResponse,
  MonthlySummary,
  APIError,
} from '../types/api';

class FinanceAPI {
  private client: AxiosInstance;

  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token to all requests
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  // Accounts
  async createAccount(data: CreateAccountRequest): Promise<Account> {
    const response = await this.client.post<Account>('/accounts', data);
    return response.data;
  }

  async getAccounts(currency?: string): Promise<GetAccountsResponse> {
    const response = await this.client.get<GetAccountsResponse>('/accounts', {
      params: { currency },
    });
    return response.data;
  }

  // Transactions
  async createTransaction(
    data: CreateTransactionRequest
  ): Promise<CreateTransactionResponse> {
    const response = await this.client.post<CreateTransactionResponse>(
      '/transactions',
      data
    );
    return response.data;
  }

  async getTransactions(params?: {
    account_id?: string;
    transaction_type?: string;
    tag?: string;
    from_date?: string;
    to_date?: string;
    limit?: number;
    offset?: number;
  }): Promise<GetTransactionsResponse> {
    const response = await this.client.get<GetTransactionsResponse>(
      '/transactions',
      { params }
    );
    return response.data;
  }

  // Monthly Summary
  async getMonthlySummary(
    year: number,
    month: number,
    currency?: string
  ): Promise<MonthlySummary> {
    const response = await this.client.get<MonthlySummary>(
      '/summary/monthly',
      {
        params: { year, month, currency },
      }
    );
    return response.data;
  }
}

export const api = new FinanceAPI('https://api.example.com');
```

### 3. Usage in Components (React)

```typescript
// components/AccountList.tsx
import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { Account } from '../types/api';

export function AccountList() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchAccounts() {
      try {
        const data = await api.getAccounts();
        setAccounts(data.accounts);
      } catch (error) {
        console.error('Failed to fetch accounts:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchAccounts();
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <ul>
      {accounts.map((account) => (
        <li key={account.id}>
          {account.name}: {account.currency} {account.current_balance}
        </li>
      ))}
    </ul>
  );
}
```

### 4. Contract Testing

```typescript
// tests/api.contract.test.ts
import { api } from '../services/api';

describe('API Contracts', () => {
  it('POST /accounts returns correct structure', async () => {
    const account = await api.createAccount({
      name: 'Test Account',
      currency: 'INR',
      opening_balance: '1000.00',
    });

    // Validate structure
    expect(account).toHaveProperty('id');
    expect(account).toHaveProperty('name', 'Test Account');
    expect(account).toHaveProperty('currency', 'INR');
    expect(account).toHaveProperty('opening_balance', '1000.00');
    expect(account).toHaveProperty('current_balance');
    expect(account).toHaveProperty('created_at');

    // Validate types
    expect(typeof account.id).toBe('string');
    expect(typeof account.current_balance).toBe('string');
    expect(account.current_balance).toMatch(/^-?\d+\.\d{2}$/);
  });
});
```

---

## Summary

### Contract Stability Benefits

1. **Parallel Development**
   - Frontend and backend teams work independently
   - Mock data matches production structure
   - Integration happens smoothly

2. **Type Safety**
   - TypeScript definitions prevent errors
   - IDE autocomplete works correctly
   - Catch mistakes at compile time

3. **Testing**
   - Contract tests ensure compliance
   - Mock servers use same schema
   - E2E tests validate end-to-end flow

4. **Documentation**
   - Single source of truth
   - Always up-to-date
   - Developers know exactly what to expect

5. **Versioning**
   - Breaking changes are explicit
   - Old clients continue working
   - Gradual migration possible

### Key Takeaways

 **Human-readable amounts** (`"500.00"` not `50000`)
 **Explicit currency** (always include ISO 4217 code)
 **User from auth token** (not in request body)
 **ISO standards** (dates, timestamps, currency codes)
 **Detailed validation** (prevent bad data early)
 **Rich error messages** (help developers debug)
 **Type-safe** (use TypeScript definitions)

**Next steps:** Implement these contracts in FastAPI with Pydantic validation!
