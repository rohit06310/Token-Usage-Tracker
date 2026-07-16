# Unified AI Usage Dashboard

> **Phase 1 — Foundations & Architecture** ✅

A production-grade unified dashboard for tracking LLM token usage and costs across **OpenAI, Anthropic, Groq, and Gemini** in a single place.

**Stack:** Python 3.12 · FastAPI · SQLAlchemy 2.x · Alembic · PostgreSQL (Supabase) · Docker · pytest · GitHub Actions

---

## Quick Start

### 1. Generate secrets

```bash
python scripts/generate_keys.py
```

Copy the output into your `.env` file.

### 2. Configure environment

```bash
cp .env.example .env
# Fill in:
#   DATABASE_URL  — Supabase direct connection string (port 5432)
#   FERNET_KEY    — output from generate_keys.py
#   DASHBOARD_API_KEY — output from generate_keys.py
```

### 3. Start with Docker

```bash
docker compose up --build
```

The container will:
1. Wait for database connectivity
2. Run `alembic upgrade head` (creates all tables)
3. Start Uvicorn with hot-reload (development mode)

### 4. Verify

```bash
# Health check
curl http://localhost:8000/health

# Smoke test (requires running app)
DASHBOARD_API_KEY=your-key python scripts/smoke_test.py

# Interactive API docs
open http://localhost:8000/docs
```

---

## Local Development (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set env vars (or use .env file)
export DATABASE_URL="postgresql://..."
export FERNET_KEY="..."
export DASHBOARD_API_KEY="..."

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

---

## Running Tests

```bash
# No database needed — tests use SQLite in-memory
pytest tests/ -v
```

Tests inject a fresh Fernet key and test database at runtime. No `.env` required.

---

## Project Structure

```
AIusageDashboard/
├── app/
│   ├── main.py                  # FastAPI app factory
│   ├── api/v1/
│   │   ├── health.py            # GET /health (public)
│   │   ├── providers.py         # CRUD /api/v1/providers/
│   │   ├── api_keys.py          # CRUD /api/v1/api-keys/
│   │   └── usage.py             # GET /api/v1/usage/
│   ├── core/
│   │   ├── config.py            # Pydantic Settings (all env vars)
│   │   ├── security.py          # FernetEncryption + HMAC key hashing
│   │   └── deps.py              # get_current_user FastAPI dependency
│   ├── adapters/
│   │   ├── base.py              # BaseProviderAdapter (abstract)
│   │   ├── openai_adapter.py    # Phase 1 stub
│   │   ├── anthropic_adapter.py # Phase 1 stub
│   │   ├── groq_adapter.py      # Phase 1 stub
│   │   └── gemini_adapter.py    # Phase 1 stub
│   ├── models/
│   │   ├── provider.py          # Provider ORM model
│   │   ├── api_key.py           # ApiKey ORM model
│   │   ├── usage_log.py         # UsageLog ORM model (JSONB)
│   │   └── rate_limit.py        # RateLimit ORM model
│   ├── schemas/                 # Pydantic v2 request/response schemas
│   └── services/db.py           # SQLAlchemy engine + get_db dependency
├── alembic/
│   ├── env.py                   # Loads DATABASE_URL from env
│   └── versions/
│       └── 0001_initial_schema.py
├── docker/
│   ├── Dockerfile               # Multi-stage build
│   └── entrypoint.sh            # DB wait + migrate + uvicorn
├── tests/
│   ├── conftest.py              # SQLite fixtures, TestClient
│   ├── test_health.py
│   ├── test_encryption.py
│   └── test_usage_log.py
├── scripts/
│   ├── generate_keys.py         # Generate FERNET_KEY + DASHBOARD_API_KEY
│   └── smoke_test.py            # Live API smoke test
├── .github/workflows/ci.yml     # GitHub Actions CI
├── docker-compose.yml
├── requirements.txt
├── alembic.ini
├── pytest.ini
└── Makefile
```

---

## Authentication

The API uses **JWT-based OAuth2** authentication.

1. **Sign up**: `POST /api/v1/auth/signup`
2. **Log in**: `POST /api/v1/auth/login` (receives `access_token`)
3. **Authenticate**: Include `Authorization: Bearer <access_token>` in API requests.

The frontend stores the JWT in an `httpOnly` cookie for security.

---

## Phase Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| **1 — Foundations** | ✅ Done | Project structure, DB schema, encryption, auth, Docker |
| **2 — Provider Adapters** | ✅ Done | Real SDK calls for OpenAI, Anthropic, Groq, Gemini |
| **3 — Analytics** | ✅ Done | Cost aggregation, per-model breakdown, trends |
| **4 — Dashboard UI** | ✅ Done | React frontend with charts |
| **5 — Prod & Deploy** | ✅ Done | Multi-user Auth, CI/CD, Load Testing, Deployment |

---

## Local Development (without Docker)

```bash
# Backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

---

## Load Testing

The system includes a k6 load test script to verify performance SLAs (e.g. 95th percentile < 500ms).

```bash
# Install k6
brew install k6
# Run test
k6 run -e BASE_URL=http://localhost:8000 -e EMAIL=admin@example.com -e PASSWORD=admin123 tests/load/k6_test.js
```

---

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment.
- **Tests**: Runs `pytest` and `ruff` on every PR/push to `main` and `develop`.
- **CD**: Automatically builds and pushes a Docker image to GitHub Container Registry (`ghcr.io`) upon merging to `main`.

---

## Deployment Guide (Railway / Render)

1. Provision a **PostgreSQL** database on Supabase.
2. In Supabase, configure **Database Backups** (PITR or daily logical backups).
3. Connect your GitHub repository to Railway or Render.
4. Set environment variables using the provided `.env.production` template. Be sure to inject secrets via Doppler or the platform's secret manager.
5. Disable `DEBUG` mode.
6. Use the connection pooled Supabase URL (port `6543`) for `DATABASE_URL`.
7. Railway/Render will automatically build the `Dockerfile` and start the Uvicorn server.

---

## Backup & Disaster Recovery

- **Supabase Backups**: Enable Daily Backups in your Supabase project settings. For mission-critical dashboards, enable Point-in-Time Recovery (PITR).
- **Manual Export**: To manually backup `usage_logs` and encrypted `api_keys`:
  ```bash
  pg_dump --clean $DATABASE_URL > backup.sql
  ```
