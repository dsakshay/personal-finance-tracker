# 🐳 Docker Deployment Guide

This project supports both **production** and **development** Docker setups.

## Quick Start

### Production (Optimized)
```bash
# Build and start all services
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop all services
docker-compose -f docker/docker-compose.yml down
```

### Development (Hot-reload)
```bash
# Build and start with hot-reload
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml logs -f

# Stop all services
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml down
```

## Services

The application consists of 3 services:

| Service | Container Name | Port | Description |
|---------|---------------|------|-------------|
| **db** | finance-tracker-db | 5432 | PostgreSQL 15 database |
| **backend** | finance-tracker-backend | 8000 | FastAPI application |
| **frontend** | finance-tracker-frontend | 3000 | Next.js web app |

## Access URLs

Once running:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **PostgreSQL:** localhost:5432

## Production vs Development

### Production (`docker-compose.yml`)
- ✅ Optimized builds
- ✅ Minimal image sizes
- ✅ No source code mounting
- ✅ Best for deployment
- ❌ No hot-reload (requires rebuild for changes)

```bash
docker-compose -f docker/docker-compose.yml up -d --build
```

### Development (`docker/docker-compose.dev.yml`)
- ✅ Hot-reload enabled
- ✅ Source code mounted as volumes
- ✅ Fast iteration
- ✅ Best for local development
- ⚠️ Larger image sizes

```bash
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up -d --build
```

## Common Commands

### Build & Start
```bash
# Production
docker-compose -f docker/docker-compose.yml up -d --build

# Development
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up -d --build
```

### View Logs
```bash
# All services
docker-compose -f docker/docker-compose.yml logs -f

# Specific service
docker-compose -f docker/docker-compose.yml logs -f backend
docker-compose -f docker/docker-compose.yml logs -f frontend
docker-compose -f docker/docker-compose.yml logs -f db
```

### Stop Services
```bash
# Stop (keeps volumes)
docker-compose -f docker/docker-compose.yml down

# Stop and remove volumes (⚠️ deletes data!)
docker-compose -f docker/docker-compose.yml down -v
```

### Rebuild Single Service
```bash
# Rebuild backend
docker-compose -f docker/docker-compose.yml up -d --build backend

# Rebuild frontend
docker-compose -f docker/docker-compose.yml up -d --build frontend
```

### Execute Commands in Containers
```bash
# Backend shell
docker-compose -f docker/docker-compose.yml exec backend bash

# Run migrations manually
docker-compose -f docker/docker-compose.yml exec backend alembic upgrade head

# Frontend shell
docker-compose -f docker/docker-compose.yml exec frontend sh

# Database shell
docker-compose -f docker/docker-compose.yml exec db psql -U postgres -d finance_tracker
```

## Data Persistence

All database data is stored in a Docker volume:
- **Volume name:** `finance-tracker_postgres_data`
- **Location:** Managed by Docker
- **Persistence:** Data survives container restarts

### View Volumes
```bash
docker volume ls | grep finance
```

### Backup Database
```bash
# Export database
docker-compose -f docker/docker-compose.yml exec db pg_dump -U postgres finance_tracker > backup.sql

# Import database
cat backup.sql | docker-compose -f docker/docker-compose.yml exec -T db psql -U postgres finance_tracker
```

### Reset Database (⚠️ Destructive!)
```bash
# Stop services
docker-compose -f docker/docker-compose.yml down

# Remove volume
docker volume rm finance-tracker_postgres_data

# Start fresh
docker-compose -f docker/docker-compose.yml up -d
```

## Environment Variables

Create a `.env` file in the root directory:

```bash
# Copy example
cp docker/.env.example .env

# Edit as needed
nano .env
```

Available variables:
- `SECRET_KEY` - Backend JWT secret (change in production!)
- `POSTGRES_USER` - Database user (default: postgres)
- `POSTGRES_PASSWORD` - Database password (default: postgres)
- `POSTGRES_DB` - Database name (default: finance_tracker)
- `NEXT_PUBLIC_API_BASE_URL` - API URL for frontend (default: http://localhost:8000)

## Troubleshooting

### Services won't start
```bash
# Check status
docker-compose -f docker/docker-compose.yml ps

# View logs for errors
docker-compose -f docker/docker-compose.yml logs

# Rebuild from scratch
docker-compose -f docker/docker-compose.yml down -v
docker-compose -f docker/docker-compose.yml up -d --build
```

### Port already in use
```bash
# Find process using port
lsof -i :3000
lsof -i :8000
lsof -i :5432

# Change ports in docker-compose.yml
# Example: "3001:3000" maps container port 3000 to host port 3001
```

### Database connection issues
```bash
# Check database health
docker-compose -f docker/docker-compose.yml exec db pg_isready -U postgres

# Check logs
docker-compose -f docker/docker-compose.yml logs db

# Restart database
docker-compose -f docker/docker-compose.yml restart db
```

### Frontend can't connect to backend
1. Check backend is running: `curl http://localhost:8000`
2. Verify `NEXT_PUBLIC_API_BASE_URL` in `.env`
3. Check browser console for CORS errors

### Clear everything and start fresh
```bash
# Stop all services
docker-compose -f docker/docker-compose.yml down -v

# Remove images
docker-compose -f docker/docker-compose.yml rm -f
docker rmi finance-tracker-backend finance-tracker-frontend

# Rebuild
docker-compose -f docker/docker-compose.yml up -d --build
```

## Performance Tips

### Reduce build time
```bash
# Use BuildKit
DOCKER_BUILDKIT=1 docker-compose -f docker/docker-compose.yml build

# Build in parallel
docker-compose -f docker/docker-compose.yml build --parallel
```

### View resource usage
```bash
docker stats
```

### Prune unused resources
```bash
# Remove unused containers, networks, images
docker system prune -a

# Remove unused volumes (⚠️ be careful!)
docker volume prune
```

## Migration from Local Setup

If you were running services locally:

1. **Stop local services:**
   ```bash
   ./stop.sh
   ```

2. **Backup your database:**
   ```bash
   pg_dump -U postgres finance_tracker > backup.sql
   ```

3. **Start Docker services:**
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

4. **Restore database (if needed):**
   ```bash
   cat backup.sql | docker-compose -f docker/docker-compose.yml exec -T db psql -U postgres finance_tracker
   ```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Build and Test

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build services
        run: docker-compose -f docker/docker-compose.yml build
      - name: Run tests
        run: docker-compose -f docker/docker-compose.yml run backend pytest
```

## Production Deployment

For production deployment:

1. **Update `.env` with secure values**
2. **Use a reverse proxy (nginx/Traefik)**
3. **Enable HTTPS**
4. **Set proper SECRET_KEY**
5. **Configure external database (RDS/CloudSQL)**
6. **Use Docker secrets for sensitive data**
7. **Enable monitoring (Prometheus/Grafana)**

Example with external database:
```yaml
services:
  backend:
    environment:
      DATABASE_URL: postgresql://user:pass@external-db:5432/finance_tracker
```

## Advanced Configuration

### Custom networks
```yaml
networks:
  frontend-network:
  backend-network:
```

### Resource limits
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

### Health checks
Already configured for `db` service. Add to other services:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```
