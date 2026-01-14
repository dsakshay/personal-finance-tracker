#  Service Management Scripts

Convenience scripts to manage the Personal Finance Tracker application using Docker Compose.

## Scripts

### `start.sh` - Start all services
```bash
# Development mode (with hot-reload)
./scripts/start.sh

# Production mode (optimized)
./scripts/start.sh prod
```

**Features:**
- Automatically builds and starts all Docker containers
- Development mode: hot-reload enabled, faster iteration
- Production mode: optimized builds, better performance
- Shows service status and URLs when complete

### `stop.sh` - Stop all services
```bash
./scripts/stop.sh
```

**Features:**
- Stops all running containers (dev and prod)
- Asks before removing data volumes
- Preserves your data by default

### `status.sh` - Check service status
```bash
./scripts/status.sh
```

**Features:**
- Shows running services (dev and prod)
- Health checks for database, backend, and frontend
- Resource usage (CPU, memory)
- Direct URLs to access services

## Quick Start

```bash
# 1. Start in development mode
./scripts/start.sh

# 2. Check status
./scripts/status.sh

# 3. Access the application
#    Frontend: http://localhost:3000
#    Backend:  http://localhost:8000

# 4. View logs (in another terminal)
docker-compose -f docker/docker-compose.dev.yml logs -f

# 5. Stop when done
./scripts/stop.sh
```

## Development vs Production

### Development Mode (Default)
- **Start:** `./scripts/start.sh`
- **Hot-reload:** Code changes apply automatically
- **Best for:** Local development and testing
- **Uses:** `docker/docker-compose.dev.yml`

### Production Mode
- **Start:** `./scripts/start.sh prod`
- **Optimized:** Smaller images, better performance
- **Best for:** Testing production builds
- **Uses:** `docker/docker-compose.yml`

## Common Tasks

### View Logs
```bash
# All services
docker-compose -f docker/docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker/docker-compose.dev.yml logs -f backend
docker-compose -f docker/docker-compose.dev.yml logs -f frontend
```

### Rebuild Services
```bash
# Rebuild and restart
./scripts/stop.sh
./scripts/start.sh
```

### Access Database
```bash
# Development database
docker exec -it finance-tracker-db-dev psql -U postgres finance_tracker

# Production database
docker exec -it finance-tracker-db psql -U postgres finance_tracker
```

### Run Migrations
```bash
# Already runs automatically on startup
# But you can run manually if needed:
docker-compose -f docker/docker-compose.dev.yml exec backend alembic upgrade head
```

## Troubleshooting

### Services won't start
```bash
# Check Docker is running
docker info

# Check status
./scripts/status.sh

# View logs for errors
docker-compose -f docker/docker-compose.dev.yml logs
```

### Port conflicts
If ports 3000, 8000, or 5432 are already in use:
```bash
# Find what's using the port
lsof -i :3000

# Stop the conflicting service or modify docker-compose.yml ports
```

### Reset everything
```bash
# Stop and remove all data (️ destructive!)
./scripts/stop.sh
# Answer 'y' when asked about volumes

# Start fresh
./scripts/start.sh
```

## Documentation

For more details, see:
- [docs/README-DOCKER.md](../docs/README-DOCKER.md) - Complete Docker guide
- [docker/README.md](../docker/README.md) - Docker configuration
- [docs/PROJECT-STRUCTURE.md](../docs/PROJECT-STRUCTURE.md) - Project overview
