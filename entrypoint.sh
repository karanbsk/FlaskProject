#!/usr/bin/env sh
# entrypoint.sh — improved, robust, and explicit
# - Requires: pg_isready (package: postgresql-client)
# - Behavior: waits for Postgres, optionally runs migrations, then execs the server
# - Config:
#     POSTGRES_HOST (default: postgres)
#     POSTGRES_PORT (default: 5432)
#     POSTGRES_USER (default: postgres)
#     MIGRATE_ON_STARTUP (default: false)
#     MIGRATE_IGNORE_FAILURE (default: false)  # if true, continue even if migration fails
#     PG_STARTUP_TIMEOUT (seconds, default: 60)
#     APP_CONFIG (production|anything_else)
#     If you run container with custom CMD/args, they will be executed (exec "$@")

set -e

# -------------------------
# Defaults (override from env or docker-compose)
# -------------------------
POSTGRES_HOST=${POSTGRES_HOST:-postgres}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_USER=${POSTGRES_USER:-postgres}
MIGRATE_ON_STARTUP=${MIGRATE_ON_STARTUP:-false}
MIGRATE_IGNORE_FAILURE=${MIGRATE_IGNORE_FAILURE:-false}
PG_STARTUP_TIMEOUT=${PG_STARTUP_TIMEOUT:-60}   # seconds
APP_CONFIG=${APP_CONFIG:-development}

# print config in CI logs (avoid printing secrets)
printf "Entrypoint starting — APP_CONFIG=%s, wait for Postgres %s:%s, MIGRATE_ON_STARTUP=%s\n" \
  "$APP_CONFIG" "$POSTGRES_HOST" "$POSTGRES_PORT" "$MIGRATE_ON_STARTUP"

# Ensure pg_isready exists
if ! command -v pg_isready >/dev/null 2>&1; then
  printf "ERROR: pg_isready not found. Install 'postgresql-client' in your image.\n" >&2
  exit 1
fi

# -------------------------
# Wait for Postgres to be ready (bounded wait)
# -------------------------
printf "Waiting for Postgres at %s:%s ..." "$POSTGRES_HOST" "$POSTGRES_PORT"
elapsed=0
interval=1

while ! pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" >/dev/null 2>&1; do
  if [ "$elapsed" -ge "$PG_STARTUP_TIMEOUT" ]; then
    printf "\nERROR: Postgres at %s:%s did not become ready within %s seconds\n" \
      "$POSTGRES_HOST" "$POSTGRES_PORT" "$PG_STARTUP_TIMEOUT" >&2
    exit 1
  fi
  printf '.'  # progress dot
  sleep "$interval"
  elapsed=$((elapsed + interval))
done
printf '\nPostgres is ready.\n'

# -------------------------
# Optional DB migrations
# -------------------------
if [ "${MIGRATE_ON_STARTUP}" = "true" ]; then
  printf "Running DB migrations...\n"
  # Prefer flask db upgrade; fallback to alembic; surface errors unless MIGRATE_IGNORE_FAILURE=true
  if command -v flask >/dev/null 2>&1; then
    if ! flask db upgrade; then
      printf "ERROR: 'flask db upgrade' failed\n" >&2
      if [ "${MIGRATE_IGNORE_FAILURE}" != "true" ]; then
        exit 1
      else
        printf "MIGRATE_IGNORE_FAILURE=true — continuing despite migration failure\n"
      fi
    fi
  elif command -v alembic >/dev/null 2>&1; then
    if ! alembic upgrade head; then
      printf "ERROR: 'alembic upgrade head' failed\n" >&2
      if [ "${MIGRATE_IGNORE_FAILURE}" != "true" ]; then
        exit 1
      else
        printf "MIGRATE_IGNORE_FAILURE=true — continuing despite migration failure\n"
      fi
    fi
  else
    printf "WARNING: neither 'flask' nor 'alembic' found; skipping migrations\n"
  fi
fi

# -------------------------
# Start the main process
# -------------------------
# If user supplied CLI args to 'docker run <image> <cmd...>' then execute them
if [ "$#" -gt 0 ]; then
  printf "Executing provided command: %s\n" "$*"
  exec "$@"
fi

# Default behavior: decide based on APP_CONFIG
if [ "$APP_CONFIG" = "production" ]; then
  printf "Starting app with gunicorn (production)...\n"
  # Use configured number of workers or default
  : "${GUNICORN_WORKERS:=3}"
  # Exec so signals are forwarded
  exec gunicorn --bind 0.0.0.0:8000 wsgi:app --workers "$GUNICORN_WORKERS" --threads 2
else
  printf "Starting Flask dev server (development)...\n"
  # Ensure FLASK_APP is set via environment or docker-compose
  exec flask run --host=0.0.0.0 --port=5000
fi
