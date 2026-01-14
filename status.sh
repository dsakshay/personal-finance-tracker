#!/bin/bash

# Personal Finance Tracker - Status Check Script
# This script checks the status of all services

echo "📊 Personal Finance Tracker - Service Status"
echo "=============================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check PostgreSQL
echo -e "\n${YELLOW}PostgreSQL (Docker):${NC}"
if [ "$(docker ps -q -f name=finance-postgres)" ]; then
    echo -e "  Status: ${GREEN}✓ Running${NC}"
    docker ps --filter name=finance-postgres --format "  Container: {{.Names}} ({{.Status}})"
else
    echo -e "  Status: ${RED}✗ Not running${NC}"
fi

# Check Backend
echo -e "\n${YELLOW}Backend (FastAPI):${NC}"
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "  Status: ${GREEN}✓ Running${NC} (PID: $BACKEND_PID)"
        if curl -s http://localhost:8000 > /dev/null; then
            echo -e "  API:    ${GREEN}✓ Responding${NC} (http://localhost:8000)"
        else
            echo -e "  API:    ${RED}✗ Not responding${NC}"
        fi
    else
        echo -e "  Status: ${RED}✗ Not running${NC} (stale PID file)"
    fi
else
    echo -e "  Status: ${RED}✗ Not running${NC}"
fi

# Check Frontend
echo -e "\n${YELLOW}Frontend (Next.js):${NC}"
if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "  Status: ${GREEN}✓ Running${NC} (PID: $FRONTEND_PID)"
        if curl -s http://localhost:3000 > /dev/null; then
            echo -e "  Web:    ${GREEN}✓ Responding${NC} (http://localhost:3000)"
        else
            echo -e "  Web:    ${YELLOW}⚠ Starting up...${NC}"
        fi
    else
        echo -e "  Status: ${RED}✗ Not running${NC} (stale PID file)"
    fi
else
    echo -e "  Status: ${RED}✗ Not running${NC}"
fi

echo -e "\n=============================================="
echo ""
echo "💡 Commands:"
echo "  Start all:  ./start.sh"
echo "  Stop all:   ./stop.sh"
echo "  View logs:  tail -f logs/backend.log"
echo "              tail -f logs/frontend.log"
