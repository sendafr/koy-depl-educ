#!/bin/bash
set -e

export PGPASSWORD="${DB_PASSWORD:-securepassword}"

if [[ "${DATABASE_URL:-}" =~ ^postgres(ql)?:// ]] || [[ "${DB_HOST:-}" =~ ^postgres(ql)?:// ]]; then
  if [[ -n "${DATABASE_URL:-}" && "${DATABASE_URL:-}" =~ ^postgres(ql)?:// ]]; then
    DB_URL="${DATABASE_URL}"
  else
    DB_URL="${DB_HOST}"
  fi
  export DB_URL

  eval "$(python - <<'PY'
import os, urllib.parse, shlex
u = urllib.parse.urlparse(os.environ['DB_URL'])
print(f"DB_HOST={shlex.quote(u.hostname or 'db')}")
print(f"DB_PORT={shlex.quote(str(u.port or 5432))}")
print(f"DB_USER={shlex.quote(u.username or os.environ.get('DB_USER', 'admin'))}")
print(f"DB_PASSWORD={shlex.quote(u.password or os.environ.get('DB_PASSWORD', 'securepassword'))}")
print(f"DB_NAME={shlex.quote(u.path.lstrip('/') or os.environ.get('DB_NAME', 'federalism_db'))}")
PY
)"
  export DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME
fi

until pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${DB_USER:-admin}" -d "${DB_NAME:-federalism_db}" >/dev/null 2>&1; do
  echo "Waiting for PostgreSQL at ${DB_HOST:-db}:${DB_PORT:-5432}..."
  sleep 1
done

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

echo "Running migrations..."
python manage.py migrate --noinput

echo "Starting Gunicorn..."
exec gunicorn --config gunicorn.conf.py fed_api.wsgi:application
