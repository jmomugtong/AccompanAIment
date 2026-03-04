# ===========================================================================
# AccompanAIment -- GPU-optimized multi-stage production Dockerfile
# ===========================================================================
# Builds both the backend (Python/FastAPI) and frontend (React/nginx).
# Supports optional NVIDIA GPU acceleration for CREPE melody extraction
# and Ollama LLM inference.
#
# Build variants:
#   Default (CPU):  docker build -t accompaniment .
#   GPU:            docker build --build-arg BASE_IMAGE=nvidia/cuda:12.2.0-runtime-ubuntu22.04 -t accompaniment:gpu .
# ===========================================================================

ARG BASE_IMAGE=python:3.11-slim

# ---------------------------------------------------------------------------
# Stage 1: Frontend build
# ---------------------------------------------------------------------------
FROM node:18-alpine AS frontend-build

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --no-audit --no-fund

COPY frontend/ ./
RUN npm run build

# ---------------------------------------------------------------------------
# Stage 2: Backend dependencies
# ---------------------------------------------------------------------------
FROM ${BASE_IMAGE} AS backend-deps

# Install system packages required by audio processing libraries.
# When using the nvidia/cuda base image, python3 must be installed manually.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    libsndfile1 \
    fluidsynth \
    libfluidsynth3 \
    lilypond \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a symlink so "python" and "pip" work regardless of base image.
RUN ln -sf /usr/bin/python3 /usr/bin/python || true \
    && ln -sf /usr/bin/pip3 /usr/bin/pip || true

WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 3: Production application
# ---------------------------------------------------------------------------
FROM backend-deps AS production

WORKDIR /app

# Copy backend source code
COPY backend/src ./src
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./
COPY backend/scripts ./scripts
COPY backend/datasets ./datasets
COPY backend/assets ./assets

# Copy built frontend into a static directory served by the backend or nginx
COPY --from=frontend-build /frontend/dist ./static

# Create required storage directories
RUN mkdir -p \
    /app/data/storage/uploads \
    /app/data/storage/melodies \
    /app/data/storage/generations \
    /app/data/storage/samples

# Non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default entrypoint: run the FastAPI application with uvicorn
CMD ["python", "-m", "uvicorn", "src.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--access-log"]
