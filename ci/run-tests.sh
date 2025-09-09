#!/usr/bin/env sh
set -euo pipefail

# configure defaults if not set
PG_HOST="${POSTGRES_HOST:-postgres}"
PG_PORT="${POSTGRES_PORT:-5432}"
PG_USER="${POSTGRES_USER:-test_user}"
PG_DB="${POSTGRES_DB:-test_db}"

echo "Waiting for Postgres at ${PG_HOST}:${PG_PORT} ..."
# Wait for DB readiness
until pg_isready -h "${PG_HOST}" -p "${PG_PORT}" -U "${PG_USER}" >/dev/null 2>&1; do
  echo "Postgres not ready, sleeping 1s..."
  sleep 1
done

echo "DB ready. Installing test dependencies..."
# install deps (if image doesn't already have them)
pip install -r requirements.txt

# Apply migrations if you use alembic (optional)
if [ -f "./alembic.ini" ]; then
  echo "Running alembic upgrade head"
  alembic upgrade head
fi

echo "Running pytest..."
pytest -q
EXIT_CODE=$?

echo "Tests finished with exit code ${EXIT_CODE}"
exit ${EXIT_CODE}
