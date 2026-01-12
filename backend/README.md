# Personal Finance Tracker - Backend

FastAPI backend for the Personal Finance Tracker MVP.

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Poetry (recommended) or pip

### Installation

1. **Install dependencies:**
   ```bash
   poetry install
   # or
   pip install -e .
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. **Set up database:**
   ```bash
   # Create database
   createdb finance_tracker

   # Run migrations
   alembic upgrade head
   ```

4. **Run development server:**
   ```bash
   uvicorn app.main:app --reload
   ```

   API: http://localhost:8000
   Docs: http://localhost:8000/docs
   ReDoc: http://localhost:8000/redoc

---

## Documentation

### 📚 Core Documentation
- **[API Reference](../docs/backend/api-reference.md)** - Complete API endpoint documentation
- **[Architecture](../docs/backend/architecture.md)** - System design and technical architecture
- **[Error Handling](../docs/backend/error-handling.md)** - Error scenarios and financial correctness

### 🎯 Scope Management
- **[Scope Boundaries](../docs/backend/scope-boundaries.md)** - What NOT to build yet (prevent scope creep)
- **[MVP Checklist](../docs/backend/mvp-checklist.md)** - Quick reference for scope decisions

### 📖 Project Documentation
- **[Architectural Decisions](../docs/decisions.md)** - Key design decisions (ADRs)
- **[Development Roadmap](../docs/roadmap.md)** - Phased development plan
- **[Main README](../README.md)** - Project overview and goals

---

## Project Structure

```
backend/
├── app/
│   ├── core/                  # Core utilities and config
│   │   ├── config.py          # Environment settings (Pydantic)
│   │   ├── database.py        # SQLAlchemy engine & session
│   │   ├── security.py        # JWT & password hashing
│   │   ├── dependencies.py    # FastAPI dependencies (auth)
│   │   ├── exceptions.py      # Custom exception classes
│   │   ├── error_handlers.py  # Global exception handlers
│   │   └── validators.py      # Validation helpers
│   │
│   ├── models/                # SQLAlchemy ORM models
│   │   ├── user.py            # User authentication
│   │   ├── account.py         # Financial accounts
│   │   └── transaction.py     # Transactions (income/expense/transfer)
│   │
│   ├── schemas/               # Pydantic validation schemas
│   │   ├── user.py            # User request/response schemas
│   │   ├── account.py         # Account schemas
│   │   ├── transaction.py     # Transaction schemas
│   │   └── summary.py         # Summary/aggregation schemas
│   │
│   ├── routers/               # API route handlers
│   │   ├── auth.py            # Authentication (signup/login)
│   │   ├── accounts.py        # Account CRUD
│   │   ├── transactions.py    # Transaction CRUD & transfers
│   │   └── summary.py         # Financial summaries
│   │
│   └── main.py                # FastAPI application entry point
│
├── alembic/                   # Database migrations
│   ├── versions/              # Migration scripts
│   ├── env.py                 # Alembic environment
│   └── README                 # Migration usage guide
│
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── alembic.ini                # Alembic configuration
└── pyproject.toml             # Python dependencies (Poetry)
```

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/finance_tracker

# Security (change SECRET_KEY in production!)
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

---

## API Endpoints

### Authentication
- `POST /api/v1/auth/signup` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user info

### Accounts
- `POST /api/v1/accounts` - Create account
- `GET /api/v1/accounts` - List user's accounts
- `GET /api/v1/accounts/with-balance` - List accounts with balances
- `GET /api/v1/accounts/{id}` - Get single account

### Transactions
- `POST /api/v1/transactions` - Create transaction (income/expense)
- `POST /api/v1/transactions/transfer` - Transfer between accounts
- `GET /api/v1/transactions` - List transactions (with filters)
- `GET /api/v1/transactions/{id}` - Get single transaction

### Summaries
- `GET /api/v1/summary/monthly` - Monthly financial summary

**Full documentation:** [API Reference](../docs/backend/api-reference.md)

---

## Database Migrations

### Create Migration
```bash
alembic revision --autogenerate -m "description of changes"
```

### Apply Migrations
```bash
alembic upgrade head
```

### Rollback One Migration
```bash
alembic downgrade -1
```

### View Current Version
```bash
alembic current
```

### View Migration History
```bash
alembic history
```

---

## Development Workflow

### 1. Make Code Changes
Edit models, schemas, or routes in `app/`

### 2. Create Migration (if models changed)
```bash
alembic revision --autogenerate -m "add new field"
```

### 3. Review Migration
Check `alembic/versions/` for generated SQL

### 4. Apply Migration
```bash
alembic upgrade head
```

### 5. Test
```bash
# Run server
uvicorn app.main:app --reload

