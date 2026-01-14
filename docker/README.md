# Docker Configuration

This directory contains all Docker-related configuration files for the Personal Finance Tracker application.

## Files

- **docker-compose.yml** - Production configuration
- **docker-compose.dev.yml** - Development configuration with hot-reload
- **.env.example** - Environment variables template

## Quick Start

### Development Mode (Recommended for local development)
```bash
# From project root
docker-compose -f docker/docker-compose.dev.yml up -d --build
```

### Production Mode
```bash
# From project root
docker-compose -f docker/docker-compose.yml up -d --build
```

## Documentation

See [docs/README-DOCKER.md](../docs/README-DOCKER.md) for complete documentation.

## Setup

1. Copy environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your configuration (optional - defaults work for development)

3. Start services:
   ```bash
   docker-compose -f docker/docker-compose.dev.yml up -d --build
   ```

## Services

- **db**: PostgreSQL 15 database on port 5432
- **backend**: FastAPI application on port 8000
- **frontend**: Next.js web app on port 3000

## Data Persistence

Database data is stored in a Docker volume and persists across container restarts.
