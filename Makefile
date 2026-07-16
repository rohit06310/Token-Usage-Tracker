# ==============================================================================
# Unified AI Usage Dashboard — Makefile
# ==============================================================================

.PHONY: help up down build logs shell migrate test lint format clean keys

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up:  ## Start all services (detached)
	docker compose up -d --build

down:  ## Stop all services
	docker compose down

build:  ## Build Docker images
	docker compose build

logs:  ## Follow service logs
	docker compose logs -f api

shell:  ## Open a shell in the api container
	docker compose exec api bash

migrate:  ## Run Alembic migrations (inside container)
	docker compose exec api alembic upgrade head

migrate-local:  ## Run Alembic migrations locally
	alembic upgrade head

migrate-create:  ## Create a new migration (usage: make migrate-create msg="add table")
	alembic revision --autogenerate -m "$(msg)"

test:  ## Run tests
	pytest tests/ -v --tb=short

test-ci:  ## Run tests with coverage (for CI)
	pytest tests/ -v --tb=short --cov=app --cov-report=xml --cov-report=term

lint:  ## Lint code
	ruff check app/ tests/

format:  ## Format code
	ruff format app/ tests/

clean:  ## Remove __pycache__ and .pyc files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type f -name "*.pyc" -delete

keys:  ## Generate new FERNET_KEY and DASHBOARD_API_KEY
	python scripts/generate_keys.py
