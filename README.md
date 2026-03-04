# AccompanAIment

An AI-powered piano accompaniment generator for singer-songwriters. Extracts vocal melodies from uploaded songs via CREPE pitch tracking, accepts user-specified chord progressions, and generates piano accompaniments in multiple styles (jazz, soulful, RnB, pop, classical) using an LLM agent. Outputs MIDI, audio (WAV), and sheet music (PDF). 100% open-source, zero external API costs.

---

## Architecture

```
Frontend (React + TailwindCSS)
  [Upload] -> [Waveform] -> [Chord Input] -> [Style Select] -> [Progress] -> [Download]
       |                                                              |
       | REST + WebSocket (JWT auth)                                  |
       v                                                              v
API Layer (FastAPI)                                          WebSocket Progress
  POST /songs/upload          GET /songs/{id}/melody              Updates
  POST /songs/{id}/generate   GET /generations/{id}/download
       |
  Async Job Queue (Celery + Redis)
       |
  +---------+-----------+-----------+
  |         |           |           |
  Melody    Piano       Audio       Sheet
  Extractor Generator   Renderer    Generator
  (CREPE)   (LLM Agent) (FluidSynth)(Lilypond)
       |
  PostgreSQL + Redis + Filesystem Storage
```

### Pipeline Flow

Upload song -> Audio preprocessing (normalize, resample to 22.05kHz) -> CREPE melody extraction -> User inputs chords + style -> LLM agent generates music21 voicing code -> MIDI generation -> FluidSynth audio rendering + Lilypond sheet music -> Download

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.11+, FastAPI, Celery + Redis, SQLAlchemy 2.0 (async), PostgreSQL, Alembic |
| **Frontend** | React 18, TypeScript, TailwindCSS, Wavesurfer.js, Tone.js |
| **Audio/Music** | librosa, CREPE, music21, FluidSynth/pyfluidsynth, pydub, Lilypond |
| **ML/Agents** | Ollama (local LLM), Mistral/Llama2, LangChain |
| **Observability** | OpenTelemetry, Prometheus, Grafana |
| **Testing** | pytest, Vitest, k6 |
| **Infra** | Docker Compose, GitHub Actions CI/CD |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- 8GB RAM (GPU optional for faster CREPE inference)

### 1. Clone and configure

```bash
git clone https://github.com/jmomugtong/AccompanAIment.git
cd AccompanAIment
cp .env.example .env
cp frontend/.env.example frontend/.env
```

### 2. Start services

```bash
docker compose up -d
```

This starts PostgreSQL, Redis, Ollama, backend, frontend, and Prometheus.

### 3. Install dependencies (local development)

```bash
make install
```

### 4. Database setup

```bash
cd backend && alembic upgrade head
python scripts/seed_styles.py
python scripts/seed_chord_library.py
```

### 5. Pull LLM model (first time only)

```bash
docker exec accompaniment-ollama ollama pull mistral
```

### 6. Download piano soundfont (first time only)

```bash
mkdir -p backend/assets/soundfonts
# Download FluidR3_GM.sf2 and save as backend/assets/soundfonts/piano.sf2
```

### 7. Run

```bash
make dev
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Development Commands

```bash
# Testing
make test                 # Run all tests
make test-cov             # Tests with coverage
make test-integration     # Integration tests
make eval                 # Musician evaluation (50 accompaniments)
make load-test            # k6 load tests

# Code quality
make lint                 # Run all linters
make format               # Auto-format code

# Infrastructure
make docker-up            # Start all services
make docker-down          # Stop all services
make docker-build         # Build Docker images

# Database
make db-migrate           # Run Alembic migrations
make db-seed              # Seed styles and chord library
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/songs/upload` | Upload audio file (MP3/WAV/M4A/FLAC, max 100MB) |
| `GET` | `/songs/{id}/melody` | Get extracted melody data |
| `POST` | `/songs/{id}/generate-piano` | Trigger piano accompaniment generation |
| `WS` | `/songs/{id}/status` | Real-time progress updates |
| `GET` | `/songs/{id}/generations/{id}/download?format=midi\|audio\|sheet` | Download generated files |
| `POST` | `/generations/{id}/feedback` | Submit multi-dimensional rating |
| `GET` | `/generations` | User's generation history |
| `GET` | `/health` | Health check |
| `GET` | `/metrics` | Prometheus metrics |

---

## Testing

**806 backend tests** covering:
- Database models, CRUD, relationships, indexes, soft deletes
- Audio upload validation, preprocessing, storage
- CREPE melody extraction (mocked), pitch processing
- Chord validation and parsing (178 tests)
- LLM client, agent orchestration, sandboxed execution
- Voicing generation, MIDI generation
- Audio rendering, sheet music generation
- Celery task workers
- REST API endpoints, JWT auth, WebSocket
- Prometheus metrics, OpenTelemetry
- Evaluation framework (Kramer's alpha, rating stats)
- Full pipeline integration tests

---

## Quality Gates

| Metric | Target |
|--------|--------|
| Backend test coverage | >= 85% |
| Frontend test coverage | >= 70% |
| Musician evaluation avg rating | > 4.0/5 |
| Interrater agreement (Kramer's alpha) | > 0.85 |
| Load test p95 latency (uploads) | < 5s |
| Load test p95 latency (queries) | < 2s |
| Error rate | < 1% |

---

## Project Structure

```
AccompanAIment/
├── backend/
│   ├── src/
│   │   ├── api/          # FastAPI routes, JWT auth, WebSocket
│   │   ├── audio/        # Upload handling, CREPE, pitch processing, cache
│   │   ├── music/        # Chord validation, voicing, MIDI generation
│   │   ├── agents/       # LLM agent, style configs, prompts
│   │   ├── generation/   # Audio rendering, sheet music
│   │   ├── workers/      # Celery tasks
│   │   ├── db/           # SQLAlchemy models, PostgreSQL connection
│   │   ├── evals/        # Musician evaluation framework
│   │   ├── observability/ # Prometheus metrics, OpenTelemetry
│   │   └── storage/      # Filesystem storage abstraction
│   ├── tests/            # 806 tests
│   ├── scripts/          # Seed, health check, eval, benchmark scripts
│   ├── alembic/          # Database migrations
│   └── datasets/         # Evaluation dataset (50 accompaniments)
├── frontend/
│   └── src/
│       ├── components/   # 8 React components
│       ├── pages/        # Home, Generate, History, Feedback
│       ├── hooks/        # useGeneration, useAuth
│       └── services/     # API client, WebSocket client
├── k6/                   # Load test scenarios
├── docker-compose.yml
├── Makefile
└── .github/workflows/    # CI/CD pipeline
```

---

## License

MIT
