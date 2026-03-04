# Deployment Guide

This document covers deploying AccompanAIment using Docker Compose,
configuring environment variables, running database migrations, and
scaling the application for production workloads.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Docker Compose Setup](#docker-compose-setup)
- [Environment Variables](#environment-variables)
- [Database Migrations](#database-migrations)
- [Seeding Reference Data](#seeding-reference-data)
- [GPU Support](#gpu-support)
- [Production Hardening](#production-hardening)
- [Scaling Strategies](#scaling-strategies)
- [Monitoring](#monitoring)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker Engine 24.0 or later
- Docker Compose v2.20 or later
- At least 8 GB RAM (16 GB recommended for GPU workloads)
- At least 20 GB free disk space (more if storing audio files locally)
- NVIDIA GPU with CUDA 12.x drivers (optional, for GPU acceleration)
- NVIDIA Container Toolkit (optional, for GPU support in Docker)

## Docker Compose Setup

### Quick Start

1. Clone the repository and navigate to the project root:

   ```bash
   git clone <repository-url>
   cd AccompanAIment
   ```

2. Create the environment file from the template:

   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and set production values (see Environment Variables below).

4. Build and start all services:

   ```bash
   docker compose up -d --build
   ```

5. Run database migrations:

   ```bash
   docker compose exec backend alembic upgrade head
   ```

6. Seed reference data:

   ```bash
   docker compose exec backend python scripts/seed_styles.py
   docker compose exec backend python scripts/seed_chord_library.py
   ```

7. Verify all services are running:

   ```bash
   docker compose ps
   ```

### Services Overview

| Service        | Image/Build       | Port  | Description                    |
|----------------|-------------------|-------|--------------------------------|
| postgres       | postgres:15-alpine | 5432 | PostgreSQL database            |
| redis          | redis:7-alpine     | 6379 | Message broker and cache       |
| ollama         | ollama/ollama      | 11434| Local LLM inference server     |
| backend        | ./backend          | 8000 | FastAPI application            |
| celery-worker  | ./backend          | --   | Async task workers             |
| frontend       | ./frontend         | 3000 | React development server       |
| prometheus     | prom/prometheus     | 9090 | Metrics collection             |
| grafana        | grafana/grafana    | 3001 | Dashboards (optional profile)  |

### Stopping Services

```bash
docker compose down
```

To also remove persistent volumes (WARNING: deletes all data):

```bash
docker compose down -v
```

## Environment Variables

All configuration is managed through environment variables. Copy
`.env.example` to `.env` and set values appropriate for your environment.

### Database

| Variable         | Default                                                             | Description                 |
|------------------|---------------------------------------------------------------------|-----------------------------|
| DATABASE_URL     | postgresql+asyncpg://accompaniment:accompaniment@localhost:5432/accompaniment | Async database URL (asyncpg driver) |
| DATABASE_URL_SYNC| postgresql://accompaniment:accompaniment@localhost:5432/accompaniment | Sync database URL (psycopg2 driver) |

### Redis

| Variable  | Default                  | Description              |
|-----------|--------------------------|--------------------------|
| REDIS_URL | redis://localhost:6379/0 | Redis connection URL     |

### Ollama (LLM)

| Variable             | Default                  | Description                     |
|----------------------|--------------------------|---------------------------------|
| OLLAMA_BASE_URL      | http://localhost:11434   | Ollama server URL               |
| OLLAMA_MODEL         | mistral                  | Primary LLM model (7B)         |
| OLLAMA_FALLBACK_MODEL| neural-chat              | Fallback model (smaller)        |

### Storage

| Variable        | Default            | Description                              |
|-----------------|--------------------|------------------------------------------|
| STORAGE_PATH    | ./data/storage     | Local file storage path                  |
| STORAGE_BACKEND | filesystem         | Storage backend: filesystem or minio     |

### Audio

| Variable                    | Default                              | Description                     |
|-----------------------------|--------------------------------------|---------------------------------|
| SOUNDFONT_PATH              | ./backend/assets/soundfonts/piano.sf2| Path to FluidR3_GM soundfont    |
| CREPE_MODEL_CAPACITY        | full                                 | CREPE model size (tiny/small/medium/large/full) |
| MAX_UPLOAD_SIZE_MB           | 100                                  | Maximum upload file size in MB  |
| MAX_AUDIO_DURATION_SECONDS   | 600                                  | Maximum audio duration (10 min) |

### Authentication

| Variable              | Default  | Description                              |
|-----------------------|----------|------------------------------------------|
| JWT_SECRET            | (none)   | Secret key for signing JWTs (MUST change)|
| JWT_ALGORITHM         | HS256    | JWT signing algorithm                    |
| JWT_EXPIRATION_MINUTES| 1440     | Token lifetime in minutes (24 hours)     |

### CORS

| Variable     | Default                                    | Description              |
|--------------|--------------------------------------------|--------------------------|
| CORS_ORIGINS | http://localhost:3000,http://localhost:5173 | Allowed CORS origins     |

### Celery

| Variable              | Default                  | Description              |
|-----------------------|--------------------------|--------------------------|
| CELERY_BROKER_URL     | redis://localhost:6379/0 | Celery message broker    |
| CELERY_RESULT_BACKEND | redis://localhost:6379/1 | Celery result storage    |

### Melody Cache

| Variable         | Default | Description                              |
|------------------|---------|------------------------------------------|
| MELODY_CACHE_TTL | 604800  | Melody cache lifetime in seconds (7 days)|

### Application

| Variable           | Default   | Description                     |
|--------------------|-----------|---------------------------------|
| API_HOST           | 0.0.0.0   | Bind address for the API server |
| API_PORT           | 8000      | API server port                 |
| DEBUG              | true      | Debug mode (set false in prod)  |
| PROMETHEUS_ENABLED | true      | Enable Prometheus metrics        |

## Database Migrations

AccompanAIment uses Alembic for database schema management.

### Running Migrations

Apply all pending migrations:

```bash
# Via Docker Compose
docker compose exec backend alembic upgrade head

# Local development
cd backend && alembic upgrade head
```

### Checking Migration Status

```bash
docker compose exec backend alembic current
```

### Viewing Migration History

```bash
docker compose exec backend alembic history --verbose
```

### Creating a New Migration

After modifying SQLAlchemy models:

```bash
cd backend
alembic revision --autogenerate -m "Description of the change"
```

Review the generated migration file in `backend/alembic/versions/`
before applying it.

### Rolling Back

Roll back the most recent migration:

```bash
docker compose exec backend alembic downgrade -1
```

Roll back to a specific revision:

```bash
docker compose exec backend alembic downgrade <revision_id>
```

## Seeding Reference Data

After running migrations, seed the database with reference data:

```bash
# Seed accompaniment style templates
docker compose exec backend python scripts/seed_styles.py

# Seed chord progression library
docker compose exec backend python scripts/seed_chord_library.py
```

Both scripts are idempotent and safe to run multiple times. Use `--dry-run`
to preview what would be inserted:

```bash
docker compose exec backend python scripts/seed_styles.py --dry-run
```

## GPU Support

### Ollama GPU Acceleration

The `docker-compose.yml` includes GPU resource reservations for the
Ollama service. This requires:

1. NVIDIA GPU with CUDA 12.x compatible drivers.
2. NVIDIA Container Toolkit installed on the host.

If no GPU is available, remove the `deploy.resources` block from the
`ollama` service in `docker-compose.yml`.

### Root Dockerfile GPU Build

The root `Dockerfile` supports an optional GPU base image:

```bash
# CPU-only build (default)
docker build -t accompaniment .

# GPU build with CUDA support
docker build \
  --build-arg BASE_IMAGE=nvidia/cuda:12.2.0-runtime-ubuntu22.04 \
  -t accompaniment:gpu .
```

## Production Hardening

### Security Checklist

- Set a strong, random `JWT_SECRET` (at least 32 characters).
- Set `DEBUG=false`.
- Restrict `CORS_ORIGINS` to your frontend domain only.
- Use TLS/HTTPS via a reverse proxy (nginx, Traefik, or cloud load balancer).
- Do not expose PostgreSQL (5432) or Redis (6379) ports publicly.
- Run containers as non-root users (the root Dockerfile creates an `appuser`).
- Rotate the JWT secret periodically.

### Reverse Proxy

Place nginx or Traefik in front of the FastAPI backend to handle:

- TLS termination
- Rate limiting
- Request buffering for large uploads
- Static file serving for the React frontend

### Log Aggregation

Configure Docker logging drivers to forward logs to a centralized
system (e.g., ELK stack, Loki, or a cloud logging service).

## Scaling Strategies

### Horizontal Scaling: Celery Workers

The most effective way to increase throughput is adding more Celery
workers. Each worker handles one pipeline task at a time.

Scale workers via Docker Compose:

```bash
docker compose up -d --scale celery-worker=4
```

Or adjust the concurrency per worker:

```yaml
command: celery -A src.celery_app worker --loglevel=info --concurrency=4
```

### Horizontal Scaling: API Servers

Run multiple backend instances behind a load balancer:

```bash
docker compose up -d --scale backend=3
```

Ensure session affinity is not required (the API is stateless with JWT
authentication). WebSocket connections require sticky sessions if
scaling the backend horizontally.

### Vertical Scaling: GPU Workers

For CREPE melody extraction, GPU acceleration significantly reduces
processing time. Dedicate GPU-equipped machines to Celery workers
running melody extraction tasks.

### Database Scaling

- Enable PostgreSQL connection pooling with PgBouncer.
- Use read replicas for query-heavy endpoints (generation history, feedback).
- Partition the `melodies` table by `created_at` if it grows very large.

### Redis Scaling

- Use Redis Sentinel or Redis Cluster for high availability.
- Separate the Celery broker and result backend onto different Redis instances
  under heavy load.

### Storage Scaling

- Switch from `filesystem` to `minio` (S3-compatible) for production.
- Use a CDN for serving generated audio and sheet music downloads.

## Monitoring

### Prometheus Metrics

The backend exposes metrics at `GET /metrics`. The included
`prometheus.yml` is pre-configured to scrape this endpoint.

Access Prometheus at `http://localhost:9090`.

### Grafana Dashboards

Enable the Grafana service:

```bash
docker compose --profile monitoring up -d
```

Access Grafana at `http://localhost:3001` (default password: `admin`).

### Key Metrics to Monitor

- `accompaniment_uploads_total` -- upload volume
- `accompaniment_generations_total` -- generation throughput
- `accompaniment_generation_duration_seconds` -- processing time histogram
- `celery_worker_tasks_active` -- active worker tasks
- Redis memory usage and connection count
- PostgreSQL connection pool utilization

## Backup and Recovery

### Database Backup

```bash
# Create a backup
docker compose exec postgres pg_dump -U accompaniment accompaniment > backup.sql

# Restore from backup
docker compose exec -i postgres psql -U accompaniment accompaniment < backup.sql
```

### Volume Backup

Back up Docker volumes for persistent data:

```bash
docker run --rm -v accompaniment_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres_data.tar.gz /data
```

## Troubleshooting

### Ollama Model Not Found

If Ollama reports a missing model, pull it manually:

```bash
docker compose exec ollama ollama pull mistral
```

### Database Connection Refused

Verify PostgreSQL is healthy:

```bash
docker compose ps postgres
docker compose logs postgres
```

Ensure the `DATABASE_URL` matches the PostgreSQL credentials in
`docker-compose.yml`.

### Celery Workers Not Processing Tasks

Check worker logs:

```bash
docker compose logs celery-worker
```

Verify Redis is reachable:

```bash
docker compose exec redis redis-cli ping
```

### CREPE Out of Memory

CREPE (via TensorFlow) may exhaust GPU or system memory on long audio
files. Reduce `CREPE_MODEL_CAPACITY` from `full` to `medium` or `small`,
or increase available memory.

### FluidSynth Soundfont Missing

Ensure the FluidR3_GM soundfont is present at the configured
`SOUNDFONT_PATH`. Download it once and place it in
`backend/assets/soundfonts/piano.sf2`.
