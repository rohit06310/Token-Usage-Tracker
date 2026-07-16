# ==============================================================================
# Unified AI Usage Dashboard — Dockerfile
# ==============================================================================
# Multi-stage build: keeps the final image lean.
# Stage 1 (deps): install Python packages
# Stage 2 (app):  copy source + entrypoint
# ==============================================================================

# ---- Stage 1: dependency builder ----
FROM python:3.12-slim AS deps

WORKDIR /build

# Install system deps needed to compile psycopg2-binary & cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ---- Stage 2: runtime ----
FROM python:3.12-slim AS app

WORKDIR /app

# Runtime system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=deps /install /usr/local

# Copy application source
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./alembic.ini
COPY docker/entrypoint.sh ./entrypoint.sh

RUN chmod +x ./entrypoint.sh

# Non-root user for security
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