# Test endpoints via Swagger UI
open http://localhost:8000/docs
```

---

## Key Features

### ✅ Implemented (MVP)
- **Authentication** - JWT-based auth with bcrypt password hashing
- **User Management** - Registration, login, user isolation
- **Accounts** - Create and manage financial accounts (multiple currencies)
- **Transactions** - Income, expenses, and transfers
- **Atomic Transfers** - Two-transaction model with ACID guarantees
- **Financial Summaries** - Monthly aggregations with tag breakdowns
- **Error Handling** - Comprehensive validation and error responses
- **Currency Validation** - Prevent currency mismatches
- **Authorization** - User-scoped data access
- **API Documentation** - Auto-generated Swagger/ReDoc

### 🚧 Not Yet Implemented
- Balance caching (derived on-demand for MVP)
- Transaction editing (immutable for MVP)
- Recurring transactions
- Budget tracking
- Multi-currency support
- File uploads (receipts)
- Email notifications
- Rate limiting
- Comprehensive test suite

See [Development Roadmap](../docs/roadmap.md) for phased implementation plan.

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.11+ |
| **Web Framework** | FastAPI 0.109+ |
| **ORM** | SQLAlchemy 2.0+ |
| **Database** | PostgreSQL 14+ |
| **Migrations** | Alembic 1.13+ |
| **Authentication** | JWT (python-jose) |
| **Password Hashing** | Passlib (bcrypt) |
| **Validation** | Pydantic 2.5+ |
| **Server** | Uvicorn (ASGI) |

---

## Security Features

- ✅ JWT token authentication with expiration
- ✅ Bcrypt password hashing with salt
- ✅ User data isolation (multi-tenant safe)
- ✅ Input validation (Pydantic schemas)
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ Currency mismatch prevention
- ✅ Cross-user access prevention
- ✅ No password exposure in responses
- ✅ Proper HTTP status codes
- ✅ Error message sanitization

See [Error Handling](../docs/backend/error-handling.md) for security details.

---

## Financial Correctness

- ✅ Integer-based money storage (no floating-point errors)
- ✅ Atomic transfers (both transactions or neither)
- ✅ Currency validation (no mixing INR + USD)
- ✅ Transaction immutability (audit trail preserved)
- ✅ Balance derivation (always accurate, no drift)
- ✅ Zero amount prevention
- ✅ Future date validation
- ✅ User-scoped aggregations

See [Architectural Decisions](../docs/decisions.md) for design rationale.

---

## Troubleshooting

### Database Connection Error
```
Error: could not connect to server
```
**Solution:** Check PostgreSQL is running and credentials in `.env` are correct.

### Migration Conflicts
```
Error: Target database is not up to date
```
**Solution:** Run `alembic upgrade head` to apply pending migrations.

### Import Errors
```
ModuleNotFoundError: No module named 'app'
```
**Solution:** Install dependencies with `poetry install` or `pip install -e .`

### Token Expired
```
401 Unauthorized: Invalid or expired token
```
**Solution:** Login again to get a new token (tokens expire after 30 minutes).

---

## Contributing

1. Follow existing code structure
2. Use type hints for all functions
3. Add docstrings for public APIs
4. Create Alembic migrations for schema changes
5. Update documentation for new features

---

## License

See main project [README](../README.md) for license information.

---

## Support

For questions or issues:
1. Check [Error Handling](../docs/backend/error-handling.md) documentation
2. Review [Architecture](../docs/backend/architecture.md) guide
3. Consult [API Reference](../docs/backend/api-reference.md)
4. Open an issue in the project repository
