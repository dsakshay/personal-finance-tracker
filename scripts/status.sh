#!/bin/bash

# Personal Finance Tracker - Docker Status Script
# Checks the status of Docker Compose services

echo "📊 Personal Finance Tracker - Service Status"
echo "=============================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Change to project root
cd "$(dirname "$0")/.."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    exit 1
fi

# Check development services
echo -e "\n${YELLOW}Development Services:${NC}"
DEV_CONTAINERS=$(docker-compose -f docker/docker-compose.dev.yml ps -q 2>/dev/null)
if [ -z "$DEV_CONTAINERS" ]; then
    echo -e "  Status: ${RED}✗ Not running${NC}"
else
    echo -e "  Status: ${GREEN}✓ Running${NC}"
    docker-compose -f docker/docker-compose.dev.yml ps
fi

# Check production services
echo -e "\n${YELLOW}Production Services:${NC}"
PROD_CONTAINERS=$(docker-compose -f docker/docker-compose.yml ps -q 2>/dev/null)
if [ -z "$PROD_CONTAINERS" ]; then
    echo -e "  Status: ${RED}✗ Not running${NC}"
else
    echo -e "  Status: ${GREEN}✓ Running${NC}"
    docker-compose -f docker/docker-compose.yml ps
fi

# Show individual service health
if [ -n "$DEV_CONTAINERS" ] || [ -n "$PROD_CONTAINERS" ]; then
    echo -e "\n${YELLOW}Service Health Checks:${NC}"

    # Check database
    if docker ps --filter "name=finance-tracker-db" --format "{{.Names}}" | grep -q "finance-tracker-db"; then
        echo -e "  PostgreSQL: ${GREEN}✓ Running${NC}"
        if docker exec finance-tracker-db-dev pg_isready -U postgres > /dev/null 2>&1 || \
           docker exec finance-tracker-db pg_isready -U postgres > /dev/null 2>&1; then
            echo -e "              ${GREEN}✓ Accepting connections${NC}"
        fi
    fi

    # Check backend
    if docker ps --filter "name=finance-tracker-backend" --format "{{.Names}}" | grep -q "finance-tracker-backend"; then
        echo -e "  Backend:    ${GREEN}✓ Running${NC}"
        if curl -s http://localhost:8000 > /dev/null 2>&1; then
            echo -e "              ${GREEN}✓ Responding (http://localhost:8000)${NC}"
        else
            echo -e "              ${YELLOW}⚠ Starting up...${NC}"
        fi
    fi

    # Check frontend
    if docker ps --filter "name=finance-tracker-frontend" --format "{{.Names}}" | grep -q "finance-tracker-frontend"; then
        echo -e "  Frontend:   ${GREEN}✓ Running${NC}"
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo -e "              ${GREEN}✓ Responding (http://localhost:3000)${NC}"
        else
            echo -e "              ${YELLOW}⚠ Starting up...${NC}"
        fi
    fi
fi

# Show resource usage
echo -e "\n${YELLOW}Resource Usage:${NC}"
if [ -n "$DEV_CONTAINERS" ] || [ -n "$PROD_CONTAINERS" ]; then
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" \
        $(docker ps --filter "name=finance-tracker" -q) 2>/dev/null
fi

echo ""
echo "=============================================="
echo ""
echo "💡 Commands:"
echo "  Start:  ./scripts/start.sh       # Development"
echo "          ./scripts/start.sh prod  # Production"
echo "  Stop:   ./scripts/stop.sh"
echo "  Logs:   docker-compose -f docker/docker-compose.dev.yml logs -f"
