#!/bin/bash

# Personal Finance Tracker - Docker Start Script
# Starts all services using Docker Compose

set -e

echo "🚀 Starting Personal Finance Tracker (Docker)..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to project root
cd "$(dirname "$0")/.."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Parse arguments
BUILD_FLAG=""
MODE="dev"

for arg in "$@"; do
    case $arg in
        prod|production)
            MODE="prod"
            ;;
        build|--build)
            BUILD_FLAG="--build"
            ;;
    esac
done

# Determine which compose file to use
COMPOSE_FILE="docker/docker-compose.dev.yml"
if [ "$MODE" = "prod" ]; then
    COMPOSE_FILE="docker/docker-compose.yml"
    echo -e "${YELLOW}Starting in PRODUCTION mode${NC}"
else
    echo -e "${YELLOW}Starting in DEVELOPMENT mode (with hot-reload)${NC}"
    echo "  Tip: Use './scripts/start.sh prod' for production mode"
fi

# Start services
if [ -n "$BUILD_FLAG" ]; then
    echo -e "\n${YELLOW}Building and starting services...${NC}"
else
    echo -e "\n${YELLOW}Starting services (skipping build for speed)...${NC}"
    echo "  Tip: Use './scripts/start.sh build' to rebuild images"
fi
docker-compose -f "$COMPOSE_FILE" up -d $BUILD_FLAG

# Wait for services to be healthy
echo -e "\n${YELLOW}Waiting for services to be ready...${NC}"
sleep 5

# Check status
echo -e "\n${GREEN}✅ Services started!${NC}\n"

# Show running containers
docker-compose -f "$COMPOSE_FILE" ps

echo ""
echo "📊 Service URLs:"
echo "  • Frontend:  http://localhost:3000"
echo "  • Backend:   http://localhost:8000"
echo "  • API Docs:  http://localhost:8000/docs"
echo ""
echo "📝 View logs:"
echo "  docker-compose -f $COMPOSE_FILE logs -f"
echo ""
echo "🛑 To stop:"
echo "  ./scripts/stop.sh"
