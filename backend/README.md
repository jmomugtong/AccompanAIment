# AccompanAIment Backend

AI-powered piano accompaniment generator backend.

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- 8GB RAM minimum

### 1. Start services

```bash
# From project root
docker compose up -d postgres redis ollama
```

### 2. Install dependencies

```bash
cd backend
pip install -e ".[dev]"
```

### 3. Set up environment

```bash
cp ../.env.example ../.env
# Edit .env if needed (defaults work for local dev)
```

### 4. Run database migrations

```bash
alembic upgrade head
python scripts/seed_styles.py
python scripts/seed_chord_library.py
```

### 5. Pull LLM model (first time only)

```bash
docker exec accompaniment-ollama ollama pull mistral
```

### 6. Download piano soundfont (first time only)

```bash
mkdir -p assets/soundfonts
# Download FluidR3_GM.sf2 (~150MB) and save as assets/soundfonts/piano.sf2
```

### 7. Start the server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 8. Run tests

```bash
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
```

## API Documentation

Once running, visit http://localhost:8000/docs for interactive API docs.
