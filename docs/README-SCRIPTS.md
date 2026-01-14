# 🚀 Service Management Scripts

This project includes convenience scripts to manage all services (PostgreSQL, Backend, Frontend).

## Quick Start

```bash
# Start all services
./scripts/start.sh

# Check status
./scripts/status.sh

# Stop all services
./scripts/stop.sh
```

## Scripts Overview

### 📦 `start.sh`
Starts all services in the correct order:
1. PostgreSQL (Docker container)
2. Backend (FastAPI with auto-reload)
3. Frontend (Next.js with Turbopack)

**Features:**
- Auto-creates PostgreSQL container if needed
- Runs database migrations automatically
- Logs output to `logs/` directory
- Shows service URLs when complete

**Usage:**
```bash
./scripts/start.sh
```

### 🛑 `stop.sh`
Gracefully stops all services:
1. Frontend (Next.js)
2. Backend (FastAPI)
3. PostgreSQL (optional - asks for confirmation)

**Features:**
- Cleans up PID files
- Asks before stopping PostgreSQL (data persists)
- Fallback to process name if PID missing

**Usage:**
```bash
./scripts/stop.sh
```

### 📊 `status.sh`
Check the status of all services:
- PostgreSQL container status
- Backend API health check
- Frontend web server status
- Process IDs and ports

**Usage:**
```bash
./scripts/status.sh
```

## Service URLs

When running:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **PostgreSQL:** localhost:5432

## Logs

View real-time logs:
```bash
# Backend logs
docker-compose -f docker/docker-compose.dev.yml logs -f backend.log

# Frontend logs
docker-compose -f docker/docker-compose.dev.yml logs -f frontend.log
```

## Data Persistence

✅ **Your data is safe!**
- PostgreSQL uses a Docker volume (`finance-tracker-data`)
- Data persists across container restarts
- Stopping services does NOT delete data

## Troubleshooting

### Services won't start
```bash
# Check what's already running
./scripts/status.sh

# Stop everything and restart
./scripts/stop.sh
./scripts/start.sh
```

### Port already in use
```bash
# Find process using port 3000 or 8000
lsof -i :3000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### PostgreSQL issues
```bash
# Check container logs
docker logs finance-postgres

# Restart container
docker restart finance-postgres
```

### Reset everything (DANGER - deletes data!)
```bash
# Stop all services
./scripts/stop.sh

# Remove PostgreSQL container and volume
docker rm -f finance-postgres
docker volume rm finance-tracker-data

# Start fresh
./scripts/start.sh
```

## Manual Service Management

If you prefer to start services individually:

### PostgreSQL
```bash
# Start
docker start finance-postgres

# Stop
docker stop finance-postgres
```

### Backend
```bash
cd backend
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm run dev
```
