#!/bin/bash
# ==============================================================================
# Docker entrypoint — runs on container startup
# 1. Waits for the database to be reachable
# 2. Runs Alembic migrations
# 3. Starts Uvicorn
# ==============================================================================

set -e

echo "============================================="
echo "  Unified AI Usage Dashboard — Starting up"
echo "============================================="

# ---------------------------------------------------------------------------
# 1. Wait for database connectivity (simple TCP probe via Python)
# ---------------------------------------------------------------------------
echo "[entrypoint] Waiting for database..."

python - <<EOF
import os, sys, time, urllib.parse

db_url = os.environ.get("DATABASE_URL", "")
if not db_url:
    print("ERROR: DATABASE_URL is not set.", file=sys.stderr)
    sys.exit(1)

parsed = urllib.parse.urlparse(db_url)
host = parsed.hostname
port = parsed.port or 5432

import socket
max_retries = 30
for attempt in range(max_retries):
    try:
        sock = socket.create_connection((host, port), timeout=2)
        sock.close()
        print(f"[entrypoint] Database is reachable at {host}:{port}")
        sys.exit(0)
    except (socket.error, OSError):
        print(f"[entrypoint] Attempt {attempt + 1}/{max_retries} — waiting...")
        time.sleep(2)

print("ERROR: Database not reachable after retries.", file=sys.stderr)
sys.exit(1)
EOF

# ---------------------------------------------------------------------------
# 2. Run Alembic migrations
# ---------------------------------------------------------------------------
echo "[entrypoint] Running database migrations..."
alembic upgrade head
echo "[entrypoint] Migrations complete."

# ---------------------------------------------------------------------------
# 3. Start the application
# ---------------------------------------------------------------------------
APP_ENV="${APP_ENV:-production}"

if [ "$APP_ENV" = "development" ]; then
    echo "[entrypoint] Starting in DEVELOPMENT mode (hot-reload enabled)"
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        --log-level debug
else
    echo "[entrypoint] Starting in PRODUCTION mode"
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 2 \
        --log-level info
fi
