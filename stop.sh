#!/bin/bash

# Personal Finance Tracker - Shutdown Script
# This script stops all running services

echo "🛑 Stopping Personal Finance Tracker..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Stop Frontend
echo -e "\n${YELLOW}[1/3] Stopping Frontend...${NC}"
if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        echo "✓ Frontend stopped (PID: $FRONTEND_PID)"
    else
        echo "⚠ Frontend process not running"
    fi
    rm logs/frontend.pid
else
    echo "⚠ No frontend PID file found"
    # Try to kill by name
    pkill -f "next dev" && echo "✓ Killed running Next.js processes" || echo "⚠ No Next.js processes found"
fi

# 2. Stop Backend
echo -e "\n${YELLOW}[2/3] Stopping Backend...${NC}"
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        echo "✓ Backend stopped (PID: $BACKEND_PID)"
    else
        echo "⚠ Backend process not running"
    fi
    rm logs/backend.pid
else
    echo "⚠ No backend PID file found"
    # Try to kill by name
    pkill -f "uvicorn app.main:app" && echo "✓ Killed running uvicorn processes" || echo "⚠ No uvicorn processes found"
fi

# 3. Stop PostgreSQL (optional - you might want to keep it running)
echo -e "\n${YELLOW}[3/3] Stopping PostgreSQL...${NC}"
read -p "Do you want to stop PostgreSQL Docker container? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker stop finance-postgres
    echo "✓ PostgreSQL stopped"
else
    echo "⚠ PostgreSQL left running"
fi

echo -e "\n${GREEN}✅ Services stopped${NC}"
echo ""
echo "💡 To start again, run: ./start.sh"
