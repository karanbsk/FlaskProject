#!/usr/bin/env sh

set -e

# default envs (ensure these exist in your docker-compose .env)
# DB_HOST=${DB_HOST:-postgres}
# DB_PORT=${DB_PORT:-5432}
# DB_USER=${POSTGRES_USER:-postgres}
# DB_NAME=${POSTGRES_DB:-postgres}

# Wait for Postgres
echo "Waiting for Postgres at $POSTGRES_HOST:$POSTGRES_PORT ..."
until pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" >/dev/null 2>&1; do
  printf '.'
  sleep 1
done
echo "\nPostgres is ready."

# Optionally run migrations at startup (set MIGRATE_ON_STARTUP=true in compose if you want this)
if [ "${MIGRATE_ON_STARTUP:-false}" = "true" ]; then
  echo "Running DB migrations..."
  # Prefer 'flask db upgrade' if using Flask-Migrate; fallback to alembic
  if command -v flask >/dev/null 2>&1; then
    flask db upgrade || true
  else
    alembic upgrade head || true
  fi
fi

# Choose process based on APP_ENV or FLASK_ENV
#APP_ENV=${APP_ENV:-development}   # set to 'production' in prod
if [ "$APP_CONFIG" = "production" ]; then
  echo "Starting app with gunicorn (production)..."
  exec gunicorn wsgi:app --bind 0.0.0.0:8000
else
  echo "Starting Flask dev server..."
  # Ensure FLASK_APP is set (wsgi:app) in your docker-compose for dev
  exec flask run --host=0.0.0.0 --port=5000
fi
