# 📁 Project Structure

## Overview

```
personal-finance-tracker/
├── backend/              # FastAPI backend application
│   ├── app/             # Application code
│   ├── alembic/         # Database migrations
│   ├── tests/           # Backend tests
│   └── pyproject.toml   # Python dependencies
│
├── frontend/            # Next.js frontend application
│   ├── src/            # Source code
│   │   ├── app/        # App router pages
│   │   ├── components/ # React components
│   │   └── lib/        # Utilities and API client
│   ├── public/         # Static assets
│   └── package.json    # Node dependencies
│
├── docker/             # Docker configuration
│   ├── backend/
│   │   ├── Dockerfile       # Production backend image
│   │   └── Dockerfile.dev   # Development backend image
│   ├── frontend/
│   │   ├── Dockerfile       # Production frontend image
│   │   └── Dockerfile.dev   # Development frontend image
│   ├── docker-compose.yml      # Production setup
│   ├── docker-compose.dev.yml  # Development setup
│   ├── .env.example            # Environment template
│   └── README.md               # Docker quick start
│
├── docs/               # Documentation
│   ├── README-DOCKER.md        # Complete Docker guide
│   ├── README-SCRIPTS.md       # Service management scripts
│   └── PROJECT-STRUCTURE.md    # This file
│
├── logs/               # Application logs (gitignored)
│
├── start.sh           # Start all services (local)
├── stop.sh            # Stop all services (local)
└── status.sh          # Check service status (local)
```

## Key Directories

### `/backend`
The FastAPI backend with PostgreSQL database integration.

**Key files:**
- `app/main.py` - Application entry point
- `app/routers/` - API endpoints
- `app/models/` - SQLAlchemy models
- `app/services/` - Business logic
- `alembic/` - Database migrations

**Running locally:**
```bash
cd backend
.venv/bin/uvicorn app.main:app --reload
```

### `/frontend`
The Next.js frontend with React Query for data fetching.

**Key files:**
- `src/app/` - Pages and layouts (App Router)
- `src/components/ui/` - Reusable UI components
- `src/lib/api/` - API client and types
- `src/app/globals.css` - Global styles

**Running locally:**
```bash
cd frontend
npm run dev
```

### `/docker`
All Docker-related configuration files.

**Usage:**
```bash
# Development
docker-compose -f docker/docker-compose.dev.yml up -d

# Production
docker-compose -f docker/docker-compose.yml up -d
```

See [docker/README.md](../docker/README.md) for quick start.

### `/docs`
Project documentation.

- **README-DOCKER.md** - Complete Docker deployment guide
- **README-SCRIPTS.md** - Local service management scripts
- **PROJECT-STRUCTURE.md** - This file

## Running the Application

### Option 1: Local Scripts (Simple)
```bash
./start.sh   # Start all services
./status.sh  # Check status
./stop.sh    # Stop all services
```

### Option 2: Docker Compose (Recommended)
```bash
# Development with hot-reload
docker-compose -f docker/docker-compose.dev.yml up -d

# Production optimized
docker-compose -f docker/docker-compose.yml up -d
```

### Option 3: Manual (Advanced)
```bash
# Terminal 1: Database
docker start finance-postgres

# Terminal 2: Backend
cd backend
.venv/bin/uvicorn app.main:app --reload

# Terminal 3: Frontend
cd frontend
npm run dev
```

## Development Workflow

1. **Make changes** to backend or frontend code
2. **Services auto-reload** (if using dev mode)
3. **Database migrations:**
   ```bash
   cd backend
   .venv/bin/alembic revision --autogenerate -m "description"
   .venv/bin/alembic upgrade head
   ```
4. **Test changes** at http://localhost:3000

## Port Usage

- **3000** - Frontend (Next.js)
- **8000** - Backend (FastAPI)
- **5432** - PostgreSQL database

## Data Persistence

### Docker Volume
- **Name:** `docker_postgres_data` or `finance-tracker-data`
- **Location:** Managed by Docker
- **Survives:** Container restarts, Docker restart
- **Lost when:** Volume explicitly deleted

### Local Development
- Database data in PostgreSQL data directory
- Persists until PostgreSQL is uninstalled or data directory deleted

## Environment Variables

### Backend
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret key

### Frontend
- `NEXT_PUBLIC_API_BASE_URL` - Backend API URL

Set in:
- `backend/.env` (local)
- `docker/.env` (Docker)

## Tech Stack

### Backend
- **Framework:** FastAPI
- **Database:** PostgreSQL 15
- **ORM:** SQLAlchemy
- **Migrations:** Alembic
- **Auth:** JWT tokens
- **Validation:** Pydantic

### Frontend
- **Framework:** Next.js 16
- **React:** React 19
- **Styling:** TailwindCSS 4
- **Data Fetching:** React Query (TanStack Query)
- **TypeScript:** Full type safety

### DevOps
- **Containerization:** Docker
- **Orchestration:** Docker Compose
- **Development:** Hot-reload for both services
- **Production:** Optimized multi-stage builds

## Quick Reference

| Task | Command |
|------|---------|
| Start everything | `./start.sh` or `docker-compose -f docker/docker-compose.dev.yml up -d` |
| Stop everything | `./stop.sh` or `docker-compose -f docker/docker-compose.dev.yml down` |
| Check status | `./status.sh` or `docker-compose -f docker/docker-compose.dev.yml ps` |
| View logs | `tail -f logs/backend.log` or `docker-compose -f docker/docker-compose.dev.yml logs -f` |
| Run migrations | `cd backend && .venv/bin/alembic upgrade head` |
| Access database | `docker exec -it finance-tracker-db psql -U postgres finance_tracker` |
| Frontend URL | http://localhost:3000 |
| Backend URL | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

## Next Steps

- Read [README-DOCKER.md](README-DOCKER.md) for Docker deployment
- Read [README-SCRIPTS.md](README-SCRIPTS.md) for local scripts
- Check [docker/README.md](../docker/README.md) for Docker quick start
