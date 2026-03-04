# Contributing to AccompanAIment

Thank you for your interest in contributing to AccompanAIment. This document
describes the development environment setup, code style requirements, testing
expectations, and the process for submitting changes.

## Table of Contents

- [Development Environment Setup](#development-environment-setup)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Commit Message Format](#commit-message-format)
- [Issue Reporting](#issue-reporting)

## Development Environment Setup

### Prerequisites

- Python 3.11 or later
- Node.js 18 or later (with npm)
- Docker and Docker Compose
- PostgreSQL 15 (via Docker or local installation)
- Redis 7 (via Docker or local installation)
- Ollama (for local LLM inference)

### Getting Started

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd AccompanAIment
   ```

2. Copy the environment template and adjust values as needed:

   ```bash
   cp .env.example .env
   ```

3. Start infrastructure services:

   ```bash
   make docker-up
   ```

   This starts PostgreSQL, Redis, Ollama, the backend, the frontend dev
   server, and Prometheus.

4. Run database migrations:

   ```bash
   cd backend && alembic upgrade head
   ```

5. Seed reference data:

   ```bash
   python scripts/seed_styles.py
   python scripts/seed_chord_library.py
   ```

6. For local development without Docker, install dependencies directly:

   ```bash
   make install
   make dev
   ```

### Directory Structure

- `backend/` -- Python FastAPI application, Celery workers, and supporting modules
- `frontend/` -- React 18 TypeScript application
- `k6/` -- Load testing scripts
- `docs/` -- Project documentation and prompt references
- `models/` -- Model configuration files

## Code Style

### Python (Backend)

- Follow PEP 8 conventions.
- Use type hints on all function signatures and return types.
- Write docstrings in Google format for all public functions, classes, and modules.
- Maximum line length: 99 characters (configured in black).
- Use `black` for formatting, `isort` for import sorting.
- `flake8` for linting, `mypy` for static type checking.

Run all Python linting and formatting:

```bash
cd backend
black src/ tests/
isort src/ tests/
flake8 src/ tests/
mypy src/
```

### TypeScript (Frontend)

- Use TypeScript strict mode.
- Follow ESLint and Prettier configurations defined in the project.
- Prefer functional components and hooks in React code.
- Use named exports over default exports.

Run frontend linting and formatting:

```bash
cd frontend
npm run lint
npm run format
```

### All Files

- No trailing whitespace.
- Files must end with a single newline.
- Use UTF-8 encoding.

## Testing

### Running Tests

```bash
# All tests (backend + frontend)
make test

# Backend only
make test-backend

# Frontend only
make test-frontend

# With coverage report
make test-cov

# Integration tests
make test-integration

# A single backend test file
pytest backend/tests/test_<module>.py -v
```

### Coverage Targets

- Backend: 85% or higher
- Frontend: 70% or higher

### Test-Driven Development

This project follows TDD. When adding a new feature or fixing a bug:

1. Write a failing test in `backend/tests/test_<module>.py` (or the
   corresponding frontend test file).
2. Implement the minimum code to make the test pass.
3. Refactor as needed while keeping tests green.

### Evaluation

The musician evaluation framework validates output quality:

```bash
make eval
```

Quality gates:
- Average rating must exceed 4.0/5 on a 50-accompaniment evaluation set.
- Interrater agreement (Kramer's alpha) must exceed 0.85.

## Pull Request Process

1. Create a feature branch from `main`:

   ```bash
   git checkout -b feature/short-description
   ```

2. Make your changes, following code style and testing requirements.

3. Run the full test suite and linting before pushing:

   ```bash
   make lint
   make test
   ```

4. Push your branch and open a pull request against `main`.

5. In the PR description, include:
   - A summary of what the change does and why.
   - Any relevant context or design decisions.
   - How you tested the change (manual testing, new tests, etc.).

6. Address all review feedback. The PR must pass CI checks (linting,
   tests, coverage thresholds, and evaluations) before merging.

7. PRs are merged via squash-and-merge to keep a clean history on `main`.

## Commit Message Format

- Use the imperative mood in the subject line (e.g., "Add melody caching"
  not "Added melody caching").
- Keep the subject line under 72 characters.
- Do NOT prefix commit messages with "Phase #" or similar numbering.
- Separate the subject from the body with a blank line.
- Use the body to explain what changed and why, not how.

Examples of good commit messages:

```
Add Redis caching for extracted melodies

Extracted melodies are now cached in Redis with a 7-day TTL.
Subsequent requests for the same song return the cached result,
avoiding redundant CREPE processing.
```

```
Fix voice leading violation in classical style voicing

The classical voicing template allowed parallel fifths between
soprano and bass voices. Added interval checking to enforce
proper contrary motion.
```

## Issue Reporting

When reporting a bug or requesting a feature:

- Search existing issues first to avoid duplicates.
- For bugs, include: steps to reproduce, expected behavior, actual behavior,
  and your environment (OS, Python version, Node version, Docker version).
- For feature requests, describe the use case and expected outcome.

## Questions

If you have questions about contributing, open a discussion or reach out
to the maintainers.
