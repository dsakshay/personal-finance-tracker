# Request Flow Guide: Account Endpoints

## Overview

This document explains **step-by-step** what happens when a request hits the account endpoints, from the moment a client sends an HTTP request to when they receive a response.

Understanding this flow is critical for:
- **Debugging**: Know where errors can occur
- **Performance**: Identify bottlenecks
- **Security**: Understand authorization checks
- **Data transformation**: Track format conversions

---

## Table of Contents

1. [POST /accounts - Create Account](#post-accounts---create-account)
2. [GET /accounts - List Accounts](#get-accounts---list-accounts)
3. [Common Layers](#common-layers)
4. [Data Transformations](#data-transformations)
5. [Error Handling](#error-handling)

---

## POST /accounts - Create Account

**Purpose:** Create a new account for the authenticated user

### Request Example

```http
POST /api/v1/accounts HTTP/1.1
Host: api.example.com
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "name": "Emergency Fund",
  "currency": "INR",
  "opening_balance": "50000.00"
}
```

### Complete Flow (13 Steps)

#### Layer 1: HTTP Server (Uvicorn)

**Step 1: Receive Request**
```
Client → Uvicorn (ASGI server)
- Receives raw HTTP request
- Parses headers, body
- Creates ASGI scope dictionary
```

**What's happening:**
- Uvicorn listens on port 8000
- TCP socket receives bytes
- HTTP parser extracts method, path, headers, body

#### Layer 2: FastAPI Middleware

**Step 2: CORS Middleware**
```
Uvicorn → CORS Middleware
- Checks request origin
- Adds CORS headers if configured
- Allows/blocks cross-origin requests
```

**Code location:** [main.py:31-37](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/main.py#L31-L37)

**What's happening:**
- Browser sends `Origin: https://app.example.com`
- Middleware checks if origin is in `settings.cors_origins`
- Adds `Access-Control-Allow-Origin` header

**Step 3: Route Matching**
```
Middleware → FastAPI Router
- Matches path: /api/v1/accounts
- Matches method: POST
- Finds endpoint: create_account()
```

**Code location:** [main.py:66](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/main.py#L66)

**What's happening:**
```python
# FastAPI matches this route registration
app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["Accounts"])

# To this endpoint definition
@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(...):
```

#### Layer 3: Dependency Injection

**Step 4: Extract Authorization Token**
```
FastAPI → HTTPBearer security scheme
- Extracts "Authorization" header
- Validates format: "Bearer <token>"
- Passes to get_current_user dependency
```

**Code location:** [dependencies.py:16-17](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/core/dependencies.py#L16-L17)

**What's happening:**
```python
security = HTTPBearer()  # Looks for "Authorization: Bearer ..." header

credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
# FastAPI extracts: credentials.credentials = "eyJhbGc..."
```

**Step 5: Decode JWT Token**
```
get_current_user → decode_access_token()
- Decodes JWT using secret key
- Verifies signature
- Extracts user_id from payload
```

**Code location:** [dependencies.py:52](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/core/dependencies.py#L52)

**What's happening:**
```python
# JWT token contains:
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",  # user_id
  "exp": 1736689800  # expiration timestamp
}

user_id = decode_access_token(token)
# Returns: UUID("550e8400-e29b-41d4-a716-446655440000")
```

**Step 6: Fetch User from Database**
```
get_current_user → Database query
- Query: SELECT * FROM users WHERE id = ?
- Returns User model instance
- Raises 401 if user not found
```

**Code location:** [dependencies.py:62](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/core/dependencies.py#L62)

**SQL Generated:**
```sql
SELECT users.id, users.email, users.password_hash, users.created_at
FROM users
WHERE users.id = '550e8400-e29b-41d4-a716-446655440000'
LIMIT 1;
```

**Step 7: Create Database Session**
```
FastAPI → get_db() dependency
- Creates SQLAlchemy Session
- Manages connection pool
- Returns session object
```

**Code location:** Referenced via `Depends(get_db)`

**What's happening:**
```python
# Connection pool managed by SQLAlchemy Engine
# Session created from SessionLocal factory
# Will be closed automatically after request
```

#### Layer 4: Request Validation

**Step 8: Parse and Validate Request Body**
```
FastAPI → Pydantic (AccountCreate schema)
- Parses JSON body
- Validates each field
- Runs custom validators
- Raises 422 if invalid
```

**Code location:** [schemas/account.py:13-140](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/schemas/account.py#L13-L140)

**Validation steps:**
```python
# Input JSON:
{
  "name": "Emergency Fund",
  "currency": "INR",
  "opening_balance": "50000.00"
}

# Pydantic validates:
1. name: "Emergency Fund"
   → validate_name(): Not empty/whitespace ✓

2. currency: "INR"
   → validate_currency():
     - Uppercase ✓
     - 3 letters ✓
     - In valid_currencies ✓

3. opening_balance: "50000.00"
   → validate_opening_balance():
     - Valid decimal ✓
     - Exactly 2 decimal places ✓
     - Within range ✓

# Creates AccountCreate instance with validated data
```

#### Layer 5: Business Logic (Endpoint Handler)

**Step 9: Convert to Minor Units**
```
create_account() → account_data.to_minor_units()
- Converts decimal string to integer
- "50000.00" → 5000000 paise
```

**Code location:** [routers/accounts.py:65](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/accounts.py#L65)

**Calculation:**
```python
opening_balance = "50000.00"
decimal_value = Decimal("50000.00")  # = 50000.00
minor_units = int(decimal_value * 100)  # = 5000000 paise
```

**Step 10: Create Account Model**
```
create_account() → Account(...)
- Creates SQLAlchemy model instance
- Sets user_id from authenticated user
- Sets validated fields
- Generates UUID (in database)
```

**Code location:** [routers/accounts.py:69-74](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/accounts.py#L69-L74)

**What's happening:**
```python
new_account = Account(
    user_id=UUID("550e8400-e29b-41d4-a716-446655440000"),  # From JWT!
    name="Emergency Fund",
    currency="INR",
    opening_balance_minor=5000000,  # Integer, not decimal
)

# SQLAlchemy creates Python object (not yet in DB)
# id and created_at will be generated on insert
```

#### Layer 6: Database Persistence

**Step 11: Save to Database**
```
db.add() → db.commit() → db.refresh()
- Add to session (transactional)
- Execute INSERT query
- Reload to get auto-generated fields
```

**Code location:** [routers/accounts.py:77-79](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/accounts.py#L77-L79)

**SQL Generated:**
```sql
-- db.add(new_account) - stages for insert
-- db.commit() - executes this:

INSERT INTO accounts (id, user_id, name, currency, opening_balance_minor, created_at)
VALUES (
  '660e8400-e29b-41d4-a716-446655440111',  -- Generated UUID
  '550e8400-e29b-41d4-a716-446655440000',  -- From JWT token
  'Emergency Fund',
  'INR',
  5000000,
  '2026-01-12 10:30:00+00'  -- Generated timestamp
)
RETURNING id, created_at;

-- db.refresh(new_account) - reloads from DB
SELECT * FROM accounts WHERE id = '660e8400-e29b-41d4-a716-446655440111';
```

#### Layer 7: Response Serialization

**Step 12: Convert to Response Format**
```
AccountResponse.from_db_model() → Convert minor units to decimal strings
- 5000000 paise → "50000.00"
- current_balance = opening_balance (no transactions yet)
```

**Code location:** [schemas/account.py:159-187](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/schemas/account.py#L159-L187)

**Transformation:**
```python
# Database model (internal):
Account(
    id=UUID("660e8400-e29b-41d4-a716-446655440111"),
    user_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
    name="Emergency Fund",
    currency="INR",
    opening_balance_minor=5000000,  # Integer
    created_at=datetime(2026, 1, 12, 10, 30, 0, tzinfo=UTC),
)

# API response (external):
AccountResponse(
    id=UUID("660e8400-e29b-41d4-a716-446655440111"),
    name="Emergency Fund",
    currency="INR",
    opening_balance="50000.00",  # Decimal string
    current_balance="50000.00",  # Decimal string
    created_at=datetime(2026, 1, 12, 10, 30, 0, tzinfo=UTC),
)
```

**Step 13: Return HTTP Response**
```
FastAPI → JSON serialization → HTTP response
- Serialize to JSON
- Add status code: 201 Created
- Add Content-Type: application/json
- Send to client
```

**HTTP Response:**
```http
HTTP/1.1 201 Created
Content-Type: application/json
Content-Length: 234

{
  "id": "660e8400-e29b-41d4-a716-446655440111",
  "name": "Emergency Fund",
  "currency": "INR",
  "opening_balance": "50000.00",
  "current_balance": "50000.00",
  "created_at": "2026-01-12T10:30:00Z"
}
```

### Flow Diagram

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ POST /api/v1/accounts
       │ Authorization: Bearer <token>
       │ {"name": "Emergency Fund", "currency": "INR", "opening_balance": "50000.00"}
       ▼
┌──────────────────────────────────────────────────┐
│ Layer 1: HTTP Server (Uvicorn)                  │
│ - Receive TCP request                            │
│ - Parse HTTP                                     │
└──────┬───────────────────────────────────────────┘
       ▼
┌──────────────────────────────────────────────────┐
│ Layer 2: FastAPI Middleware                     │
│ - CORS checks                                    │
│ - Route matching: /api/v1/accounts → POST       │
└──────┬───────────────────────────────────────────┘
       ▼
┌──────────────────────────────────────────────────┐
│ Layer 3: Dependency Injection                   │
│ ┌────────────────────────────────────────┐      │
│ │ HTTPBearer:                             │      │
│ │   Extract "Bearer eyJhbG..." token      │      │
│ └──────┬─────────────────────────────────┘      │
│        ▼                                         │
│ ┌────────────────────────────────────────┐      │
│ │ get_current_user():                     │      │
│ │   1. Decode JWT → user_id               │      │
│ │   2. Query DB → User model              │      │
│ │   3. Return current_user                │      │
│ └──────┬─────────────────────────────────┘      │
│        ▼                                         │
│ ┌────────────────────────────────────────┐      │
│ │ get_db():                               │      │
│ │   Create database session               │      │
│ └────────────────────────────────────────┘      │
└──────┬───────────────────────────────────────────┘
       ▼
┌──────────────────────────────────────────────────┐
│ Layer 4: Request Validation (Pydantic)          │
│ ┌────────────────────────────────────────┐      │
│ │ AccountCreate schema:                   │      │
│ │   name: "Emergency Fund" ✓              │      │
│ │   currency: "INR" ✓                     │      │
│ │   opening_balance: "50000.00" ✓         │      │
│ └────────────────────────────────────────┘      │
└──────┬───────────────────────────────────────────┘
       ▼
┌──────────────────────────────────────────────────┐
│ Layer 5: Business Logic (create_account)        │
│ 1. Convert: "50000.00" → 5000000 paise          │
│ 2. Create Account model                         │
│    - user_id from JWT (not request!)            │
│    - opening_balance_minor = 5000000            │
└──────┬───────────────────────────────────────────┘
       ▼
┌──────────────────────────────────────────────────┐
│ Layer 6: Database (PostgreSQL)                  │
│ INSERT INTO accounts (...)                       │
│ VALUES ('Emergency Fund', 'INR', 5000000, ...)  │
│ RETURNING id, created_at                        │
└──────┬───────────────────────────────────────────┘
       ▼
┌──────────────────────────────────────────────────┐
│ Layer 7: Response Serialization                 │
│ Convert: 5000000 paise → "50000.00"             │
│ AccountResponse → JSON                          │
└──────┬───────────────────────────────────────────┘
       ▼
┌──────────────┐
│ 201 Created  │
│ {            │
│   "id": "...",
│   "name": "Emergency Fund",
│   "currency": "INR",
│   "opening_balance": "50000.00",
│   "current_balance": "50000.00"
│ }            │
└──────────────┘
```

---

## GET /accounts - List Accounts

**Purpose:** Retrieve all accounts for the authenticated user with current balances

### Request Example

```http
GET /api/v1/accounts?currency=INR HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Complete Flow (14 Steps)

#### Layers 1-4: Same as POST (Authentication & Validation)

**Steps 1-7:** Same as POST /accounts
- HTTP server receives request
- CORS middleware
- Route matching
- Extract & decode JWT token
- Fetch user from database
- Create database session
- Query parameters parsed

**Step 8: Parse Query Parameters**
```
FastAPI → Query parameter parsing
- Extract: currency="INR"
- Optional parameter (can be None)
```

**Code location:** [routers/accounts.py:90](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/accounts.py#L90)

#### Layer 5: Business Logic

**Step 9: Query Accounts with Filters**
```
list_accounts() → Database query
- Filter by user_id (security!)
- Optional filter by currency
- Order by created_at descending
```

**Code location:** [routers/accounts.py:127-134](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/accounts.py#L127-L134)

**SQL Generated:**
```sql
SELECT accounts.id, accounts.user_id, accounts.name,
       accounts.currency, accounts.opening_balance_minor, accounts.created_at
FROM accounts
WHERE accounts.user_id = '550e8400-e29b-41d4-a716-446655440000'
  AND accounts.currency = 'INR'  -- If currency filter provided
ORDER BY accounts.created_at DESC;

-- Example result:
-- id | user_id | name | currency | opening_balance_minor | created_at
-- 660...111 | 550...000 | Emergency Fund | INR | 5000000 | 2026-01-12 10:30:00
-- 770...222 | 550...000 | Checking | INR | 500000 | 2026-01-01 08:00:00
```

**Step 10: Calculate Current Balance (Per Account)**
```
For each account → Query transaction sum
- Query: SELECT SUM(amount_minor) FROM transactions WHERE account_id = ?
- Add to opening balance
```

**Code location:** [routers/accounts.py:141-148](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/accounts.py#L141-L148)

**SQL Generated (per account):**
```sql
-- For account 660...111:
SELECT SUM(transactions.amount_minor) AS sum_1
FROM transactions
WHERE transactions.account_id = '660e8400-e29b-41d4-a716-446655440111';

-- Example result: -180050 (expenses - income)

-- Calculate current balance:
current_balance_minor = opening_balance_minor + transaction_sum
                      = 5000000 + (-180050)
                      = 4819950 paise
                      = ₹48199.50
```

**Performance Note:**
```
⚠️ N+1 Query Problem
- 1 query to fetch all accounts
- N queries to calculate balance (one per account)

With 10 accounts: 1 + 10 = 11 queries
With 100 accounts: 1 + 100 = 101 queries

Future optimization:
- Use JOIN with GROUP BY
- Or implement cached balances (ADR-004)
```

**Step 11: Convert Each Account to Response Format**
```
For each account → AccountResponse.from_db_model()
- Convert minor units to decimal strings
- Format: "48199.50"
```

**Code location:** [routers/accounts.py:151-153](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/accounts.py#L151-L153)

**Transformation (per account):**
```python
# Database models:
[
  Account(id=UUID("660...111"), opening_balance_minor=5000000, ...),
  Account(id=UUID("770...222"), opening_balance_minor=500000, ...),
]

# With calculated balances:
[
  (Account(...), current_balance_minor=4819950),
  (Account(...), current_balance_minor=785025),
]

# API responses:
[
  AccountResponse(
    id=UUID("660...111"),
    opening_balance="50000.00",
    current_balance="48199.50",
    ...
  ),
  AccountResponse(
    id=UUID("770...222"),
    opening_balance="5000.00",
    current_balance="7850.25",
    ...
  ),
]
```

**Step 12: Wrap in List Response**
```
list_accounts() → AccountListResponse
- Combine accounts array
- Add total_count
```

**Code location:** [routers/accounts.py:156-159](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/accounts.py#L156-L159)

**Step 13: Serialize to JSON**
```
FastAPI → JSON serialization
- Serialize UUIDs to strings
- Serialize datetimes to ISO 8601
- Return 200 OK
```

**Step 14: Return HTTP Response**

**HTTP Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 487

{
  "accounts": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440111",
      "name": "Emergency Fund",
      "currency": "INR",
      "opening_balance": "50000.00",
      "current_balance": "48199.50",
      "created_at": "2026-01-12T10:30:00Z"
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440222",
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

### Flow Diagram

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ GET /api/v1/accounts?currency=INR
       │ Authorization: Bearer <token>
       ▼
┌──────────────────────────────────────────────────┐
│ Layers 1-4: Same as POST                        │
│ - HTTP parsing                                   │
│ - Authentication (JWT)                           │
│ - Get current_user from DB                      │
│ - Parse query params: currency="INR"            │
└──────┬───────────────────────────────────────────┘
       ▼
┌──────────────────────────────────────────────────┐
│ Layer 5: Query Accounts                         │
│ SELECT * FROM accounts                           │
│ WHERE user_id = ? AND currency = ?              │
│ ORDER BY created_at DESC                        │
│                                                  │
│ Result: [Account1, Account2]                    │
└──────┬───────────────────────────────────────────┘
       ▼
┌──────────────────────────────────────────────────┐
│ Layer 6: Calculate Balances (Loop)              │
│ ┌────────────────────────────────────────┐      │
│ │ For Account1:                           │      │
│ │   SELECT SUM(amount_minor)              │      │
│ │   FROM transactions                     │      │
│ │   WHERE account_id = Account1.id        │      │
│ │   → transaction_sum = -180050           │      │
│ │   → current = 5000000 + (-180050)       │      │
│ │             = 4819950                   │      │
│ └────────────────────────────────────────┘      │
│ ┌────────────────────────────────────────┐      │
│ │ For Account2:                           │      │
│ │   SELECT SUM(amount_minor) ...          │      │
│ │   → transaction_sum = 285025            │      │
│ │   → current = 500000 + 285025           │      │
│ │             = 785025                    │      │
│ └────────────────────────────────────────┘      │
└──────┬───────────────────────────────────────────┘
       ▼
┌──────────────────────────────────────────────────┐
│ Layer 7: Convert to Response Format             │
│ For each account:                                │
│   4819950 paise → "48199.50"                    │
│   785025 paise → "7850.25"                      │
│                                                  │
│ Wrap in AccountListResponse:                    │
│   {accounts: [...], total_count: 2}             │
└──────┬───────────────────────────────────────────┘
       ▼
┌──────────────┐
│ 200 OK       │
│ {            │
│   "accounts": [...]
│   "total_count": 2
│ }            │
└──────────────┘
```

---

## Common Layers

### 1. FastAPI Dependency Injection

**What it is:**
- Pattern for injecting shared resources into endpoints
- Executed before endpoint handler runs
- Can have nested dependencies

**Example:**
```python
@router.post("")
def create_account(
    account_data: AccountCreate,          # Dependency: Request body validation
    current_user: CurrentUser,            # Dependency: get_current_user()
    db: Annotated[Session, Depends(get_db)],  # Dependency: Database session
):
    # All dependencies resolved before this runs
    pass
```

**Execution order:**
```
1. HTTPBearer extracts token
2. get_current_user(credentials, db):
   2a. get_db() creates session
   2b. decode_access_token(token)
   2c. Query user from DB
3. Pydantic validates account_data
4. create_account() runs with all dependencies injected
```

### 2. Database Session Management

**What it is:**
- SQLAlchemy Session manages database connection
- Connection pooling for performance
- Automatic cleanup after request

**Code location:** `app.core.database.get_db()`

**Flow:**
```python
def get_db():
    db = SessionLocal()  # Get connection from pool
    try:
        yield db  # Endpoint uses this
    finally:
        db.close()  # Return connection to pool
```

**Connection lifecycle:**
```
Request starts
  ↓
get_db() creates session
  ↓
Endpoint queries database
  ↓
Response sent
  ↓
get_db() closes session (automatic cleanup)
```

### 3. Authentication Flow

**What it is:**
- Extract user identity from JWT token
- Verify token signature and expiration
- Load user from database

**Code location:** [dependencies.py:20-71](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/core/dependencies.py#L20-L71)

**Security checks:**
```
1. Token present in header?
   ❌ → 401 Unauthorized

2. Token format valid? (Bearer <token>)
   ❌ → 401 Unauthorized

3. Signature valid? (JWT verification)
   ❌ → 401 Unauthorized

4. Token expired?
   ❌ → 401 Unauthorized

5. User exists in database?
   ❌ → 401 Unauthorized

✅ → Return User object
```

---

## Data Transformations

### Human-Readable ↔ Minor Units

**Why we do this:**
- **Database:** Stores integers (no floating-point precision issues)
- **API:** Returns decimal strings (human-readable, JSON-safe)
- **Precision:** Exact money calculations

**Transformation points:**

#### Request → Database (POST /accounts)

```
Client sends:          "50000.00"  (string)
                            ↓
Pydantic validates:    Decimal("50000.00")
                            ↓
to_minor_units():      5000000  (int)
                            ↓
Database stores:       5000000  (bigint)
```

**Code:**
```python
# schemas/account.py
def to_minor_units(self) -> int:
    decimal_value = Decimal(self.opening_balance)  # "50000.00" → Decimal
    return int(decimal_value * 100)  # Decimal * 100 → 5000000
```

#### Database → Response (GET /accounts)

```
Database stores:       5000000  (bigint)
                            ↓
Query returns:         5000000  (int)
                            ↓
from_db_model():       Decimal(5000000) / 100 = Decimal("50000.00")
                            ↓
Format:                f"{50000.00:.2f}" = "50000.00"
                            ↓
JSON serializes:       "50000.00"  (string)
                            ↓
Client receives:       "50000.00"  (string)
```

**Code:**
```python
# schemas/account.py
@classmethod
def from_db_model(cls, account, current_balance_minor):
    opening_decimal = Decimal(account.opening_balance_minor) / 100
    current_decimal = Decimal(current_balance_minor) / 100

    return cls(
        opening_balance=f"{opening_decimal:.2f}",  # "50000.00"
        current_balance=f"{current_decimal:.2f}",  # "48199.50"
    )
```

### Why Decimal Strings (Not Numbers)?

**Problem with JSON numbers:**
```javascript
// JavaScript loses precision
0.1 + 0.2 === 0.3  // false! (equals 0.30000000000000004)

// Large integers lose precision
9007199254740993 === 9007199254740992  // true! (same number)
```

**Solution: Decimal strings**
```javascript
// Exact representation
const amount = "50000.00";  // No precision loss

// Parsing for display
parseFloat("50000.00").toFixed(2);  // "50000.00"

// Arithmetic (use library)
import Decimal from 'decimal.js';
new Decimal("50000.00").minus("1800.50").toString();  // "48199.50"
```

---

## Error Handling

### Error Types and Responses

#### 1. Validation Errors (400 Bad Request)

**When:** Pydantic validation fails

**Example:**
```json
// Request:
{
  "name": "",
  "currency": "INVALID",
  "opening_balance": "100.5"  // Wrong format
}

// Response: 400 Bad Request
{
  "error": "validation_error",
  "message": "Invalid request data",
  "details": {
    "name": ["Account name cannot be empty or only whitespace"],
    "currency": ["Unsupported currency 'INVALID'. Supported: AUD, CAD, ..."],
    "opening_balance": ["Opening balance must have exactly 2 decimal places"]
  }
}
```

**Code location:** [main.py:42](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/main.py#L42)

#### 2. Authentication Errors (401 Unauthorized)

**When:** Missing, invalid, or expired JWT token

**Example:**
```json
// Request: Missing Authorization header

// Response: 401 Unauthorized
{
  "error": "unauthorized",
  "message": "Missing or invalid authentication token"
}
```

**Code location:** [dependencies.py:55-59](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/core/dependencies.py#L55-L59)

#### 3. Database Errors (500 Internal Server Error)

**When:** Database connection fails, constraint violation, etc.

**Example:**
```json
// Database is down

// Response: 500 Internal Server Error
{
  "error": "database_error",
  "message": "Database connection failed"
}
```

**Code location:** [main.py:43](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/main.py#L43)

### Error Flow

```
Request
  ↓
┌─────────────────────────────────┐
│ Layer 1: HTTP Parsing           │
│ Error → 400 Bad Request         │
└─────────────────────────────────┘
  ↓
┌─────────────────────────────────┐
│ Layer 2: Authentication         │
│ Error → 401 Unauthorized        │
└─────────────────────────────────┘
  ↓
┌─────────────────────────────────┐
│ Layer 3: Request Validation     │
│ Error → 422 Unprocessable       │
└─────────────────────────────────┘
  ↓
┌─────────────────────────────────┐
│ Layer 4: Business Logic         │
│ Error → 400/409/422             │
└─────────────────────────────────┘
  ↓
┌─────────────────────────────────┐
│ Layer 5: Database               │
│ Error → 500 Internal Error      │
└─────────────────────────────────┘
```

---

## Performance Considerations

### Current Implementation

**POST /accounts:**
- ✅ Single INSERT query
- ✅ Efficient (O(1) database operations)

**GET /accounts:**
- ⚠️ N+1 query problem
- 1 query for accounts
- N queries for balances (one per account)
- Total: 1 + N queries

### N+1 Problem Example

```python
# Current implementation:
accounts = db.query(Account).filter(...).all()  # 1 query

for account in accounts:  # N queries
    transaction_sum = db.query(func.sum(...)).filter(
        Transaction.account_id == account.id
    ).scalar()
```

**With 10 accounts:**
- 1 query to fetch accounts
- 10 queries to calculate balances
- **Total: 11 queries**

**With 100 accounts:**
- **Total: 101 queries**

### Future Optimizations

#### Option 1: JOIN with GROUP BY

```sql
SELECT
  a.id,
  a.name,
  a.currency,
  a.opening_balance_minor,
  a.created_at,
  COALESCE(SUM(t.amount_minor), 0) as transaction_sum
FROM accounts a
LEFT JOIN transactions t ON t.account_id = a.id
WHERE a.user_id = ?
GROUP BY a.id
ORDER BY a.created_at DESC;

-- Single query, all balances calculated
```

**Pros:**
- Single query for all data
- Scales well (O(1) queries regardless of account count)

**Cons:**
- More complex SQL
- Requires understanding of aggregation

#### Option 2: Cached Balances (ADR-004)

```python
# Add to Account model:
cached_balance_minor: Mapped[int] = mapped_column(BigInteger, default=0)
balance_updated_at: Mapped[datetime] = mapped_column(...)

# Update on every transaction
def create_transaction(...):
    # ... create transaction
    account.cached_balance_minor += transaction.amount_minor
    account.balance_updated_at = utcnow()
```

**Pros:**
- O(1) query (no aggregation needed)
- Very fast reads

**Cons:**
- Eventual consistency issues
- More complex write logic
- Requires migration strategy

---

## Summary

### Key Takeaways

1. **Request Flow has 7 layers:**
   - HTTP Server (Uvicorn)
   - FastAPI Middleware (CORS)
   - Route Matching
   - Dependency Injection (Auth, DB)
   - Request Validation (Pydantic)
   - Business Logic (Endpoint handler)
   - Database Persistence

2. **Data transformations happen at boundaries:**
   - **API → Internal:** Decimal strings → Minor units (integers)
   - **Internal → API:** Minor units → Decimal strings
   - **Reason:** Precision, JSON compatibility

3. **Security enforced at multiple layers:**
   - **Layer 1:** CORS (cross-origin requests)
   - **Layer 2:** JWT validation (authentication)
   - **Layer 3:** user_id filter (authorization)
   - **Layer 4:** Pydantic validation (input sanitization)

4. **Current performance characteristics:**
   - **POST /accounts:** O(1) queries ✅
   - **GET /accounts:** O(N) queries ⚠️ (N+1 problem)
   - **Future:** Can optimize with JOIN or cached balances

5. **Error handling is comprehensive:**
   - Validation errors → 400/422
   - Authentication errors → 401
   - Business logic errors → 400/409
   - Database errors → 500

### Next Steps

- Implement transaction endpoints (POST /transactions, GET /transactions)
- Optimize GET /accounts with single query
- Add pagination for large account lists
- Implement caching strategy (ADR-004)
