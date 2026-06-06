#!/bin/bash
set -e

echo "=== Starting Container ==="

# Wait for DB
export PGPASSWORD="${DB_PASSWORD:-securepassword}"
echo "Waiting for PostgreSQL at ${DB_HOST:-db}..."
until pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${DB_USER:-admin}" -d "${DB_NAME:-federalism_db}" >/dev/null 2>&1; do
  sleep 1
done
echo "PostgreSQL is ready."

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
# This is CRITICAL. It moves frontend_dist -> staticfiles
python manage.py collectstatic --noinput

# Verify index.html exists
if [ -f "/app/staticfiles/index.html" ]; then
    echo "✅ index.html found in staticfiles."
else
    echo "❌ ERROR: index.html NOT found in staticfiles!"
    echo "Contents of staticfiles:"
    ls -la /app/staticfiles/
    exit 1
fi

echo "Starting Gunicorn..."
exec gunicorn --config gunicorn.conf.py fed_api.wsgi:application