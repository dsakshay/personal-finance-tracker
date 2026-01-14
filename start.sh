#!/bin/bash

# Personal Finance Tracker - Startup Script
# This script starts all required services

set -e

echo "🚀 Starting Personal Finance Tracker..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Start PostgreSQL Docker container
echo -e "\n${YELLOW}[1/3] Starting PostgreSQL...${NC}"
if [ "$(docker ps -q -f name=finance-postgres)" ]; then
    echo "✓ PostgreSQL already running"
else
    docker start finance-postgres || {
        echo "⚠ Container not found, creating new one..."
        docker run -d \
            --name finance-postgres \
            -e POSTGRES_PASSWORD=postgres \
            -e POSTGRES_DB=finance_tracker \
            -p 5432:5432 \
            -v finance-tracker-data:/var/lib/postgresql/data \
            postgres:15
    }
    echo "✓ PostgreSQL started"
fi

# Wait for PostgreSQL to be ready
echo "  Waiting for PostgreSQL to be ready..."
sleep 3

# 2. Start Backend (FastAPI)
echo -e "\n${YELLOW}[2/3] Starting Backend (FastAPI)...${NC}"
cd backend
if [ ! -d ".venv" ]; then
    echo "⚠ Virtual environment not found. Please run: python3 -m venv .venv && .venv/bin/pip install poetry && .venv/bin/poetry install"
    exit 1
fi

# Run migrations
echo "  Running database migrations..."
.venv/bin/alembic upgrade head

# Start backend in background
echo "  Starting uvicorn server..."
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../logs/backend.pid
echo "✓ Backend started (PID: $BACKEND_PID)"
cd ..

# 3. Start Frontend (Next.js)
echo -e "\n${YELLOW}[3/3] Starting Frontend (Next.js)...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    echo "⚠ Dependencies not found. Please run: npm install"
    exit 1
fi

npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid
echo "✓ Frontend started (PID: $FRONTEND_PID)"
cd ..

# Summary
echo -e "\n${GREEN}✅ All services started successfully!${NC}"
echo ""
echo "📊 Service URLs:"
echo "  • Frontend:  http://localhost:3000"
echo "  • Backend:   http://localhost:8000"
echo "  • API Docs:  http://localhost:8000/docs"
echo "  • PostgreSQL: localhost:5432"
echo ""
echo "📝 Logs:"
echo "  • Backend:  tail -f logs/backend.log"
echo "  • Frontend: tail -f logs/frontend.log"
echo ""
echo "🛑 To stop all services, run: ./stop.sh"
