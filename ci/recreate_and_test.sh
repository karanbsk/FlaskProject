#!/usr/bin/env bash
set -euo pipefail

# Usage:
#  ./ci/recreate_and_test.sh         # keeps stack up after tests (default)
#  TEARDOWN=yes ./ci/recreate_and_test.sh   # remove stack & volumes at end
#
COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.test.yml}
ALEMBIC_CFG_PATH=${ALEMBIC_CFG_PATH:-./alembic.ini}
DATABASE_URL=${DATABASE_URL:-}
INIT_ROOT_PW=${INIT_ROOT_PW:-'ChangeMeNow!'}
# If TEARDOWN=yes, the script will bring the stack down and remove volumes at the end.
TEARDOWN=${TEARDOWN:-no}

echo "→ Compose file: $COMPOSE_FILE"
echo "→ Alembic config: $ALEMBIC_CFG_PATH"
echo "→ TEARDOWN: $TEARDOWN"
echo

# sanity checks
if [ ! -f "$COMPOSE_FILE" ]; then
  echo "ERROR: $COMPOSE_FILE not found in $(pwd)"
  exit 2
fi
if [ ! -f "$ALEMBIC_CFG_PATH" ]; then
  echo "ERROR: Alembic config $ALEMBIC_CFG_PATH not found in $(pwd)"
  exit 3
fi

# 1) Tear down any existing test stack & volumes (fresh slate)
echo
echo "⏹ Bringing down any running test stack (removing volumes from prior runs)..."
docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans || true

# 2) Start only the postgres service
echo
echo "⏬ Starting postgres service..."
docker-compose -f "$COMPOSE_FILE" up -d postgres

# 3) Wait for Postgres readiness (up to 60s)
echo -n "⏳ Waiting for Postgres to accept connections"
for i in $(seq 1 60); do
  if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U "${POSTGRES_USER:-test_user}" -d "${POSTGRES_DB:-test_db}" >/dev/null 2>&1; then
    echo " → ready"
    break
  fi
  echo -n "."
  sleep 1
  if [ "$i" -eq 60 ]; then
    echo
    echo "ERROR: Postgres did not become ready in 60s. Dumping postgres logs (tail 200):"
    docker-compose -f "$COMPOSE_FILE" logs --no-color --tail=200 postgres
    exit 10
  fi
done

# 4) Run alembic upgrade head inside the app container (use ALEMBIC_DB_URL to be explicit)
echo
echo "🔧 Running alembic upgrade head inside app container..."
docker-compose -f "$COMPOSE_FILE" run --rm \
  -e ALEMBIC_DB_URL="${DATABASE_URL:-}" \
  -e INIT_ROOT_PW="$INIT_ROOT_PW" \
  -e DATABASE_URL="${DATABASE_URL:-}" \
  -e APP_CONFIG=testing \
  -w /app \
  app bash -lc "alembic -c $ALEMBIC_CFG_PATH upgrade head" \
  || {
    echo "ERROR: alembic upgrade head failed. Dumping logs:"
    docker-compose -f "$COMPOSE_FILE" run --rm -e ALEMBIC_DB_URL="${DATABASE_URL:-}" app bash -lc "alembic -c $ALEMBIC_CFG_PATH current || true"
    docker-compose -f "$COMPOSE_FILE" logs --no-color --tail=200 app postgres
    exit 11
  }

# 5) Show DB tables after migrations (sanity)
echo
echo "📋 Tables after migrations (from app container):"
docker-compose -f "$COMPOSE_FILE" run --rm -e DATABASE_URL="${DATABASE_URL:-}" app bash -lc "psql \"${DATABASE_URL:-}\" -c \"SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;\"" || true

# 6) Run tests inside the app container
echo
echo "🧪 Running pytest inside app container..."
docker-compose -f "$COMPOSE_FILE" run --rm \
  -e DATABASE_URL="${DATABASE_URL:-}" \
  -e APP_CONFIG=testing \
  -w /app \
  app bash -lc "pytest -q -s" || {
    echo
    echo "❌ Tests failed. Showing last 200 lines of app & postgres logs:"
    docker-compose -f "$COMPOSE_FILE" logs --no-color --tail=200 app postgres
    # If TEARDOWN=yes, still tear down; otherwise keep stack up for debugging
    if [ "${TEARDOWN,,}" = "yes" ]; then
      docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans || true
    fi
    exit 12
  }

echo
echo "✅ Tests completed (exit code 0)."

# 7) Conditional teardown
if [ "${TEARDOWN,,}" = "yes" ]; then
  echo "⏹ TEARDOWN=yes -> tearing down test stack and removing volumes..."
  docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans || true
  echo "Done. Test stack removed."
else
  echo "ℹ️ TEARDOWN is not enabled. Keeping test stack running for further inspection."
  echo "To clean up later run: docker-compose -f $COMPOSE_FILE down -v --remove-orphans"
  echo "If you want to reset DB to empty next run, run the script again (it will remove volumes at start)."
fi
