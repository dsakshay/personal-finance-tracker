 Request Flow Guide: Account Endpoints

 Overview

This document explains step-by-step what happens when a request hits the account endpoints, from the moment a client sends an HTTP request to when they receive a response.

Understanding this flow is critical for:
- Debugging: Know where errors can occur
- Performance: Identify bottlenecks
- Security: Understand authorization checks
- Data transformation: Track format conversions

---

 Table of Contents

. [POST /accounts - Create Account](post-accounts---create-account)
. [GET /accounts - List Accounts](get-accounts---list-accounts)
. [Common Layers](common-layers)
. [Data Transformations](data-transformations)
. [Error Handling](error-handling)

---

 POST /accounts - Create Account

Purpose: Create a new account for the authenticated user

 Request Example

```http
POST /api/v/accounts HTTP/.
Host: api.example.com
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzINiIsInRcCIIkpXVCJ...

{
  "name": "Emergency Fund",
  "currency": "INR",
  "opening_balance": "."
}
```

 Complete Flow ( Steps)

 Layer : HTTP Server (Uvicorn)

Step : Receive Request
```
Client → Uvicorn (ASGI server)
- Receives raw HTTP request
- Parses headers, body
- Creates ASGI scope dictionary
```

What's happening:
- Uvicorn listens on port 
- TCP socket receives bytes
- HTTP parser extracts method, path, headers, body

 Layer : FastAPI Middleware

Step : CORS Middleware
```
Uvicorn → CORS Middleware
- Checks request origin
- Adds CORS headers if configured
- Allows/blocks cross-origin requests
```

Code location: [main.py:-](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/main.pyL-L)

What's happening:
- Browser sends `Origin: https://app.example.com`
- Middleware checks if origin is in `settings.cors_origins`
- Adds `Access-Control-Allow-Origin` header

Step : Route Matching
```
Middleware → FastAPI Router
- Matches path: /api/v/accounts
- Matches method: POST
- Finds endpoint: create_account()
```

Code location: [main.py:](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/main.pyL)

What's happening:
```python
 FastAPI matches this route registration
app.include_router(accounts.router, prefix="/api/v/accounts", tags=["Accounts"])

 To this endpoint definition
@router.post("", response_model=AccountResponse, status_code=status.HTTP__CREATED)
def create_account(...):
```

 Layer : Dependency Injection

Step : Extract Authorization Token
```
FastAPI → HTTPBearer security scheme
- Extracts "Authorization" header
- Validates format: "Bearer <token>"
- Passes to get_current_user dependency
```

Code location: [dependencies.py:-](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/core/dependencies.pyL-L)

What's happening:
```python
security = HTTPBearer()   Looks for "Authorization: Bearer ..." header

credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
 FastAPI extracts: credentials.credentials = "eyJhbGc..."
```

Step : Decode JWT Token
```
get_current_user → decode_access_token()
- Decodes JWT using secret key
- Verifies signature
- Extracts user_id from payload
```

Code location: [dependencies.py:](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/core/dependencies.pyL)

What's happening:
```python
 JWT token contains:
{
  "sub": "e-eb-d-a-",   user_id
  "exp":    expiration timestamp
}

user_id = decode_access_token(token)
 Returns: UUID("e-eb-d-a-")
```

Step : Fetch User from Database
```
get_current_user → Database query
- Query: SELECT  FROM users WHERE id = ?
- Returns User model instance
- Raises  if user not found
```

Code location: [dependencies.py:](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/core/dependencies.pyL)

SQL Generated:
```sql
SELECT users.id, users.email, users.password_hash, users.created_at
FROM users
WHERE users.id = 'e-eb-d-a-'
LIMIT ;
```

Step : Create Database Session
```
FastAPI → get_db() dependency
- Creates SQLAlchemy Session
- Manages connection pool
- Returns session object
```

Code location: Referenced via `Depends(get_db)`

What's happening:
```python
 Connection pool managed by SQLAlchemy Engine
 Session created from SessionLocal factory
 Will be closed automatically after request
```

 Layer : Request Validation

Step : Parse and Validate Request Body
```
FastAPI → Pydantic (AccountCreate schema)
- Parses JSON body
- Validates each field
- Runs custom validators
- Raises  if invalid
```

Code location: [schemas/account.py:-](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/schemas/account.pyL-L)

