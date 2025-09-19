#!/usr/bin/env sh
set -euo pipefail

# ---------- Config (fall back to sensible defaults) ----------
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-test_user}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"
POSTGRES_DB="${POSTGRES_DB:-test_db}"

# Maintenance DB to connect to when doing DROP/CREATE
MAINT_DB="${PG_ADMIN_DB:-postgres}"

# Build DATABASE_URL (app connection) and ADMIN_CONN (maintenance connection using same user)
DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
ADMIN_CONN="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${MAINT_DB}"

echo "Using POSTGRES_HOST=${POSTGRES_HOST} POSTGRES_USER=${POSTGRES_USER} POSTGRES_DB=${POSTGRES_DB}"

# ---------- Ensure required client tools exist ----------
if ! command -v psql >/dev/null 2>&1; then
  echo "ERROR: psql client not found in image. Install postgresql-client or include psql in the image." >&2
  exit 1
fi

# Wait for Postgres to accept connections
if command -v pg_isready >/dev/null 2>&1; then
  echo "Waiting for Postgres socket (pg_isready) at ${POSTGRES_HOST}:${POSTGRES_PORT} ..."
  until pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" >/dev/null 2>&1; do
    echo "Postgres socket not ready, sleeping 1s..."
    sleep 1
  done
else
  echo "pg_isready not found, waiting using psql ping..."
  until psql "${ADMIN_CONN}" -c '\q' >/dev/null 2>&1; do
    echo "Postgres not ready, sleeping 1s..."
    sleep 1
  done
fi

echo "Postgres reachable. Recreating target database '${POSTGRES_DB}' (drop & create) via maintenance DB '${MAINT_DB}'."

# Terminate connections (connect to maintenance DB), then drop & create DB.
# Note: DROP DATABASE must be executed from a different DB than the one being dropped.
# We connect as POSTGRES_USER (which in test environment is a superuser).
echo "Terminating other connections to '${POSTGRES_DB}' (if any)..."
psql "${ADMIN_CONN}" -v ON_ERROR_STOP=1 -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${POSTGRES_DB}' AND pid <> pg_backend_pid();" || true

echo "Dropping database '${POSTGRES_DB}' (if exists)..."
psql "${ADMIN_CONN}" -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS \"${POSTGRES_DB}\";"

echo "Creating database '${POSTGRES_DB}'..."
psql "${ADMIN_CONN}" -v ON_ERROR_STOP=1 -c "CREATE DATABASE \"${POSTGRES_DB}\";"

echo "Database recreate complete."

# Run migrations
ALEMBIC_PATH="/app/alembic.ini"
if [ -f "$ALEMBIC_PATH" ]; then
  echo "Running alembic upgrade head"
  alembic -c "$ALEMBIC_PATH" upgrade head || echo "Alembic upgrade failed (continuing)"
fi

# ---------- Run tests only if RUN_TESTS=1 (opt-in) ----------
# default to running tests so 'docker-compose run --rm app' executes tests and exits.
if [ "${RUN_TESTS:-1}" = "1" ]; then
  echo "Running pytest..."
  pytest -q -s
  EXIT_CODE=$?
  echo "Tests finished with exit code ${EXIT_CODE}"
  exit ${EXIT_CODE}
else
  echo "RUN_TESTS!=1; skipping pytest and leaving container running for debugging."
  tail -f /dev/null
fi
