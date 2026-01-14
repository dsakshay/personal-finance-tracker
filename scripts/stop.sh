#!/bin/bash

# Personal Finance Tracker - Docker Stop Script
# Stops all Docker Compose services

echo "🛑 Stopping Personal Finance Tracker..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Change to project root
cd "$(dirname "$0")/.."

# Check which services are running
DEV_RUNNING=$(docker-compose -f docker/docker-compose.dev.yml ps -q 2>/dev/null | wc -l)
PROD_RUNNING=$(docker-compose -f docker/docker-compose.yml ps -q 2>/dev/null | wc -l)

STOPPED=false

# Stop dev services if running
if [ "$DEV_RUNNING" -gt 0 ]; then
    echo -e "\n${YELLOW}Stopping development services...${NC}"
    docker-compose -f docker/docker-compose.dev.yml down
    STOPPED=true
fi

# Stop prod services if running
if [ "$PROD_RUNNING" -gt 0 ]; then
    echo -e "\n${YELLOW}Stopping production services...${NC}"
    docker-compose -f docker/docker-compose.yml down
    STOPPED=true
fi

if [ "$STOPPED" = false ]; then
    echo "⚠️  No services were running"
    exit 0
fi

# Ask about removing volumes
echo ""
read -p "Do you want to remove data volumes? (⚠️  THIS WILL DELETE ALL DATA) (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Removing volumes...${NC}"
    docker-compose -f docker/docker-compose.dev.yml down -v 2>/dev/null
    docker-compose -f docker/docker-compose.yml down -v 2>/dev/null
    echo "✓ Volumes removed"
else
    echo "✓ Data preserved"
fi

echo -e "\n${GREEN}✅ Services stopped${NC}"
echo ""
echo "💡 To start again:"
echo "  ./scripts/start.sh       # Development mode"
echo "  ./scripts/start.sh prod  # Production mode"
