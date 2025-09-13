#!/usr/bin/env sh
set -euo pipefail

# ---------- Config (fall back to sensible defaults) ----------
PG_HOST="${POSTGRES_HOST:-postgres}"
PG_PORT="${POSTGRES_PORT:-5432}"
PG_USER="${POSTGRES_USER:-test_user}"
PG_DB="${POSTGRES_DB:-test_db}"
PG_PASS="${POSTGRES_PASSWORD:-}"

# Admin connection used to DROP/CREATE target DB
PG_ADMIN_DB="${PG_ADMIN_DB:-postgres}"
PG_ADMIN_USER="${PG_ADMIN_USER:-postgres}"
# allow overriding admin password separate from normal user password
PG_ADMIN_PASSWORD="${PG_ADMIN_PASSWORD:-${PG_PASS:-}}"

# export PGPASSWORD for psql non-interactive use (for commands that rely on it)
export PGPASSWORD="${PG_ADMIN_PASSWORD:-${PG_PASS:-}}"

# allow caller to override full DATABASE_URL
if [ -z "${DATABASE_URL:-}" ]; then
  # Do NOT use DATABASE_URL for DROP/CREATE — we'll build ADMIN_CONN separately below.
  DATABASE_URL="postgresql://${PG_USER}:${PG_PASS}@${PG_HOST}:${PG_PORT}/${PG_DB}"
fi

# ADMIN connection string (used for DROP/CREATE & terminating backends)
ADMIN_CONN="postgresql://${PG_ADMIN_USER}:${PG_ADMIN_PASSWORD}@${PG_HOST}:${PG_PORT}/${PG_ADMIN_DB}"

echo "Using PG_HOST=${PG_HOST} PG_PORT=${PG_PORT} PG_USER=${PG_USER} PG_DB=${PG_DB}"
echo "Using DATABASE_URL=${DATABASE_URL}"
echo "Using ADMIN_CONN (user=${PG_ADMIN_USER} db=${PG_ADMIN_DB})"

# ---------- Ensure required client tools exist ----------
if ! command -v psql >/dev/null 2>&1; then
  echo "ERROR: psql client not found in image. Install postgresql-client or include psql in the image." >&2
  exit 1
fi

# Prefer pg_isready (checks server socket). Falls back to psql probe if missing.
if command -v pg_isready >/dev/null 2>&1; then
  echo "Waiting for Postgres socket (pg_isready) at ${PG_HOST}:${PG_PORT} ..."
  until pg_isready -h "${PG_HOST}" -p "${PG_PORT}" >/dev/null 2>&1; do
    echo "Postgres socket not ready, sleeping 1s..."
    sleep 1
  done
else
  echo "pg_isready not found, waiting using psql probe..."
  until psql "${ADMIN_CONN}" -c '\q' >/dev/null 2>&1; do
    echo "Postgres not ready, sleeping 1s..."
    sleep 1
  done
fi

echo "Postgres socket ready. Attempting to recreate database '${PG_DB}' (DROP & CREATE) using admin connection."

RETRIES=10
SLEEPTIME=1
i=0
recreated=0

while [ "$i" -lt "$RETRIES" ]; do
  # terminate other connections to the target DB (must run on admin DB)
  if psql "${ADMIN_CONN}" -v ON_ERROR_STOP=1 -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${PG_DB}' AND pid <> pg_backend_pid();" >/dev/null 2>&1; then
    echo "Terminated other connections to ${PG_DB} (if any)."
  else
    echo "Warning: could not terminate connections (attempt $((i+1))/${RETRIES})."
  fi

  if psql "${ADMIN_CONN}" -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS \"${PG_DB}\";" >/dev/null 2>&1; then
    if psql "${ADMIN_CONN}" -v ON_ERROR_STOP=1 -c "CREATE DATABASE \"${PG_DB}\";" >/dev/null 2>&1; then
      echo "Successfully recreated database '${PG_DB}'."
      recreated=1
      break
    else
      echo "CREATE DATABASE attempt failed (attempt $((i+1))/${RETRIES}). Retrying in ${SLEEPTIME}s..."
    fi
  else
    echo "DROP DATABASE attempt failed (attempt $((i+1))/${RETRIES}). Retrying in ${SLEEPTIME}s..."
  fi

  i=$((i+1))
  sleep ${SLEEPTIME}
done

if [ "${recreated}" -ne 1 ]; then
  echo "WARNING: Could not recreate database '${PG_DB}' after ${RETRIES} attempts."
  echo "This may be because the configured admin user (${PG_ADMIN_USER}) does not have permission to DROP/CREATE databases,"
  echo "or because PG admin credentials were not supplied. Continuing — tests may fail."
fi

# ---------- Install / migrations ----------
echo "DB ready. Installing test dependencies..."
pip install -r requirements.txt

ALEMBIC_PATH="/app/migrations/alembic.ini"
if [ -f "$ALEMBIC_PATH" ]; then
  echo "Running alembic upgrade head"
  alembic upgrade head || echo "Alembic upgrade failed (continuing)"
fi

# ---------- Run tests only if RUN_TESTS=1 (opt-in) ----------
if [ "${RUN_TESTS:-0}" = "1" ]; then
  echo "Running pytest..."
  pytest -q -s 
  EXIT_CODE=$?
  echo "Tests finished with exit code ${EXIT_CODE}"
  exit ${EXIT_CODE}
else
  echo "RUN_TESTS!=1; skipping pytest and leaving container running for debugging."
  # Keep container alive for inspection (reasonable default for dev). Use `docker-compose exec` to get a shell.
  # If you prefer the script to exit instead of sleeping, replace the next line with `exit 0`.
  tail -f /dev/null
fi