Validation steps:
```python
 Input JSON:
{
  "name": "Emergency Fund",
  "currency": "INR",
  "opening_balance": "."
}

 Pydantic validates:
. name: "Emergency Fund"
   → validate_name(): Not empty/whitespace 

. currency: "INR"
   → validate_currency():
     - Uppercase 
     -  letters 
     - In valid_currencies 

. opening_balance: "."
   → validate_opening_balance():
     - Valid decimal 
     - Exactly  decimal places 
     - Within range 

 Creates AccountCreate instance with validated data
```

 Layer : Business Logic (Endpoint Handler)

Step : Convert to Minor Units
```
create_account() → account_data.to_minor_units()
- Converts decimal string to integer
- "." →  paise
```

Code location: [routers/accounts.py:](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/accounts.pyL)

Calculation:
```python
opening_balance = "."
decimal_value = Decimal(".")   = .
minor_units = int(decimal_value  )   =  paise
```

Step : Create Account Model
```
create_account() → Account(...)
- Creates SQLAlchemy model instance
- Sets user_id from authenticated user
- Sets validated fields
- Generates UUID (in database)
```

Code location: [routers/accounts.py:-](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/accounts.pyL-L)

What's happening:
```python
new_account = Account(
    user_id=UUID("e-eb-d-a-"),   From JWT!
    name="Emergency Fund",
    currency="INR",
    opening_balance_minor=,   Integer, not decimal
)

 SQLAlchemy creates Python object (not yet in DB)
 id and created_at will be generated on insert
```

 Layer : Database Persistence

Step : Save to Database
```
db.add() → db.commit() → db.refresh()
- Add to session (transactional)
- Execute INSERT query
- Reload to get auto-generated fields
```

Code location: [routers/accounts.py:-](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/accounts.pyL-L)

SQL Generated:
```sql
-- db.add(new_account) - stages for insert
-- db.commit() - executes this:

INSERT INTO accounts (id, user_id, name, currency, opening_balance_minor, created_at)
VALUES (
  'e-eb-d-a-',  -- Generated UUID
  'e-eb-d-a-',  -- From JWT token
  'Emergency Fund',
  'INR',
  ,
  '-- ::+'  -- Generated timestamp
)
RETURNING id, created_at;

-- db.refresh(new_account) - reloads from DB
SELECT  FROM accounts WHERE id = 'e-eb-d-a-';
```

 Layer : Response Serialization

Step : Convert to Response Format
```
AccountResponse.from_db_model() → Convert minor units to decimal strings
-  paise → "."
- current_balance = opening_balance (no transactions yet)
```

Code location: [schemas/account.py:-](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/schemas/account.pyL-L)

Transformation:
```python
 Database model (internal):
Account(
    id=UUID("e-eb-d-a-"),
    user_id=UUID("e-eb-d-a-"),
    name="Emergency Fund",
    currency="INR",
    opening_balance_minor=,   Integer
    created_at=datetime(, , , , , , tzinfo=UTC),
)

 API response (external):
AccountResponse(
    id=UUID("e-eb-d-a-"),
    name="Emergency Fund",
    currency="INR",
    opening_balance=".",   Decimal string
    current_balance=".",   Decimal string
    created_at=datetime(, , , , , , tzinfo=UTC),
)
```

Step : Return HTTP Response
```
FastAPI → JSON serialization → HTTP response
- Serialize to JSON
- Add status code:  Created
- Add Content-Type: application/json
- Send to client
```

HTTP Response:
```http
HTTP/.  Created
Content-Type: application/json
Content-Length: 

{
  "id": "e-eb-d-a-",
  "name": "Emergency Fund",
  "currency": "INR",
  "opening_balance": ".",
  "current_balance": ".",
  "created_at": "--T::Z"
}
```

 Flow Diagram

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ POST /api/v/accounts
       │ Authorization: Bearer <token>
       │ {"name": "Emergency Fund", "currency": "INR", "opening_balance": "."}
       ▼
┌──────────────────────────────────────────────────┐
│ Layer : HTTP Server (Uvicorn)                  │
│ - Receive TCP request                            │
│ - Parse HTTP                                     │
└──────┬───────────────────────────────────────────┘
       ▼
┌──────────────────────────────────────────────────┐
│ Layer : FastAPI Middleware                     │
│ - CORS checks                                    │
│ - Route matching: /api/v/accounts → POST       │
└──────┬───────────────────────────────────────────┘
       ▼
