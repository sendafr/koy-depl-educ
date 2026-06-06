#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/run-containers.sh [--build]
# Detects docker or podman, creates a network, starts Postgres, then starts the app.

RUNTIME=""
if command -v docker >/dev/null 2>&1; then
  RUNTIME=docker
elif command -v podman >/dev/null 2>&1; then
  RUNTIME=podman
else
  echo "Error: neither docker nor podman found in PATH." >&2
  exit 1
fi

NET=fedox-net
DB_NAME=db
APP_NAME=fedox-app
DB_USER=admin
DB_PASS=securepassword
DB_DB=federalism_db
ENV_SRC=src_api/.env
ENV_TMP="/tmp/fedox_env.$RANDOM"
IMAGE_TAG=fedox-app:local

# optional build
if [ "${1:-}" = "--build" ]; then
  echo "Building app image ($IMAGE_TAG) with $RUNTIME..."
  $RUNTIME build -f src_api/Dockerfile -t $IMAGE_TAG .
fi

# prepare cleaned env file (remove comments, empty lines, leading spaces)
if [ -f "$ENV_SRC" ]; then
  awk 'BEGIN{FS=OFS=""} /^[[:space:]]*#/ {next} /^[[:space:]]*$/ {next} {sub(/^[[:space:]]+/,""); print}' "$ENV_SRC" > "$ENV_TMP"
else
  cat > "$ENV_TMP" <<EOF
DATABASE_URL=postgresql://$DB_USER:$DB_PASS@${DB_NAME}:5432/${DB_DB}
EOF
fi

# Ensure DATABASE_URL exists in the temporary env file (useful when src_api/.env has separate DB_* vars)
if ! grep -q '^DATABASE_URL=' "$ENV_TMP"; then
  echo "DATABASE_URL=postgresql://$DB_USER:$DB_PASS@${DB_NAME}:5432/${DB_DB}" >> "$ENV_TMP"
fi

trap 'rm -f "$ENV_TMP"' EXIT

# stop any existing containers with the same names
EXISTING_DB=$($RUNTIME ps -q --filter "name=^/${DB_NAME}$") || true
if [ -n "$EXISTING_DB" ]; then
  echo "Stopping existing $DB_NAME..."
  $RUNTIME rm -f $EXISTING_DB || true
fi
EXISTING_APP=$($RUNTIME ps -q --filter "name=^/${APP_NAME}$") || true
if [ -n "$EXISTING_APP" ]; then
  echo "Stopping existing $APP_NAME..."
  $RUNTIME rm -f $EXISTING_APP || true
fi

# create network if missing
if ! $RUNTIME network ls --format '{{.Name}}' 2>/dev/null | grep -qw "$NET"; then
  echo "Creating network $NET"
  $RUNTIME network create "$NET" || true
fi

# start postgres
echo "Starting Postgres ($DB_NAME) on network $NET..."
$RUNTIME run -d --name $DB_NAME --network $NET \
  -e POSTGRES_USER=$DB_USER -e POSTGRES_PASSWORD=$DB_PASS -e POSTGRES_DB=$DB_DB \
  -p 5432:5432 docker.io/library/postgres:16

# wait for postgres to be ready
echo "Waiting for Postgres to accept connections..."
until $RUNTIME exec $DB_NAME pg_isready -U "$DB_USER" >/dev/null 2>&1; do
  sleep 1
done

echo "Postgres is ready."

# start app (detached)
echo "Starting app container $APP_NAME..."
$RUNTIME run -d --name $APP_NAME --network $NET --env-file "$ENV_TMP" -p 8000:8000 $IMAGE_TAG

cat <<EOF
All containers started.
Follow logs with:
  $RUNTIME logs -f $APP_NAME
To stop and remove both containers:
  $RUNTIME rm -f $APP_NAME $DB_NAME
EOF
