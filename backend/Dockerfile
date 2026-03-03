# ── Stage 1: Dependencies ─────────────────────────────────────
FROM python:3.11-slim AS dependencies

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsndfile1 \
    fluidsynth \
    libfluidsynth3 \
    lilypond \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Application ─────────────────────────────────────
FROM dependencies AS app

WORKDIR /app

COPY . .

# Create storage directories
RUN mkdir -p /app/data/storage/uploads \
    /app/data/storage/melodies \
    /app/data/storage/generations

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ── Stage 3: Test runner ─────────────────────────────────────
FROM app AS test

RUN pip install --no-cache-dir pytest pytest-asyncio pytest-cov pytest-mock

CMD ["pytest", "tests/", "-v", "--cov=src", "--cov-report=term-missing"]