┌──────────────────────────────────────────────────┐
│ Layer : Dependency Injection                   │
│ ┌────────────────────────────────────────┐      │
│ │ HTTPBearer:                             │      │
│ │   Extract "Bearer eyJhbG..." token      │      │
│ └──────┬─────────────────────────────────┘      │
│        ▼                                         │
│ ┌────────────────────────────────────────┐      │
│ │ get_current_user():                     │      │
│ │   . Decode JWT → user_id               │      │
│ │   . Query DB → User model              │      │
│ │   . Return current_user                │      │
│ └──────┬─────────────────────────────────┘      │
│        ▼                                         │
│ ┌────────────────────────────────────────┐      │
│ │ get_db():                               │      │
│ │   Create database session               │      │
│ └────────────────────────────────────────┘      │
└──────┬───────────────────────────────────────────┘
       ▼
┌──────────────────────────────────────────────────┐
│ Layer : Request Validation (Pydantic)          │
│ ┌────────────────────────────────────────┐      │
│ │ AccountCreate schema:                   │      │
│ │   name: "Emergency Fund"               │      │
│ │   currency: "INR"                      │      │
│ │   opening_balance: "."          │      │
│ └────────────────────────────────────────┘      │
└──────┬───────────────────────────────────────────┘
       ▼
┌──────────────────────────────────────────────────┐
│ Layer : Business Logic (create_account)        │
│ . Convert: "." →  paise          │
│ . Create Account model                         │
│    - user_id from JWT (not request!)            │
│    - opening_balance_minor =             │
└──────┬───────────────────────────────────────────┘
       ▼
┌──────────────────────────────────────────────────┐
│ Layer : Database (PostgreSQL)                  │
│ INSERT INTO accounts (...)                       │
│ VALUES ('Emergency Fund', 'INR', , ...)  │
│ RETURNING id, created_at                        │
└──────┬───────────────────────────────────────────┘
       ▼
┌──────────────────────────────────────────────────┐
│ Layer : Response Serialization                 │
│ Convert:  paise → "."             │
│ AccountResponse → JSON                          │
└──────┬───────────────────────────────────────────┘
       ▼
┌──────────────┐
│  Created  │
│ {            │
│   "id": "...",
│   "name": "Emergency Fund",
│   "currency": "INR",
│   "opening_balance": ".",
│   "current_balance": "."
│ }            │
└──────────────┘
```

---

 GET /accounts - List Accounts

Purpose: Retrieve all accounts for the authenticated user with current balances

 Request Example

```http
GET /api/v/accounts?currency=INR HTTP/.
Host: api.example.com
Authorization: Bearer eyJhbGciOiJIUzINiIsInRcCIIkpXVCJ...
```

 Complete Flow ( Steps)

 Layers -: Same as POST (Authentication & Validation)

Steps -: Same as POST /accounts
- HTTP server receives request
- CORS middleware
- Route matching
- Extract & decode JWT token
- Fetch user from database
- Create database session
- Query parameters parsed

Step : Parse Query Parameters
```
FastAPI → Query parameter parsing
- Extract: currency="INR"
- Optional parameter (can be None)
```

Code location: [routers/accounts.py:](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/accounts.pyL)

 Layer : Business Logic

Step : Query Accounts with Filters
```
list_accounts() → Database query
- Filter by user_id (security!)
- Optional filter by currency
- Order by created_at descending
```

Code location: [routers/accounts.py:-](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/accounts.pyL-L)

SQL Generated:
```sql
SELECT accounts.id, accounts.user_id, accounts.name,
       accounts.currency, accounts.opening_balance_minor, accounts.created_at
FROM accounts
WHERE accounts.user_id = 'e-eb-d-a-'
  AND accounts.currency = 'INR'  -- If currency filter provided
ORDER BY accounts.created_at DESC;

-- Example result:
-- id | user_id | name | currency | opening_balance_minor | created_at
-- ... | ... | Emergency Fund | INR |  | -- ::
-- ... | ... | Checking | INR |  | -- ::
```

Step : Calculate Current Balance (Per Account)
```
For each account → Query transaction sum
- Query: SELECT SUM(amount_minor) FROM transactions WHERE account_id = ?
- Add to opening balance
```

Code location: [routers/accounts.py:-](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/accounts.pyL-L)

SQL Generated (per account):
```sql
-- For account ...:
SELECT SUM(transactions.amount_minor) AS sum_
FROM transactions
WHERE transactions.account_id = 'e-eb-d-a-';

