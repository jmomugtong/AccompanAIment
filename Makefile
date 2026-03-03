.PHONY: install dev test test-cov test-integration eval load-test lint format docker-up docker-down docker-build clean

# ── Installation ──────────────────────────────────────────────

install:
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install

# ── Development ───────────────────────────────────────────────

dev:
	@echo "Starting backend and frontend dev servers..."
	$(MAKE) dev-backend &
	$(MAKE) dev-frontend &
	wait

dev-backend:
	cd backend && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

# ── Testing ───────────────────────────────────────────────────

test:
	cd backend && pytest tests/ -v
	cd frontend && npm test

test-backend:
	cd backend && pytest tests/ -v

test-frontend:
	cd frontend && npm test

test-cov:
	cd backend && pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
	cd frontend && npm run test:coverage

test-integration:
	cd backend && pytest tests/integration/ -v

# ── Evaluation ────────────────────────────────────────────────

eval:
	cd backend && python scripts/run_musician_evals.py --eval-set=50

# ── Load Testing ──────────────────────────────────────────────

load-test:
	k6 run k6/load_test.js

# ── Code Quality ──────────────────────────────────────────────

lint:
	cd backend && black --check src/ tests/
	cd backend && isort --check-only src/ tests/
	cd backend && flake8 src/ tests/
	cd backend && mypy src/
	cd frontend && npm run lint
	cd frontend && npm run format:check

format:
	cd backend && black src/ tests/
	cd backend && isort src/ tests/
	cd frontend && npm run format

# ── Docker ────────────────────────────────────────────────────

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-build:
	docker compose build

# ── Database ──────────────────────────────────────────────────

db-migrate:
	cd backend && alembic upgrade head

db-seed:
	cd backend && python scripts/seed_styles.py
	cd backend && python scripts/seed_chord_library.py

# ── Cleanup ───────────────────────────────────────────────────

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf backend/dist backend/build backend/*.egg-info
