# --- Stage 1: Builder (Install dependencies) ---
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies (needed for compiling C extensions like psycopg2)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY src_api/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Stage 2: Runtime (Lean production image) ---
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only (no gcc needed here)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY src_api/ .

# Create startup script with DB wait logic
RUN printf '%s\n' \
  '#!/bin/bash' \
  'set -e' \
  'export PGPASSWORD="${DB_PASSWORD:-securepassword}"' \
  '' \
  'until pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${DB_USER:-admin}" -d "${DB_NAME:-federalism_db}" >/dev/null 2>&1; do' \
  '  echo "Waiting for PostgreSQL at ${DB_HOST:-db}:${DB_PORT:-5432}..."' \
  '  sleep 1' \
  'done' \
  '' \
  'echo "Running migrations..."' \
  'python manage.py migrate --noinput' \
  '' \
  'echo "Starting Gunicorn..."' \
  'exec gunicorn --config gunicorn.conf.py fed_api.wsgi:application' \
  > /start.sh && chmod +x /start.sh

EXPOSE 8000

CMD ["/start.sh"]