-- Example result: - (expenses - income)

-- Calculate current balance:
current_balance_minor = opening_balance_minor + transaction_sum
                      =  + (-)
                      =  paise
                      = ₹.
```

Performance Note:
```
️ N+ Query Problem
-  query to fetch all accounts
- N queries to calculate balance (one per account)

With  accounts:  +  =  queries
With  accounts:  +  =  queries

Future optimization:
- Use JOIN with GROUP BY
- Or implement cached balances (ADR-)
```

Step : Convert Each Account to Response Format
```
For each account → AccountResponse.from_db_model()
- Convert minor units to decimal strings
- Format: "."
```

Code location: [routers/accounts.py:-](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/accounts.pyL-L)

Transformation (per account):
```python
 Database models:
[
  Account(id=UUID("..."), opening_balance_minor=, ...),
  Account(id=UUID("..."), opening_balance_minor=, ...),
]

 With calculated balances:
[
  (Account(...), current_balance_minor=),
  (Account(...), current_balance_minor=),
]

 API responses:
[
  AccountResponse(
    id=UUID("..."),
    opening_balance=".",
    current_balance=".",
    ...
  ),
  AccountResponse(
    id=UUID("..."),
    opening_balance=".",
    current_balance=".",
    ...
  ),
]
```

Step : Wrap in List Response
```
list_accounts() → AccountListResponse
- Combine accounts array
- Add total_count
```

Code location: [routers/accounts.py:-](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/routers/accounts.pyL-L)

Step : Serialize to JSON
```
FastAPI → JSON serialization
- Serialize UUIDs to strings
- Serialize datetimes to ISO 
- Return  OK
```

Step : Return HTTP Response

HTTP Response:
```http
HTTP/.  OK
Content-Type: application/json
Content-Length: 

{
  "accounts": [
    {
      "id": "e-eb-d-a-",
      "name": "Emergency Fund",
      "currency": "INR",
      "opening_balance": ".",
      "current_balance": ".",
      "created_at": "--T::Z"
    },
    {
      "id": "e-eb-d-a-",
      "name": "Checking",
      "currency": "INR",
      "opening_balance": ".",
      "current_balance": ".",
      "created_at": "--T::Z"
    }
  ],
  "total_count": 
}
```

 Flow Diagram

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ GET /api/v/accounts?currency=INR
       │ Authorization: Bearer <token>
       ▼
┌──────────────────────────────────────────────────┐
│ Layers -: Same as POST                        │
│ - HTTP parsing                                   │
│ - Authentication (JWT)                           │
│ - Get current_user from DB                      │
│ - Parse query params: currency="INR"            │
└──────┬───────────────────────────────────────────┘
       ▼
┌──────────────────────────────────────────────────┐
│ Layer : Query Accounts                         │
│ SELECT  FROM accounts                           │
│ WHERE user_id = ? AND currency = ?              │
│ ORDER BY created_at DESC                        │
│                                                  │
│ Result: [Account, Account]                    │
└──────┬───────────────────────────────────────────┘
       ▼
┌──────────────────────────────────────────────────┐
│ Layer : Calculate Balances (Loop)              │
│ ┌────────────────────────────────────────┐      │
│ │ For Account:                           │      │
│ │   SELECT SUM(amount_minor)              │      │
│ │   FROM transactions                     │      │
│ │   WHERE account_id = Account.id        │      │
│ │   → transaction_sum = -           │      │
│ │   → current =  + (-)       │      │
│ │             =                    │      │
│ └────────────────────────────────────────┘      │
│ ┌────────────────────────────────────────┐      │
│ │ For Account:                           │      │
│ │   SELECT SUM(amount_minor) ...          │      │
│ │   → transaction_sum =             │      │
│ │   → current =  +            │      │
│ │             =                     │      │
│ └────────────────────────────────────────┘      │
└──────┬───────────────────────────────────────────┘
       ▼
┌──────────────────────────────────────────────────┐
│ Layer : Convert to Response Format             │
│ For each account:                                │
│    paise → "."                    │
│    paise → "."                      │
│                                                  │
│ Wrap in AccountListResponse:                    │
│   {accounts: [...], total_count: }             │
└──────┬───────────────────────────────────────────┘
       ▼
┌──────────────┐
│  OK       │
│ {            │
│   "accounts": [...]
│   "total_count": 
│ }            │
└──────────────┘
```

