# Backend Architecture

Technical architecture documentation for the Personal Finance Tracker backend.

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Language** | Python | 3.11+ |
| **Web Framework** | FastAPI | 0.109+ |
| **ORM** | SQLAlchemy | 2.0+ |
| **Database** | PostgreSQL | 14+ |
| **Migrations** | Alembic | 1.13+ |
| **Authentication** | JWT (python-jose) | 3.3+ |
| **Password Hashing** | Passlib (bcrypt) | 1.7+ |
| **Validation** | Pydantic | 2.5+ |

---

## Project Structure

```
backend/
├── app/
│   ├── core/                  # Core utilities
│   │   ├── config.py          # Settings from environment
│   │   ├── database.py        # Database engine & session
│   │   ├── security.py        # JWT & password hashing
│   │   ├── dependencies.py    # FastAPI dependencies
│   │   ├── exceptions.py      # Custom exceptions
│   │   ├── error_handlers.py  # Global exception handlers
│   │   └── validators.py      # Validation helpers
│   │
│   ├── models/                # SQLAlchemy models
│   │   ├── user.py            # User model
│   │   ├── account.py         # Account model
│   │   └── transaction.py     # Transaction model
│   │
│   ├── schemas/               # Pydantic schemas
│   │   ├── user.py            # User schemas
│   │   ├── account.py         # Account schemas
│   │   ├── transaction.py     # Transaction schemas
│   │   └── summary.py         # Summary schemas
│   │
│   ├── routers/               # API route handlers
│   │   ├── auth.py            # Authentication routes
│   │   ├── accounts.py        # Account routes
│   │   ├── transactions.py    # Transaction routes
│   │   └── summary.py         # Summary routes
│   │
│   └── main.py                # FastAPI application
│
├── alembic/                   # Database migrations
│   ├── versions/              # Migration scripts
│   └── env.py                 # Alembic environment
│
├── .env                       # Environment variables (not committed)
├── .env.example               # Environment template
├── pyproject.toml             # Dependencies (Poetry)
└── alembic.ini                # Alembic configuration
```

---

## Architectural Layers

### Layer 1: API Layer (FastAPI)

**Responsibilities:**
- HTTP request/response handling
- Route definition
- OpenAPI documentation
- CORS middleware
- Exception handling

**Files:** `app/main.py`, `app/routers/*.py`

**Example:**
```python
@router.post("/accounts", response_model=AccountRead)
def create_account(
    account_data: AccountCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    # Route handler logic
    pass
```

---

### Layer 2: Validation Layer (Pydantic)

**Responsibilities:**
- Input validation
- Type coercion
- Format validation
- Custom validators
- Response serialization

**Files:** `app/schemas/*.py`

**Example:**
```python
class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    currency: str = Field(..., min_length=3, max_length=3)
    opening_balance: Decimal = Field(default=Decimal("0.00"))

    @field_validator("currency")
    def validate_currency(cls, v: str) -> str:
        return v.upper()
```

---

### Layer 3: Business Logic Layer

**Responsibilities:**
- Business rule enforcement
- Authorization checks
- Data transformation
- Validation orchestration

**Files:** `app/core/validators.py`, route handlers

**Example:**
```python
def validate_transfer_accounts(db, from_id, to_id, user):
    # Check accounts are different
    # Check both belong to user
    # Check currencies match
    return from_account, to_account
```

---

### Layer 4: Data Access Layer (SQLAlchemy)

**Responsibilities:**
- Database queries
- ORM mapping
- Transactions
- Connection pooling

**Files:** `app/models/*.py`, `app/core/database.py`

**Example:**
```python
class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(100))
```

---

### Layer 5: Database Layer (PostgreSQL)

**Responsibilities:**
- Data persistence
- ACID guarantees
- Constraints enforcement
- Indexing

**Managed by:** Alembic migrations

---

## Data Flow

### Request Flow (Create Transaction)

```
1. CLIENT
   POST /api/v1/transactions
   Authorization: Bearer <token>
   { "amount": -100.50, ... }

2. FASTAPI MIDDLEWARE
   ├─ CORS check
   ├─ Authentication (HTTPBearer)
   └─ Extract token

3. DEPENDENCY INJECTION
   ├─ get_current_user(token)
   │  ├─ Decode JWT
   │  ├─ Fetch user from DB
   │  └─ Return User object
   └─ get_db()
      └─ Return DB session

4. PYDANTIC VALIDATION
   TransactionCreate schema:
   ├─ Type validation (Decimal, UUID, etc.)
   ├─ Field validators (currency, amount, date)
   └─ Convert to Python objects

5. ROUTE HANDLER
   create_transaction():
   ├─ Business validation
   │  ├─ validate_transaction_date()
   │  ├─ validate_account_ownership()
   │  └─ validate_currency_match()
   ├─ Convert amount to minor units
   ├─ Create Transaction model
   └─ Save to database

6. DATABASE
   PostgreSQL:
   ├─ BEGIN TRANSACTION
   ├─ INSERT INTO transactions
   ├─ Check constraints
   └─ COMMIT

7. RESPONSE SERIALIZATION
   TransactionRead schema:
   ├─ Convert minor units to decimal
   ├─ Format dates
   └─ Return JSON

8. CLIENT
   201 Created
   { "id": "...", "amount": -100.50, ... }
```

