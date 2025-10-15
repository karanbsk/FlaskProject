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
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=${POSTGRES_DB:-postgres}
POSTGRES_USER=${POSTGRES_USER:-postgres}
MIGRATE_ON_STARTUP=${MIGRATE_ON_STARTUP:-false}
MIGRATE_IGNORE_FAILURE=${MIGRATE_IGNORE_FAILURE:-false}
PG_STARTUP_TIMEOUT=${PG_STARTUP_TIMEOUT:-60}   # seconds
APP_CONFIG=${APP_CONFIG:-development}
GUNICORN_WORKERS=${GUNICORN_WORKERS:-3}

if [ -z "${DATABASE_URL:-}" ]; then
  DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
fi

# print config in CI logs (avoid printing secrets)
printf "Entrypoint starting — APP_CONFIG=%s, wait for Postgres %s:%s, MIGRATE_ON_STARTUP=%s\n" \
  "$APP_CONFIG" "$POSTGRES_HOST" "$POSTGRES_PORT" "$MIGRATE_ON_STARTUP"

wait_for_pg_isready() {
  echo "entrypoint: waiting for postgres (${POSTGRES_HOST}:${POSTGRES_PORT}) via pg_isready..."
  until pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" >/dev/null 2>&1; do
    printf '.'; sleep 1
  done
  echo " entrypoint: pg_isready ok"
}

wait_for_python_ping() {
  echo "entrypoint: waiting for postgres via python DB ping..."
  export DATABASE_URL="${DATABASE_URL}"
  tries=0
  max=30
  while [ $tries -lt $max ]; do
    if python - <<'PY'
from sqlalchemy import create_engine, text
import os,sys, traceback
try:
    url = os.environ.get('DATABASE_URL')
    engine = create_engine(url, connect_args={})
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except Exception:
    # print full traceback so we know why it fails
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
sys.exit(0)
PY
    then
      echo " entrypoint: python DB ping ok"
      return 0
    fi
    tries=$((tries+1))
    printf '.'; sleep 1
  done
  echo " entrypoint: timeout waiting for DB" >&2
  return 1
}

# Ensure pg_isready exists
if [ "${APP_CONFIG}" != "production" ]; then
  if command -v pg_isready >/dev/null 2>&1; then
    wait_for_pg_isready
    MIGRATE_ON_STARTUP=true
  else
    wait_for_python_ping
    MIGRATE_ON_STARTUP=true
  fi
else
  wait_for_python_ping
  MIGRATE_ON_STARTUP=true
fi

# -------------------------
# Optional DB migrations
# -------------------------
if [ "${MIGRATE_ON_STARTUP}" = "true" ]; then
  printf "Running DB migrations...\n"
  # Prefer flask db upgrade; fallback to alembic; surface errors unless MIGRATE_IGNORE_FAILURE=true
  if command -v flask >/dev/null 2>&1; then
    printf "Using 'flask db upgrade' for migrations\n"
    if ! flask db upgrade; then
      printf "ERROR: 'flask db upgrade' failed\n" >&2
      if [ "${MIGRATE_IGNORE_FAILURE}" != "true" ]; then
        exit 1
      else
        printf "MIGRATE_IGNORE_FAILURE=true — continuing despite migration failure\n"
      fi
    fi
  elif command -v alembic >/dev/null 2>&1; then
    printf "Using 'alembic upgrade head' for migrations\n"
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
  exec gunicorn --bind 0.0.0.0:8000 wsgi:app --workers "$GUNICORN_WORKERS" --threads 2
else
  printf "Starting Flask dev server (development)...\n"
  exec flask run --host=0.0.0.0 --port=5000
fi