---

 Common Layers

 . FastAPI Dependency Injection

What it is:
- Pattern for injecting shared resources into endpoints
- Executed before endpoint handler runs
- Can have nested dependencies

Example:
```python
@router.post("")
def create_account(
    account_data: AccountCreate,           Dependency: Request body validation
    current_user: CurrentUser,             Dependency: get_current_user()
    db: Annotated[Session, Depends(get_db)],   Dependency: Database session
):
     All dependencies resolved before this runs
    pass
```

Execution order:
```
. HTTPBearer extracts token
. get_current_user(credentials, db):
   a. get_db() creates session
   b. decode_access_token(token)
   c. Query user from DB
. Pydantic validates account_data
. create_account() runs with all dependencies injected
```

 . Database Session Management

What it is:
- SQLAlchemy Session manages database connection
- Connection pooling for performance
- Automatic cleanup after request

Code location: `app.core.database.get_db()`

Flow:
```python
def get_db():
    db = SessionLocal()   Get connection from pool
    try:
        yield db   Endpoint uses this
    finally:
        db.close()   Return connection to pool
```

Connection lifecycle:
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

 . Authentication Flow

What it is:
- Extract user identity from JWT token
- Verify token signature and expiration
- Load user from database

Code location: [dependencies.py:-](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/core/dependencies.pyL-L)

Security checks:
```
. Token present in header?
    →  Unauthorized

. Token format valid? (Bearer <token>)
    →  Unauthorized

. Signature valid? (JWT verification)
    →  Unauthorized

. Token expired?
    →  Unauthorized

. User exists in database?
    →  Unauthorized

 → Return User object
```

---

 Data Transformations

 Human-Readable  Minor Units

Why we do this:
- Database: Stores integers (no floating-point precision issues)
- API: Returns decimal strings (human-readable, JSON-safe)
- Precision: Exact money calculations

Transformation points:

 Request → Database (POST /accounts)

```
Client sends:          "."  (string)
                            ↓
Pydantic validates:    Decimal(".")
                            ↓
to_minor_units():        (int)
                            ↓
Database stores:         (bigint)
```

Code:
```python
 schemas/account.py
def to_minor_units(self) -> int:
    decimal_value = Decimal(self.opening_balance)   "." → Decimal
    return int(decimal_value  )   Decimal   → 
```

 Database → Response (GET /accounts)

```
Database stores:         (bigint)
                            ↓
Query returns:           (int)
                            ↓
from_db_model():       Decimal() /  = Decimal(".")
                            ↓
Format:                f"{.:.f}" = "."
                            ↓
JSON serializes:       "."  (string)
                            ↓
Client receives:       "."  (string)
```

Code:
```python
 schemas/account.py
@classmethod
def from_db_model(cls, account, current_balance_minor):
    opening_decimal = Decimal(account.opening_balance_minor) / 
    current_decimal = Decimal(current_balance_minor) / 

    return cls(
        opening_balance=f"{opening_decimal:.f}",   "."
        current_balance=f"{current_decimal:.f}",   "."
    )
```

 Why Decimal Strings (Not Numbers)?

Problem with JSON numbers:
```javascript
// JavaScript loses precision
. + . === .  // false! (equals .)

// Large integers lose precision
 ===   // true! (same number)
```

Solution: Decimal strings
```javascript
// Exact representation
const amount = ".";  // No precision loss

// Parsing for display
parseFloat(".").toFixed();  // "."

// Arithmetic (use library)
import Decimal from 'decimal.js';
new Decimal(".").minus(".").toString();  // "."
```

---

 Error Handling

 Error Types and Responses

 . Validation Errors ( Bad Request)

When: Pydantic validation fails

Example:
```json
// Request:
{
  "name": "",
  "currency": "INVALID",
  "opening_balance": "."  // Wrong format
}

// Response:  Bad Request
{
  "error": "validation_error",
  "message": "Invalid request data",
  "details": {
    "name": ["Account name cannot be empty or only whitespace"],
    "currency": ["Unsupported currency 'INVALID'. Supported: AUD, CAD, ..."],
    "opening_balance": ["Opening balance must have exactly  decimal places"]
  }
}
```

Code location: [main.py:](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/main.pyL)

 . Authentication Errors ( Unauthorized)

When: Missing, invalid, or expired JWT token