---

## Authentication Flow

```
┌─────────────┐
│   SIGNUP    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Hash password   │ ← bcrypt (one-way, salted)
│ Store in DB     │
└──────┬──────────┘
       │
       ▼
┌─────────────┐
│   LOGIN     │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Verify password │ ← bcrypt.verify()
│ Generate JWT    │ ← Sign with SECRET_KEY
└──────┬──────────┘
       │
       ▼
┌─────────────────────────┐
│ Client stores token     │
│ in localStorage/cookie  │
└──────┬──────────────────┘
       │
       │ All subsequent requests:
       │ Authorization: Bearer <token>
       ▼
┌────────────────────────┐
│ get_current_user()     │
│ ├─ Extract token       │
│ ├─ Verify signature    │
│ ├─ Check expiration    │
│ ├─ Extract user_id     │
│ └─ Fetch User from DB  │
└────────────────────────┘
```

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

### Accounts Table
```sql
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    opening_balance_minor BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_accounts_user_id ON accounts(user_id);
```

### Transactions Table
```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    amount_minor BIGINT NOT NULL,
    currency VARCHAR(3) NOT NULL,
    transaction_type transaction_type_enum NOT NULL,
    tag VARCHAR(50) NOT NULL,
    payment_method VARCHAR(50),
    related_account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
    description VARCHAR(255),
    transaction_date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_account_id ON transactions(account_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);
CREATE INDEX idx_transactions_tag ON transactions(tag);
```

---

## Design Patterns

### 1. Dependency Injection

FastAPI's dependency injection provides:
- Automatic session management
- User authentication
- Reusable components

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/accounts")
def list_accounts(
    db: Session = Depends(get_db),          # Injected
    current_user: User = Depends(get_current_user)  # Injected
):
    return db.query(Account).filter(Account.user_id == current_user.id).all()
```

### 2. Repository Pattern (Implicit)

SQLAlchemy ORM acts as repositories:
- Models represent entities
- Query API provides data access
- Transactions manage consistency

### 3. DTO (Data Transfer Objects)

Pydantic schemas are DTOs:
- Separate input/output representations
- Validation at boundaries
- Type safety

```python
# Input DTO
class AccountCreate(BaseModel):
    name: str
    currency: str
    opening_balance: Decimal

# Output DTO
class AccountRead(BaseModel):
    id: uuid.UUID
    name: str
    currency: str
    opening_balance: Decimal
    created_at: datetime
```

### 4. Service Layer Pattern (Light)

Validators act as service functions:
- Reusable validation logic
- Business rule enforcement
- Cross-cutting concerns

---

## Security Architecture

### 1. Authentication (JWT)

- Stateless tokens
- HMAC-SHA256 signing
- 30-minute expiration
- User ID in payload

### 2. Authorization

- User-scoped queries
- Ownership validation
- Resource isolation

### 3. Input Validation

- Pydantic schemas (type safety)
- Custom validators (business rules)
- Database constraints (data integrity)

### 4. Error Handling

- Consistent error format
- Proper HTTP status codes
- No information leakage

---

## Configuration Management

Environment variables via `.env` file:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/finance_tracker

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

Loaded via Pydantic Settings:
```python
class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    # ...

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

---

## Testing Strategy (Future)

```
tests/
├── unit/
│   ├── test_validators.py
│   ├── test_security.py
│   └── test_schemas.py
├── integration/
│   ├── test_auth_routes.py
│   ├── test_account_routes.py
│   └── test_transaction_routes.py
└── e2e/
    └── test_user_flows.py
```

---

## Performance Considerations

### Current (MVP)
- On-demand aggregations
- No caching
- Simple queries
- Connection pooling

### Future Optimizations (Phase 2+)
- Cached monthly summaries
- Materialized views
- Redis caching
- Read replicas

---

## Deployment Architecture (Future)

```
┌─────────────┐
│   Nginx     │ ← Reverse proxy
└──────┬──────┘
       │
┌──────▼──────┐
│  Uvicorn    │ ← ASGI server (multiple workers)
│  FastAPI    │
└──────┬──────┘
       │
┌──────▼──────┐
│ PostgreSQL  │ ← Primary database
└─────────────┘
```

---

## See Also

- [API Reference](./api-reference.md)
- [Error Handling](./error-handling.md)
- [Architectural Decisions](../decisions.md)
- [Development Roadmap](../roadmap.md)
