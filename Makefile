# ==============================================================================
# Unified AI Usage Dashboard — Makefile (Local Native)
# ==============================================================================

.PHONY: help install start-backend start-frontend migrate migrate-create test lint format clean keys

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install Python and Node dependencies
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	cd frontend && npm install

start-backend:  ## Start FastAPI backend locally
	.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

start-frontend:  ## Start Next.js frontend locally
	cd frontend && npm run dev

migrate:  ## Run Alembic migrations locally
	.venv/bin/alembic upgrade head

migrate-create:  ## Create a new migration (usage: make migrate-create msg="add table")
	.venv/bin/alembic revision --autogenerate -m "$(msg)"

test:  ## Run tests
	.venv/bin/pytest tests/ -v --tb=short

lint:  ## Lint code
	.venv/bin/ruff check app/ tests/

format:  ## Format code
	.venv/bin/ruff format app/ tests/

clean:  ## Remove __pycache__ and .pyc files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type f -name "*.pyc" -delete

keys:  ## Generate new FERNET_KEY and DASHBOARD_API_KEY
	.venv/bin/python scripts/generate_keys.py