Example:
```json
// Request: Missing Authorization header

// Response:  Unauthorized
{
  "error": "unauthorized",
  "message": "Missing or invalid authentication token"
}
```

Code location: [dependencies.py:-](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/core/dependencies.pyL-L)

 . Database Errors ( Internal Server Error)

When: Database connection fails, constraint violation, etc.

Example:
```json
// Database is down

// Response:  Internal Server Error
{
  "error": "database_error",
  "message": "Database connection failed"
}
```

Code location: [main.py:](/home/akshay/personal-meta/personal-projects/apps/personal-finance-tracker/backend/app/main.pyL)

 Error Flow

```
Request
  ↓
┌─────────────────────────────────┐
│ Layer : HTTP Parsing           │
│ Error →  Bad Request         │
└─────────────────────────────────┘
  ↓
┌─────────────────────────────────┐
│ Layer : Authentication         │
│ Error →  Unauthorized        │
└─────────────────────────────────┘
  ↓
┌─────────────────────────────────┐
│ Layer : Request Validation     │
│ Error →  Unprocessable       │
└─────────────────────────────────┘
  ↓
┌─────────────────────────────────┐
│ Layer : Business Logic         │
│ Error → //             │
└─────────────────────────────────┘
  ↓
┌─────────────────────────────────┐
│ Layer : Database               │
│ Error →  Internal Error      │
└─────────────────────────────────┘
```

---

 Performance Considerations

 Current Implementation

POST /accounts:
-  Single INSERT query
-  Efficient (O() database operations)

GET /accounts:
- N+ query problem
-  query for accounts
- N queries for balances (one per account)
- Total:  + N queries

 N+ Problem Example

```python
 Current implementation:
accounts = db.query(Account).filter(...).all()    query

for account in accounts:   N queries
    transaction_sum = db.query(func.sum(...)).filter(
        Transaction.account_id == account.id
    ).scalar()
```

With  accounts:
-  query to fetch accounts
-  queries to calculate balances
- Total:  queries

With  accounts:
- Total:  queries

 Future Optimizations

 Option : JOIN with GROUP BY

```sql
SELECT
  a.id,
  a.name,
  a.currency,
  a.opening_balance_minor,
  a.created_at,
  COALESCE(SUM(t.amount_minor), ) as transaction_sum
FROM accounts a
LEFT JOIN transactions t ON t.account_id = a.id
WHERE a.user_id = ?
GROUP BY a.id
ORDER BY a.created_at DESC;

-- Single query, all balances calculated
```

Pros:
- Single query for all data
- Scales well (O() queries regardless of account count)

Cons:
- More complex SQL
- Requires understanding of aggregation

 Option : Cached Balances (ADR-)

```python
 Add to Account model:
cached_balance_minor: Mapped[int] = mapped_column(BigInteger, default=)
balance_updated_at: Mapped[datetime] = mapped_column(...)

 Update on every transaction
def create_transaction(...):
     ... create transaction
    account.cached_balance_minor += transaction.amount_minor
    account.balance_updated_at = utcnow()
```

Pros:
- O() query (no aggregation needed)
- Very fast reads

Cons:
- Eventual consistency issues
- More complex write logic
- Requires migration strategy

---

 Summary

 Key Takeaways

. Request Flow has  layers:
   - HTTP Server (Uvicorn)
   - FastAPI Middleware (CORS)
   - Route Matching
   - Dependency Injection (Auth, DB)
   - Request Validation (Pydantic)
   - Business Logic (Endpoint handler)
   - Database Persistence

. Data transformations happen at boundaries:
   - API → Internal: Decimal strings → Minor units (integers)
   - Internal → API: Minor units → Decimal strings
   - Reason: Precision, JSON compatibility

. Security enforced at multiple layers:
   - Layer : CORS (cross-origin requests)
   - Layer : JWT validation (authentication)
   - Layer : user_id filter (authorization)
   - Layer : Pydantic validation (input sanitization)

. Current performance characteristics:
   - POST /accounts: O() queries 
   - GET /accounts: O(N) queries ️ (N+ problem)
   - Future: Can optimize with JOIN or cached balances

. Error handling is comprehensive:
   - Validation errors → /
   - Authentication errors → 
   - Business logic errors → /
   - Database errors → 

 Next Steps

- Implement transaction endpoints (POST /transactions, GET /transactions)
- Optimize GET /accounts with single query
- Add pagination for large account lists
- Implement caching strategy (ADR-)
